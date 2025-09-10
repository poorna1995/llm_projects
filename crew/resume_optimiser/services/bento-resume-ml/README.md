# BentoML + ONNX Service

Internal inference service for parsing/extraction/scoring.

Local build and run:

```bash
cd services/bento-resume-ml
bentoml build
bentoml containerize resume_ml_service:latest
docker run -p 3000:3000 resume_ml_service:latest
```

Endpoints:
- POST /parse_resume {"text": "..."}
- POST /extract_skills {"text": "..."}
- POST /score_match {"resume_text": "...", "job_description": "..."}

