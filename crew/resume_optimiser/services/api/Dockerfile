FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install project (uses pyproject.toml under crew/resume_optimiser)
COPY ./pyproject.toml /workspace-root-pyproject.toml
RUN pip install --no-cache-dir uv
COPY . /workspace
RUN cd /workspace/crew/resume_optimiser && uv pip install --system -e . && pip install azure-servicebus==7.12.2

EXPOSE 8000
CMD ["uvicorn", "resume_optimiser.api:app", "--host", "0.0.0.0", "--port", "8000"]



