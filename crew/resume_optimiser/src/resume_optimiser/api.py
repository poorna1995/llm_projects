"""
FastAPI application for Resume Optimizer
Provides REST API endpoints for resume optimization functionality
"""

import os
import uuid
import hashlib
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

try:
    from azure.servicebus import ServiceBusClient, ServiceBusMessage  # type: ignore
except Exception:  # pragma: no cover
    ServiceBusClient = None  # type: ignore
    ServiceBusMessage = None  # type: ignore
import uvicorn

from resume_optimiser.crew import ResumeCrew
from resume_optimiser.s3_utils import upload_file_to_s3
from resume_optimiser.models import ResumeOptimizationRequest, ResumeOptimizationResponse

# Initialize FastAPI app
app = FastAPI(
    title="Resume Optimizer API",
    description="AI-powered resume optimization using CrewAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for tracking jobs
job_status: Dict[str, Dict[str, Any]] = {}
project_root = Path(__file__).parent.parent.parent

class HealthResponse(BaseModel):
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ResumeUploadResponse(BaseModel):
    file_id: str
    file_path: str
    message: str


class CreateJobRequest(BaseModel):
    resume_text: Optional[str] = None
    job_description: Optional[str] = None


class CreateJobResponse(BaseModel):
    job_id: str
    status: str = "queued"

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic health check"""
    return HealthResponse(
        status="healthy",
        message="Resume Optimizer API is running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        message="Service is operational"
    )

@app.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file and return file ID for processing"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not supported. Allowed types: PDF, DOCX, TXT"
            )
        
        # Create knowledge directory
        knowledge_root = project_root / 'knowledge'
        knowledge_root.mkdir(exist_ok=True)
        
        # Read file content and create hash
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()[:12]
        
        # Create per-resume directory
        per_resume_dir = knowledge_root / file_hash
        if per_resume_dir.exists():
            shutil.rmtree(per_resume_dir)
        per_resume_dir.mkdir(exist_ok=True)
        
        # Save file
        file_extension = Path(file.filename).suffix or '.pdf'
        safe_filename = f"resume{file_extension}"
        file_path = per_resume_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return ResumeUploadResponse(
            file_id=file_hash,
            file_path=str(file_path),
            message="File uploaded successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/optimize", response_model=JobStatusResponse)
async def start_optimization(
    job_url: str = Form(...),
    company_name: Optional[str] = Form(None),
    file_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Start resume optimization process"""
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        job_status[job_id] = {
            "status": "queued",
            "progress": "Starting optimization...",
            "result": None,
            "error": None
        }
        
        # Find resume file if file_id provided
        resume_path = None
        if file_id:
            resume_file = project_root / 'knowledge' / file_id
            if resume_file.exists():
                # Find the actual resume file in the directory
                for file in resume_file.iterdir():
                    if file.suffix.lower() in ['.pdf', '.docx', '.txt']:
                        resume_path = str(file)
                        break
                if not resume_path:
                    raise HTTPException(status_code=404, detail="Resume file not found")
        
        # Start background task
        background_tasks.add_task(
            run_optimization_task,
            job_id,
            job_url,
            company_name or "",
            resume_path
        )
        
        return JobStatusResponse(
            job_id=job_id,
            status="queued",
            progress="Starting optimization..."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting optimization: {str(e)}")


@app.post("/v1/jobs", response_model=CreateJobResponse, status_code=202)
async def create_job_endpoint(payload: CreateJobRequest) -> CreateJobResponse:
    """Queue-based job creation for Week 3. Falls back gracefully if Service Bus not set."""
    job_id = str(uuid.uuid4())

    connection_str = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
    queue_name = os.getenv("AZURE_SERVICE_BUS_QUEUE_NAME")

    # Store minimal in-memory status for demo parity
    job_status[job_id] = {
        "status": "queued",
        "progress": "Queued",
        "result": None,
        "error": None,
    }

    if not connection_str or not queue_name or ServiceBusClient is None:
        # Dev fallback: no enqueue, still returns job id
        return CreateJobResponse(job_id=job_id)

    message_body = {
        "job_id": job_id,
        "resume_text": payload.resume_text,
        "job_description": payload.job_description,
    }

    try:
        with ServiceBusClient.from_connection_string(connection_str) as client:
            with client.get_queue_sender(queue_name) as sender:
                sender.send_messages(ServiceBusMessage(json.dumps(message_body)))
    except Exception as e:
        # Keep API responsive; caller can retry
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["error"] = str(e)
    return CreateJobResponse(job_id=job_id)

@app.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of an optimization job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_status[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job_data["status"],
        progress=job_data.get("progress"),
        result=job_data.get("result"),
        error=job_data.get("error")
    )

@app.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs():
    """List all optimization jobs"""
    return [
        JobStatusResponse(
            job_id=job_id,
            status=job_data["status"],
            progress=job_data.get("progress"),
            result=job_data.get("result"),
            error=job_data.get("error")
        )
        for job_id, job_data in job_status.items()
    ]

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its data"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up job data
    del job_status[job_id]
    
    # Clean up files (optional)
    job_dir = project_root / 'output' / f"run-{job_id}"
    if job_dir.exists():
        shutil.rmtree(job_dir)
    
    return {"message": "Job deleted successfully"}

@app.get("/download/{job_id}/{filename}")
async def download_result(job_id: str, filename: str):
    """Download a specific result file from a job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_status[job_id]
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Find the file
    output_dir = project_root / 'output' / f"run-{job_id}"
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )

async def run_optimization_task(job_id: str, job_url: str, company_name: str, resume_path: Optional[str]):
    """Background task to run resume optimization"""
    try:
        # Update status
        job_status[job_id]["status"] = "running"
        job_status[job_id]["progress"] = "Initializing CrewAI agents..."
        
        # Set working directory
        os.chdir(project_root)
        
        # Initialize crew
        crew_instance = ResumeCrew()
        crew_instance.setup(job_url, company_name, resume_path)
        
        # Update status
        job_status[job_id]["progress"] = "Running optimization agents..."
        
        # Run optimization
        result = crew_instance.crew().kickoff(inputs={
            "job_url": job_url,
            "company_name": company_name
        })
        
        # Process results
        job_status[job_id]["progress"] = "Processing results..."
        
        # Get output files
        output_dir = project_root / 'output' / f"run-{job_id}"
        output_files = {}
        
        if output_dir.exists():
            for file_path in output_dir.glob("*"):
                if file_path.is_file():
                    output_files[file_path.name] = str(file_path)
        
        # Upload to S3 if configured
        s3_uploads = {}
        s3_bucket = os.getenv("S3_BUCKET_NAME")
        if s3_bucket:
            s3_prefix = f"{os.getenv('S3_PREFIX', 'resume-optimiser/outputs')}/{job_id}"
            for filename, file_path in output_files.items():
                try:
                    content_type = "text/markdown" if filename.endswith(".md") else (
                        "application/json" if filename.endswith(".json") else "text/plain"
                    )
                    url = upload_file_to_s3(
                        local_path=file_path,
                        bucket=s3_bucket,
                        key_prefix=s3_prefix,
                        content_type=content_type
                    )
                    s3_uploads[filename] = url
                except Exception as e:
                    print(f"S3 upload failed for {filename}: {e}")
        
        # Update job status with results
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["progress"] = "Optimization completed successfully"
        job_status[job_id]["result"] = {
            "output_files": output_files,
            "s3_uploads": s3_uploads,
            "raw_result": str(result) if hasattr(result, '__str__') else str(result)
        }
        
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["error"] = str(e)
        job_status[job_id]["progress"] = f"Optimization failed: {str(e)}"

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
