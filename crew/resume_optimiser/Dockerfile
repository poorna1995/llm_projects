

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/app/.uv-cache

WORKDIR /app


# Install uv (modern Python package manager)
RUN pip install uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (faster than pip)
RUN uv sync --frozen --no-dev

# Copy project source
COPY . ./


EXPOSE 8501

# Use uv to run the app (faster startup)
CMD ["uv", "run", "streamlit", "run", "src/resume_optimiser/app.py", "--server.port=8501", "--server.address=0.0.0.0"]


