FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /bento

RUN pip install --no-cache-dir bentoml==1.2.18 onnxruntime==1.18.0 numpy==1.26.4

COPY service.py /bento/service.py

EXPOSE 3000
CMD ["bentoml", "serve", "service:svc", "--host", "0.0.0.0", "--port", "3000", "--production"]


