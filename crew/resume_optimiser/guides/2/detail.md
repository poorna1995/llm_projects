### Enterprise flow with ONNX Runtime + BentoML + Docker + Kubernetes + Load Balancer + API Gateway

Below is a production-ready pattern that fits your Resume Optimiser. It keeps your FastAPI + CrewAI orchestration, but moves heavy ML inference to a dedicated BentoML microservice powered by ONNX Runtime, then containerizes and deploys everything to Kubernetes behind an Ingress/Load Balancer and API Gateway.

## End-to-end request flow

```text
Client (Web/CLI/Streamlit)
  → API Gateway (AWS API Gateway / Azure APIM)
    → Ingress Controller (NGINX/ALB/Gateway API)
      → FastAPI Orchestrator (CrewAI + business logic)
        → Queue (SQS/Service Bus) for long runs
          → Worker Pods (CrewAI agents)
            → Internal Service: BentoML ONNX Inference (skills/entity/classifier/embeddings)
            → Vector DB + Object Store + DB
            → LLM Provider (OpenAI/Azure OpenAI/Bedrock) via LLM Gateway
```

- FastAPI remains the single public API.
- BentoML serves ONNX models as an internal microservice in the cluster.
- Workers call Bento endpoints for fast, cheap, deterministic inference (classification/extraction/scoring/embeddings).
- API Gateway provides auth, throttling, and a stable public entrypoint.
- Kubernetes autoscaling handles load; DLQ + retries protect long jobs.

## What to put where (fits your repo)

- `services/api` (FastAPI orchestrator; your existing service)
- `services/worker` (CrewAI workers consuming queue)
- `services/bento-resume-ml` (BentoML + ONNX Runtime for ML)
- `k8s/helm/` (charts or manifests for api, worker, bento, ingress, hpa)
- `infra/terraform/` (EKS/AKS, API Gateway/APIM, SQS/Service Bus, DB, VPC, etc.)
- `models/onnx/` (versioned ONNX artifacts; store long-term in S3/Blob)
- `prompts/`, `evals/`, `ops/runbooks/`, `ops/dashboards/`

## ONNX Runtime + BentoML service

Use ONNX Runtime for classic NLP components that benefit from speed and determinism:

- Resume parsing features (NER/skills extraction, section tagging)
- Job-resume matching scorer (similarity/classifier)
- Embedding model (optional, if you want to reduce external calls)

Example Bento service (BentoML 1.x style):

```python
# services/bento-resume-ml/service.py
import bentoml
from bentoml.io import JSON
import onnxruntime as ort
import numpy as np

runner = bentoml.runners.Runner()  # not used here, but useful for composing multiple models

svc = bentoml.Service("resume_ml_service")

class SkillClassifier:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        # get input/output names once
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def predict(self, features: np.ndarray) -> np.ndarray:
        return self.session.run([self.output_name], {self.input_name: features})[0]

model = SkillClassifier("/bento/models/skill_classifier.onnx")

@svc.api(input=JSON(), output=JSON())
def classify_skills(request: dict) -> dict:
    # Example: features prepared upstream or in this service
    features = np.array(request["features"], dtype=np.float32)
    preds = model.predict(features)
    return {"predictions": preds.tolist(), "model_version": "v1"}
```

Bento build file:

```yaml
# services/bento-resume-ml/bentofile.yaml
service: "service:svc"
labels:
  owner: "resume-optimiser"
  stage: "prod"
include:
  - "service.py"
  - "models/**"
python:
  packages:
    - onnxruntime==1.18.0
    - numpy==1.26.4
```

Build and containerize:

```bash
cd services/bento-resume-ml
bentoml build
bentoml containerize resume_ml_service:latest
# => produces a Docker image like resume_ml_service:20250101_xxx
```

Run locally:

```bash
docker run -p 3000:3000 resume_ml_service:20250101_xxx
# POST http://localhost:3000/classify_skills
```

Tip: Convert your PyTorch/TF models to ONNX once (versioned):

- Export script saves to `models/onnx/skill_classifier-v1.onnx`
- Copy into the Bento via `include:` and mount to `/bento/models/`

## FastAPI orchestration calling BentoML

Inside your FastAPI or worker code, call BentoML internal service:

```python
import httpx

async def classify_skills_internal(features):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post("http://resume-ml:3000/classify_skills", json={"features": features})
        r.raise_for_status()
        return r.json()
```

- In Kubernetes, `resume-ml` is the BentoML Service DNS.
- Keep Bento endpoints private; expose only FastAPI publicly.

## Dockerization

Two images:

- `services/api/Dockerfile` (FastAPI)
- `services/worker/Dockerfile` (CrewAI workers)
- Bento image is produced by `bentoml containerize`

Example FastAPI Dockerfile:

```dockerfile
# services/api/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir uv
COPY services/api/ /app/
RUN uv pip install --system -r requirements.txt
ENV PORT=8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Kubernetes (Deployments, Services, Autoscaling)

Deployments:

```yaml
# k8s/deploy-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-api
spec:
  replicas: 2
  selector:
    matchLabels: { app: resume-api }
  template:
    metadata:
      labels: { app: resume-api }
    spec:
      containers:
        - name: api
          image: ghcr.io/you/resume-api:latest
          ports: [{ containerPort: 8000 }]
          env:
            - name: BENTO_URL
              value: http://resume-ml:3000
---
apiVersion: v1
kind: Service
metadata:
  name: resume-api
spec:
  selector: { app: resume-api }
  ports:
    - port: 80
      targetPort: 8000
```

```yaml
# k8s/deploy-bento.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-ml
spec:
  replicas: 2
  selector:
    matchLabels: { app: resume-ml }
  template:
    metadata:
      labels: { app: resume-ml }
    spec:
      containers:
        - name: bento
          image: resume_ml_service:20250101_xxx
          ports: [{ containerPort: 3000 }]
---
apiVersion: v1
kind: Service
metadata:
  name: resume-ml
spec:
  selector: { app: resume-ml }
  ports:
    - port: 3000
      targetPort: 3000
```

HPA:

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: resume-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: resume-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

Ingress + LoadBalancer (NGINX):

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: resume-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: resume-api
                port:
                  number: 80
```

- The Ingress Controller runs behind a cloud Load Balancer (Service type LoadBalancer).
- Only `resume-api` is exposed; `resume-ml` stays cluster-internal.

## API Gateway integration

- AWS:
  - Option A: API Gateway HTTP API → VPC Link → NLB → NGINX Ingress Service
  - Option B: CloudFront + ALB Ingress Controller (simpler for web+api)
- Azure:
  - APIM → Ingress public endpoint; or APIM → Private Link → Internal Ingress

Benefits:

- AuthN/Z, rate limiting, WAF, request validation, custom domains, stages.
- Keep Kubernetes endpoints private; API Gateway is the only public entry.

## How this improves Resume Optimiser

- ONNX Runtime offloads deterministic ML (skills/NER/scoring/embeddings) from the LLM → lower cost, lower latency, higher reliability.
- BentoML packages models cleanly, versioned, and deployable independently → safer rollouts (canary by model).
- Kubernetes gives horizontal scaling for both orchestrator and inference.
- API Gateway + Ingress gives enterprise-grade security and traffic control.

## What to implement first (quick path)

- Convert one model to ONNX (e.g., skill classifier) and stand up `bento-resume-ml` service.
- Modify workers to call `http://resume-ml:3000/classify_skills`.
- Containerize API and Worker; deploy all three to Kubernetes with HPA.
- Put API Gateway in front of the Ingress; expose only `resume-api`.

If you want, I can generate:

- A minimal `services/bento-resume-ml` folder with working `service.py` and `bentofile.yaml`
- K8s manifests or a Helm chart for `api`, `worker`, `bento`, `ingress`, `hpa`
- A GitHub Actions pipeline to build/push images and deploy to EKS/AKS
- Terraform modules for the cluster and API Gateway

- Mapped ONNX Runtime + BentoML into your architecture, showed Docker/K8s/Ingress/API Gateway fit, and provided concise example files for the Bento service, deployments, services, HPA, and ingress.
