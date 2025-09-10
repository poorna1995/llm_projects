## Resume Optimiser - Docker

### Prerequisites

- Docker and Docker Compose installed
- Docker daemon running (start Docker Desktop or `sudo systemctl start docker` on Linux)

### Environment

Create a `.env` file in this directory with your keys:

```
OPENAI_API_KEY=...
SERPER_API_KEY=...

# Optional S3 upload
S3_BUCKET_NAME=your-bucket
S3_PREFIX=resume-optimiser/outputs
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

### Build and Run

Build image:

```bash
docker compose build
```

Start app:

```bash
docker compose up -d
```

Open the UI at http://localhost:8501

### Local directories mounted

- `output/` – stores generated files
- `uploads/` – stores any uploaded assets
- `knowledge/` – holds uploaded resumes used as knowledge input

### Rebuild on dependency change

```bash
docker compose build --no-cache && docker compose up -d
```

### Troubleshooting

**Docker daemon not running:**

```bash
# On macOS with Docker Desktop
open -a Docker

# On Linux
sudo systemctl start docker

# Check if Docker is running
docker ps
```

**Permission issues on Linux:**

```bash
sudo usermod -aG docker $USER
# Then logout and login again
```

# ResumeOptimiser Crew

Welcome to the ResumeOptimiser Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:

```bash
crewai install
```

### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/resume_optimiser/config/agents.yaml` to define your agents
- Modify `src/resume_optimiser/config/tasks.yaml` to define your tasks
- Modify `src/resume_optimiser/crew.py` to add your own logic, tools and specific args
- Modify `src/resume_optimiser/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the resume_optimiser Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The resume_optimiser Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the ResumeOptimiser Crew or crewAI.

- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
