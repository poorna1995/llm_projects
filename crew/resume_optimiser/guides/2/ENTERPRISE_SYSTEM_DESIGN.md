## Resume Optimiser — Enterprise System Design, Delivery Playbook, and Project Report

This document is a practical, end-to-end guide to take the current multi-agent Resume Optimiser (CrewAI + Streamlit + FastAPI) from a dev prototype to an enterprise-grade, scalable, secure, and reliable product. It includes system design flows, implementation steps, evaluation methodology, cloud reference architectures (AWS and Azure), CI/CD, observability, cost controls, and interview-ready talking points.

---

### 1) Current State (as provided)

- FastAPI API layer exposing endpoints for the core multi-agent flow
- Streamlit internal UI for development and demos
- CrewAI multi-agent orchestration with custom and 3rd-party tools to reduce hallucinations
- Goal: add evaluation (quality and cost), production-grade deployment, reliability, security, and cloud integrations

---

### 2) End-to-End System Design (Target)

High-level logical architecture:

```
[User/Client] ──> [API Gateway/WAF] ──> [FastAPI Service]
                                   │
                                   ├─> [AuthN (OIDC/OAuth2) + RBAC]
                                   ├─> [Request/Response Logging & Tracing]
                                   ├─> [Rate Limiter]
                                   └─> [Job Dispatcher]

[FastAPI Service]
  ├─> [CrewAI Orchestrator]
  │     ├─> [Agents & Tasks]
  │     │     ├─> [Custom Tools] (RAG, validators, parsers)
  │     │     └─> [3rd-Party Tools] (web search, ATS parsers, etc.)
  │     └─> [Model Providers] (OpenAI/Azure OpenAI/Bedrock/Anthropic)
  ├─> [Background Workers / Queue] (long-running jobs)
  ├─> [Vector Store / Document Store] (RAG)
  ├─> [Object Storage] (resume PDFs, artifacts)
  ├─> [Relational DB] (metadata, job status, audit)
  └─> [Cache] (prompt caching, throttling, idempotency)

Observability Plane: [Metrics] + [Logs] + [Traces] + [LLM Telemetry] + [Cost]
Security Plane: [Secrets] + [Encryption] + [PII Redaction] + [Network Policies]
```

Primary request flows:

- Synchronous (fast):

  1. Client calls `POST /optimize` with resume/job details
  2. FastAPI validates, authenticates, rate-limits, creates `request_id`
  3. CrewAI orchestrator runs short agent chain (<= 5s)
  4. Response streamed back; metrics + logs + cost recorded

- Asynchronous (long-running or batch):
  1. Client submits job → returns `job_id`
  2. Worker picks job from queue (SQS/Service Bus/Celery/Arq)
  3. CrewAI runs full multi-agent workflow, saving intermediate artifacts
  4. Job status and results stored; client polls or receives webhook

---

### 3) Step-by-Step: Production Hardening Roadmap

1. API & UI foundations

   - Define stable API contracts (OpenAPI) with request/response schemas
   - Add input validation (Pydantic), idempotency keys, and strict timeouts
   - Introduce a background job mode for heavy flows (queue + worker)

2. Configuration & environments

   - Create `.env` per environment; load via `pydantic-settings`
   - Split configs: `dev`, `staging`, `prod` with safe defaults and secure overrides
   - Version and pin model providers and embeddings versions

3. Observability baseline

   - Logging: structured JSON logs with `request_id`, `user_id`, `job_id`, `agent`, `tool`, `model`, `latency_ms`, `status`, `error`
   - Metrics: FastAPI + custom LLM counters/gauges (requests, durations, tokens, costs)
   - Tracing: OpenTelemetry across API → orchestrator → tool calls → model provider

4. Evaluation harness (quality + safety)

   - Golden test sets: resumes + job descriptions + expected outputs (store under `tests/regression/data/`)
   - Automatic eval: use Ragas / Promptfoo / LangSmith / TruLens for factuality, relevance, structure
   - LLM-as-judge with strict rubrics (JSON) for grading; store scores + explanations
   - Regression gate in CI: block deploy if quality drops beyond thresholds

5. Cost controls

   - Token accounting per request/agent/tool; model price table by env
   - Budgets and alerts (per request, per user, per day)
   - Prompt caching (Redis), response reuse, and model routing (cheap-fast vs expensive-accurate)

6. Reliability & performance

   - Timeouts, retries with jitter, circuit breakers, fallback models
   - Idempotency for tool calls and external APIs
   - Concurrency limits and backpressure; async streaming responses
   - Queue workers for long jobs; dead-letter queues for failures

7. Security & compliance

   - AuthN: OIDC (Auth0/Cognito/Azure AD) → JWT in API
   - AuthZ: role-based access control for endpoints and operations
   - PII redaction before logging; encryption in transit (TLS) and at rest
   - Secrets in cloud vaults; audit logs; data retention and deletion policies

8. CI/CD & releases

   - GitHub Actions: lint, typecheck, tests, eval, container build, SBOM, scan
   - Progressive delivery: dev → staging (shadow/A-B) → prod with canaries
   - Release notes + prompt versioning; rollback strategy

9. Documentation & runbooks
   - Operator runbooks (incident response, escalation)
   - On-call dashboards and alerts; SLOs (availability, latency, quality)
   - Clear feature flags and experiment toggles

---

### 4) Evaluation: What, Why, and How

Key quality dimensions:

- Factuality & hallucination rate (grounded in sources or explicit assumptions)
- Relevance to job description (skills match, keywords, ATS friendliness)
- Structure and formatting (consistent JSON/Markdown sections)
- Actionability (clear, concise suggestions vs vague text)

Recommended tooling and approach:

- Offline eval (CI):
  - Maintain a diverse golden set; include edge cases and multilingual samples
  - Use Ragas/Promptfoo/LangSmith/TruLens to compute: relevance, faithfulness, coherence, structure adherence
  - Use LLM-as-judge with deterministic prompts and temperature 0; aggregate scores
- Online eval (prod):
  - Capture explicit user ratings (thumbs up/down + reason codes)
  - Track downstream success proxies (interview callbacks if integrated)
- Safety checks:
  - Toxicity and PII detection on outputs; block or redact

Metrics to track (store per request):

- `input_tokens`, `output_tokens`, `cost_usd`, `latency_ms`
- `hallucination_score`, `structure_score`, `relevance_score`
- `num_retries`, `fallback_used`, `cache_hit`

Use thresholds in CI to prevent regressions (e.g., relevance >= 0.85; cost within +10%).

---

### 5) Cost Management and Model Strategy

- Maintain a model price catalog (per 1K tokens) and update periodically
- Implement model routing by tier: draft mode (small/cheap), finalization (larger/few-shot)
- Prompt compression and retrieval narrowing to reduce context length
- Cache embeddings and RAG chunks; reuse calculations across similar jobs
- Daily/weekly cost reports and per-user budgets; alert on spikes

---

### 6) Reliability Patterns

- Timeouts at each boundary (API, model calls, tool calls)
- Retries with exponential backoff + jitter where safe; never for non-idempotent ops
- Circuit breakers to protect providers; automatic recovery
- Idempotency keys for job submissions and external tool integrations
- Degraded modes: disable non-critical agents/tools during incidents
- Dead-letter queues and automated retry workflows for background jobs

---

### 7) Security and Compliance

- AuthN via OIDC: support enterprise identity (Azure AD/Okta/Auth0)
- AuthZ: RBAC and least-privilege service roles; tenant isolation if multi-tenant
- Secrets: store in AWS Secrets Manager / Azure Key Vault; never in code
- Data handling: encrypt at rest (S3/KMS or Blob/Key Vault), PII redaction before logs
- Network: private subnets, security groups/NSGs, WAF in front of API, egress controls
- Audit: immutable logs, retention policies, access logging for artifacts and data
- Compliance readiness: SOC2 controls, GDPR/DSAR workflows, data residency if needed

---

### 8) AWS Reference Architecture (Why and How)

Why AWS fits:

- Managed building blocks: Bedrock (models), S3 (artifacts), RDS (metadata), ElastiCache (cache), SQS (queue), CloudWatch (observability), Secrets Manager (secrets), IAM (access), ECS/EKS (compute)
- Strong enterprise support and governance tooling

Minimal to production progression:

1. Minimal viable prod (MVP):

   - ECS Fargate service running FastAPI behind ALB + WAF
   - S3 for resume PDFs and generated artifacts
   - RDS Postgres for metadata and jobs
   - SQS for background processing; Fargate worker service
   - ElastiCache Redis for caching and rate limiting
   - Bedrock or OpenAI via API for LLMs
   - CloudWatch logs/metrics; X-Ray or OTEL collector for traces
   - Secrets Manager for API keys and DB creds

2. Scale-up:
   - Private subnets, NAT for egress; VPC endpoints to S3/Bedrock
   - Autoscaling on ECS; multi-AZ RDS; global accelerators if needed
   - EventBridge for orchestration and audit events

Suggested repo layout for infra:

```
infra/
  terraform/
    aws/
      networking/
      data/
      compute/
      observability/
      security/
```

OIDC-based deploy (no long-lived keys) with GitHub Actions → AWS IAM role.

---

### 9) Azure Reference Architecture (Why and How)

Why Azure fits:

- First-class enterprise identity (AAD), Azure OpenAI, strong governance
- Managed equivalents to AWS services with tight integration

Minimal to production progression:

1. Minimal viable prod (MVP):

   - Azure Container Apps (or AKS) for FastAPI; Front Door + WAF in front
   - Azure Blob Storage for artifacts
   - Azure Database for PostgreSQL
   - Azure Service Bus for background jobs; worker container app
   - Azure Cache for Redis
   - Azure OpenAI for models
   - Application Insights + Log Analytics for observability
   - Key Vault for secrets; Managed Identity for access

2. Scale-up:
   - AKS with HPA, node pools, private cluster
   - Private endpoints to OpenAI/Blob/DB; VNet integration
   - Event Grid for audit/events

Suggested repo layout mirrors AWS (use `infra/terraform/azure/`). Use workload identity federation from GitHub → Azure.

---

### 10) CI/CD and Release Strategy

- GitHub Actions workflows:
  - `build.yml`: lint, tests, eval suite, docker build & push, SBOM + container scan
  - `deploy.yml`: infra plan/apply (Terraform) → deploy app (Helm/Kustomize/ACA revisions) → smoke tests → notify
- Branching: trunk-based with short-lived feature branches; protected main; required checks
- Promotions: dev → staging (shadow traffic / A-B) → prod (canary 10% → 100%)
- Rollbacks: image pinning + Helm/Kustomize rollback; DB migrations versioned and reversible

---

### 11) Data, Prompts, and Experimentation

- Prompt registry: version prompts with semantic labels and attach eval scores
- Feature flags: toggle agents/tools/prompt variants in runtime
- Experiment tracking: log model, temperature, tools used, eval results, and costs per experiment run
- Dataset governance: maintain anonymized corpora for testing; PII removal pipelines

---

### 12) SLOs, Dashboards, and Alerts (starter set)

- Availability: 99.9% API success rate (non-5xx)
- Latency: p95 < 1.5s for simple, p95 < 15s for long-running
- Quality: relevance score p50 ≥ 0.85; structure adherence ≥ 0.95
- Cost: average cost/request within budget; alert on +25% deviations

Dashboards:

- API: RPS, latency, error rates, rate-limit rejections
- LLM: token usage, cost, retries, fallbacks, provider errors
- Queue: job backlog, processing times, DLQ size
- Quality: eval scores over time; regression deltas by commit

Alerts:

- 5xx rate spikes, DLQ growth, cost anomalies, eval regression, provider outage

---

### 13) Concrete Next Steps (Week-by-Week)

Week 1–2 (Foundations)

- Add structured logging + request IDs; instrument FastAPI metrics
- Add OpenTelemetry tracing and propagate through CrewAI tools
- Implement token & cost accounting wrapper; expose `/metrics` (Prometheus)

Week 3–4 (Eval & Reliability)

- Create golden dataset and integrate Promptfoo/Ragas in CI
- Add timeouts/retries/circuit breaker; add Redis cache
- Introduce background worker + queue for long jobs

Week 5–6 (Cloud & CI/CD)

- Containerize and deploy MVP to AWS ECS Fargate (or Azure Container Apps)
- Wire S3/Blob, RDS/Postgres, Redis, SQS/Service Bus, Secrets Manager/Key Vault
- Set up GitHub Actions OIDC deploy; add smoke tests and basic alerts

Week 7–8 (Security & Scale)

- Add OIDC login and RBAC; PII redaction; audit logs
- Add model routing and prompt caching; budgets and alerts
- Introduce A/B experimentation for prompts and tools

---

### 14) Operational Runbooks (abridged)

- Incident response: identify failing dependency (LLM, DB, queue), enable degraded mode, drain queue, rollback prompt/app, notify
- On-call actions: reprocess DLQ, purge stuck jobs, rotate keys, flip feature flags, scale workers
- Data purging: scheduled deletion for uploads after X days; GDPR DSAR handling

---

### 15) Interview-Ready Project Report (Talking Points)

- Problem: Automate and improve resumes against job descriptions with multi-agent orchestration
- Architecture: FastAPI + CrewAI agents + Streamlit; added background jobs, RAG, caching, and robust observability
- Reliability: timeouts, retries, circuit breakers, idempotency, DLQ, degraded modes
- Security: OIDC, RBAC, PII redaction, secrets in vaults, encryption, WAF
- Evaluation: golden datasets + LLM-as-judge; regression gates in CI; quality and cost SLOs
- Cloud: reference deployments on AWS (ECS/S3/RDS/SQS/Redis/Bedrock) and Azure (ACA/Blob/Postgres/Service Bus/Redis/Azure OpenAI)
- Results: reduced hallucinations via tools and RAG; predictable costs via caching and routing; improved quality scores over baselines
- Lessons: prompt versioning is critical; background jobs for predictability; observability accelerates iteration

---

### 16) Example Command Snippets (illustrative)

Dev run with uv and FastAPI:

```bash
uv sync --all-extras --dev
uv run uvicorn resume_optimiser.api:app --reload --host 0.0.0.0 --port 8000
```

Docker build & run locally:

```bash
docker build -t resume-optimiser:local -f crew/resume_optimiser/Dockerfile .
docker run --rm -p 8000:8000 --env-file crew/resume_optimiser/.env.local resume-optimiser:local
```

GitHub Actions OIDC → AWS example (high level):

```bash
# In AWS: create an IAM role with a trust policy for GitHub's OIDC provider
# In repo: use aws-actions/configure-aws-credentials with role-to-assume
```

Terraform layout (skeleton):

```bash
infra/terraform/aws/
  main.tf    # providers, remote state
  vpc.tf     # networking
  ecs.tf     # ecs service + task definitions
  rds.tf     # postgres
  s3.tf      # artifact bucket
  sqs.tf     # queues + DLQ
  redis.tf   # ElastiCache
  observability.tf # cloudwatch, x-ray
  iam.tf     # roles & permissions
```

---

### 17) Checklist (use in PRs and releases)

- Observability: logs/metrics/traces present and linked to request_id
- Evaluation: test set updated; CI eval passed thresholds
- Security: secrets in vault; PII redaction verified; WAF rules updated
- Reliability: timeouts/retries/circuit breakers configured; DLQ empty
- Cost: model routing and caching enabled; budget dashboards green
- Docs: runbook updated; versioned prompts and release notes

---

This playbook is designed to be actionable. Start with observability and evaluation, introduce background jobs and caching, then move to cloud deployment with strict security, reliability, and cost controls. Iterate with measurements and use the CI eval gate to protect quality as you scale.

# Enterprise System Design - Resume Optimizer

## 🏗️ **Target Architecture Overview**

### **Microservices Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        API GATEWAY                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Auth      │ │   Rate      │ │   Load      │ │   Circuit   ││
│  │   Service   │ │   Limiting  │ │   Balancer  │ │   Breaker   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│ Resume Service │    │  Job Analysis   │    │  File Management│
│                │    │    Service      │    │    Service      │
│ - CrewAI Agents│    │ - Web Scraping  │    │ - S3 Operations │
│ - Processing   │    │ - Job Parsing   │    │ - File Storage  │
│ - Optimization │    │ - Requirements  │    │ - CDN Delivery  │
└────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    Message Queue      │
                    │   (Redis/RabbitMQ)    │
                    │  - Task Scheduling    │
                    │  - Event Streaming    │
                    │  - Job Management     │
                    └───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│   PostgreSQL   │    │      Redis      │    │   Vector DB     │
│                │    │                 │    │  (Pinecone)     │
│ - Job Metadata │    │ - Caching       │    │ - Resume        │
│ - User Data    │    │ - Sessions      │    │   Embeddings    │
│ - Audit Logs   │    │ - Rate Limiting │    │ - Similarity    │
└────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Service Decomposition Strategy**

#### **1. Resume Processing Service**

```python
# Core responsibilities:
- CrewAI agent orchestration
- Resume analysis and optimization
- Content generation and formatting
- Quality assurance and validation

# Technology Stack:
- FastAPI + Pydantic
- CrewAI framework
- OpenAI API integration
- Custom ML models (optional)
```

#### **2. Job Analysis Service**

```python
# Core responsibilities:
- Web scraping job postings
- Job requirement extraction
- Company research and analysis
- Market intelligence gathering

# Technology Stack:
- FastAPI + BeautifulSoup/Scrapy
- Serper API integration
- NLP processing
- Data enrichment pipelines
```

#### **3. File Management Service**

```python
# Core responsibilities:
- File upload/download handling
- S3 storage operations
- CDN integration
- File processing and conversion

# Technology Stack:
- FastAPI + boto3
- CloudFront CDN
- File processing libraries
- Virus scanning integration
```

#### **4. Notification Service**

```python
# Core responsibilities:
- Real-time progress updates
- Email notifications
- WebSocket connections
- Push notifications

# Technology Stack:
- FastAPI + WebSockets
- Celery for background tasks
- Email service integration
- Push notification services
```

#### **5. User Management Service**

```python
# Core responsibilities:
- Authentication and authorization
- User profile management
- Subscription handling
- Usage tracking and billing

# Technology Stack:
- FastAPI + JWT
- OAuth 2.0 integration
- PostgreSQL for user data
- Stripe for payments
```

## 🔄 **Event-Driven Architecture**

### **Event Flow Diagram**

```
User Upload → File Service → Event Bus → Resume Service
     │              │           │            │
     ▼              ▼           ▼            ▼
WebSocket ← Notification ← Event Bus ← Processing Complete
     │              │           │            │
     ▼              ▼           ▼            ▼
Real-time UI ← Email/SMS ← Event Bus ← Job Analysis Service
```

### **Key Events**

1. **File Uploaded** → Trigger resume processing
2. **Job Analysis Complete** → Update progress
3. **Resume Optimized** → Send notification
4. **Error Occurred** → Alert and retry
5. **User Subscription Changed** → Update permissions

## 🚀 **Scalability Patterns**

### **Horizontal Scaling**

- **Auto-scaling groups** based on CPU/memory metrics
- **Load balancing** across multiple service instances
- **Database sharding** for large datasets
- **CDN distribution** for global performance

### **Vertical Scaling**

- **Resource optimization** for each service
- **Memory management** for large file processing
- **CPU optimization** for ML workloads
- **Storage optimization** with compression

### **Caching Strategy**

```python
# Multi-layer caching
L1: Application-level (in-memory)
L2: Redis (distributed)
L3: CDN (global)
L4: Database query cache

# Cache invalidation
- Time-based TTL
- Event-driven invalidation
- Manual cache clearing
- Version-based invalidation
```

## 🔒 **Security Architecture**

### **Authentication & Authorization**

```python
# JWT-based authentication
{
  "user_id": "uuid",
  "email": "user@example.com",
  "roles": ["premium_user"],
  "permissions": ["resume_optimization", "bulk_processing"],
  "exp": 1640995200
}

# RBAC (Role-Based Access Control)
- Admin: Full system access
- Premium: Unlimited processing
- Basic: Limited processing
- Free: Trial access only
```

### **Data Protection**

- **Encryption at rest** (AES-256)
- **Encryption in transit** (TLS 1.3)
- **PII detection** and masking
- **Data retention policies**
- **GDPR compliance** for EU users

### **Network Security**

- **VPC** with private subnets
- **WAF** (Web Application Firewall)
- **DDoS protection**
- **API rate limiting**
- **Input validation** and sanitization

## 📊 **Monitoring & Observability**

### **Three Pillars of Observability**

#### **1. Metrics (Prometheus + Grafana)**

```python
# Key metrics to track
- API response times
- Error rates by service
- Resource utilization
- Business metrics (jobs processed, user activity)
- Cost metrics (API calls, storage usage)
```

#### **2. Logs (ELK Stack)**

```python
# Structured logging
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "resume-service",
  "trace_id": "abc123",
  "user_id": "user456",
  "message": "Resume optimization completed",
  "duration_ms": 15000,
  "job_id": "job789"
}
```

#### **3. Traces (Jaeger/Zipkin)**

```python
# Distributed tracing
Resume Request → File Upload → Job Analysis → Resume Processing → Notification
     │              │             │              │                │
   Start          Upload        Analysis      Processing       Complete
   (0ms)         (500ms)       (2000ms)      (12000ms)       (15000ms)
```

## 🎯 **Performance Optimization**

### **Database Optimization**

```sql
-- Indexing strategy
CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_files_hash ON files(content_hash);

-- Partitioning for large tables
CREATE TABLE job_results_2024 PARTITION OF job_results
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### **API Optimization**

```python
# Response compression
app.add_middleware(CompressionMiddleware, minimum_size=1000)

# Connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# Async processing
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
```

### **Caching Implementation**

```python
# Redis caching
@cache(ttl=3600)
async def get_job_analysis(job_url: str) -> JobAnalysis:
    # Expensive operation cached for 1 hour
    pass

# Application-level caching
@lru_cache(maxsize=1000)
def get_company_info(company_name: str) -> CompanyInfo:
    # Frequently accessed data cached in memory
    pass
```

## 🔧 **DevOps & CI/CD**

### **Container Strategy**

```dockerfile
# Multi-stage builds
FROM python:3.11-slim as base
# ... dependencies

FROM base as development
# ... dev tools

FROM base as production
# ... optimized runtime
```

### **Kubernetes Deployment**

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: resume-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: resume-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### **CI/CD Pipeline**

```yaml
# GitHub Actions workflow
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest
      - name: Security scan
        run: bandit -r src/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EKS
        run: kubectl apply -f k8s/
```

This system design provides a solid foundation for enterprise-scale deployment while maintaining the flexibility to evolve with your business needs.
