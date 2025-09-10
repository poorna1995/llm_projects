import streamlit as st
import os
import uuid
import shutil
import hashlib
from resume_optimiser.crew import ResumeCrew
from resume_optimiser.s3_utils import upload_file_to_s3

st.title("Resume Optimizer")
st.markdown("### Optimize Your Resume with CrewAI")

# User inputs
job_url = st.text_input("Enter the Job Posting URL:")
company_name = st.text_input("Enter the Company Name (Optional):")
uploaded_file = st.file_uploader("Upload Your Resume (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"])

def save_uploaded_file(uploaded_file):
    """Save uploaded resume under a per-hash folder in knowledge/ and return its absolute path.

    Ensures that re-uploading the same resume (same bytes) overwrites the same folder,
    preventing cross-contamination between different resumes.
    """
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
        knowledge_root = os.path.join(project_root, 'knowledge')
        os.makedirs(knowledge_root, exist_ok=True)

        # Read bytes once to compute deterministic hash and write to disk
        file_bytes = uploaded_file.getbuffer()
        sha256 = hashlib.sha256(file_bytes).hexdigest()[:12]

        # Create per-resume folder using short hash
        per_resume_dir = os.path.join(knowledge_root, sha256)
        if os.path.isdir(per_resume_dir):
            try:
                shutil.rmtree(per_resume_dir)
            except Exception:
                pass
        os.makedirs(per_resume_dir, exist_ok=True)

        file_extension = os.path.splitext(uploaded_file.name)[1]
        safe_name = f"resume{file_extension or '.pdf'}"
        file_path = os.path.join(per_resume_dir, safe_name)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        st.success(f"File saved to {file_path}")
        return file_path
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None
def run_crew(job_url, company_name, resume_path):
    """Runs the Resume Optimization Crew and displays results."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    base_output_dir = os.path.join(project_root, 'output')
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)

    with st.spinner("Optimizing your resume..."):
        try:
            # Ensure the current working directory is the project root so that
            # any library that looks for a `knowledge/` directory resolves correctly.
            os.chdir(project_root)
            crew_instance = ResumeCrew()
            crew_instance.setup(job_url, company_name, resume_path)
            result = crew_instance.crew().kickoff(inputs={
                "job_url": job_url,
                "company_name": company_name or ""
            })

            st.success("Optimization complete!")
            st.markdown("### Results")
            # `kickoff` may return a string or an object with `.raw`
            try:
                display_text = result.raw if hasattr(result, "raw") else str(result)
            except Exception:
                display_text = str(result)
            st.markdown(display_text)

            # Determine per-resume output subfolder
            sub_output_dir = os.path.join(project_root, crew_instance.output_subdir or 'output')
            output_files = [
                os.path.join(sub_output_dir, 'optimized_resume.md'),
                os.path.join(sub_output_dir, 'final_report.md'),
                os.path.join(sub_output_dir, 'job_analysis.json'),
                os.path.join(sub_output_dir, 'resume_optimization.json'),
                os.path.join(sub_output_dir, 'company_research.json')
            ]

            s3_bucket = os.getenv("S3_BUCKET_NAME")
            # Append the per-resume folder name to the base S3 prefix
            s3_prefix_base = os.getenv("S3_PREFIX", "resume-optimiser/outputs")
            per_resume_folder = os.path.basename(sub_output_dir.rstrip('/'))
            s3_prefix = f"{s3_prefix_base.rstrip('/')}/{per_resume_folder}"

            uploaded_links = []

            for file_path in output_files:
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        st.subheader(os.path.basename(file_path))
                        st.text_area("Content:", content, height=300)

                        # Upload to S3 if configured
                        if s3_bucket:
                            guessed_type = "text/markdown" if file_path.endswith(".md") else (
                                "application/json" if file_path.endswith(".json") else "text/plain"
                            )
                            try:
                                url = upload_file_to_s3(
                                    local_path=file_path,
                                    bucket=s3_bucket,
                                    key_prefix=s3_prefix,
                                    content_type=guessed_type,
                                )
                                uploaded_links.append((os.path.basename(file_path), url))
                            except Exception as e:
                                st.warning(f"S3 upload failed for {os.path.basename(file_path)}: {e}")

            if s3_bucket and uploaded_links:
                st.markdown("### S3 Uploads")
                for name, url in uploaded_links:
                    st.markdown(f"- **{name}**: {url}")

        except Exception as e:
            st.error(f"An error occurred: {e}")



if st.button("Run Optimizer"):
    if not job_url and not uploaded_file:
        st.error("Please provide a Job URL and/or upload a resume.")
    else:
        resume_path = None
        if uploaded_file:
            resume_path = save_uploaded_file(uploaded_file)

        run_crew(job_url, company_name, resume_path)






# Upload a resume

# Specify the job they want

# Use an AI agent (ResumeCrew) to:

# Analyze job description

# Rewrite or improve resume

# Research company

# Generate reports

# Display & upload results to S3




# resume1.pdf and resume2.pdf have identical content → hash will be the same → same folder.

# You change one word in resume1.pdf → hash will be different → new folder.