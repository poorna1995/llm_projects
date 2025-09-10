from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from .models import (
    JobRequirements,
    ResumeOptimization,
    CompanyResearch
)
from typing import Optional
from datetime import datetime
import os
import hashlib
from dotenv import load_dotenv


@CrewBase
class ResumeCrew():
    """ResumeOptimiser crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

        # --- Initialize default attributes (prevents AttributeError) ---
    job_url: Optional[str] = None
    company_name: Optional[str] = None
    resume_path: Optional[str] = None
    resume_pdf: Optional[PDFKnowledgeSource] = None
    output_subdir: Optional[str] = None
 
    load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

    def setup(self, job_url: Optional[str] = None, company_name: Optional[str] = None, resume_path: Optional[str] = None):
        """Setup values for this crew instance."""
        self.job_url = job_url
        self.company_name = company_name
        self.resume_path = resume_path

        if self.resume_path:
            abs_path = os.path.abspath(self.resume_path)
            if os.path.exists(abs_path):
                # Compute path relative to knowledge/ if the file resides there
                project_root = self._project_root()
                knowledge_root = os.path.join(project_root, 'knowledge')
                try:
                    rel_from_knowledge = os.path.relpath(abs_path, knowledge_root)
                    # If file is outside knowledge/, relpath will escape with ..
                    if rel_from_knowledge.startswith('..'):
                        rel_path = os.path.basename(abs_path)
                    else:
                        rel_path = rel_from_knowledge
                except Exception:
                    rel_path = os.path.basename(abs_path)

                # Pass the relative path (may include subfolder) so the knowledge source
                # indexes only this file under knowledge/
                self.resume_pdf = PDFKnowledgeSource(file_paths=[rel_path])
                # Derive deterministic output subfolder from resume file content
                self.output_subdir = self._derive_output_subdir(abs_path)
            else:
                raise FileNotFoundError(f"Resume file not found: {abs_path}")
        else:
            self.resume_pdf = None
            # Time-based subfolder when no resume provided
            self.output_subdir = self._derive_time_based_subdir()

        # Ensure output directory exists
        subdir = self.output_subdir or 'output'
        subdir_path = os.path.join(self._project_root(), subdir)
        os.makedirs(subdir_path, exist_ok=True)

    def _project_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

    def _derive_output_subdir(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        short_hash = sha256.hexdigest()[:12]
        return os.path.join('output', short_hash)

    def _derive_time_based_subdir(self) -> str:
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        return os.path.join('output', f'run-{ts}')

    def _output_path(self, filename: str) -> str:
        # Guard against None before setup
        subdir = self.output_subdir or 'output'
        return os.path.join(subdir, filename)

    @agent
    def resume_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["resume_analyzer"],
            verbose=True,
            knowledge_sources=[ks for ks in [self.resume_pdf] if ks]
        )

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["company_researcher"],
            verbose=True,
            tools=[SerperDevTool()],
            knowledge_sources=[ks for ks in [self.resume_pdf] if ks]
        )

    
    @agent
    def job_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['job_analyzer'],
            verbose=True,
            tools=[ScrapeWebsiteTool()]
        )
    @agent
    def resume_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_writer'],
            verbose=True
        )

    @agent
    def report_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['report_generator'],
            verbose=True
        )


    
    @task
    def analyze_job_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_job_task'],
            output_file=self._output_path('job_analysis.json'),
            output_pydantic=JobRequirements
        )

    @task
    def optimize_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config['optimize_resume_task'],
            output_file=self._output_path('resume_optimization.json'),
   
            output_pydantic=ResumeOptimization
        )

    @task
    def research_company_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_company_task'],
            output_file=self._output_path('company_research.json'),   
            output_pydantic=CompanyResearch
        )

    @task
    def generate_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_resume_task'],
            output_file=self._output_path('optimized_resume.md')

        )
        

    @task
    def generate_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_report_task'],
            output_file=self._output_path('final_report.md')

        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            process=Process.sequential,
            knowledge_sources=[ks for ks in [self.resume_pdf] if ks]
        )
