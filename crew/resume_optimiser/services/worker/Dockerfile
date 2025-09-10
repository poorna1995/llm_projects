FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir azure-servicebus==7.12.2

COPY worker.py /app/worker.py

CMD ["python", "worker.py"]



