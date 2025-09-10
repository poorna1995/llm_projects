I’m going to create a clear 12-step roadmap (as todos) and then outline each step in a week-by-week timeline with what, why, concepts, Azure services, and acceptance criteria so you understand both the flow and the reasoning.

[1 tool called]

Let’s walk this end-to-end with a simple, weekly timeline. I’ll tell you exactly what to do first, why it matters, the core concepts to learn, the Azure services involved, and how you’ll know it’s done.

- I just created a 12-step roadmap so we can track progress as we go. I’ll mark items complete as we finish each stage.

### Week 1 — Foundations and repo hygiene (roadmap-01-foundations)

- What to do:
  - Set up Azure subscription, resource groups: dev, staging, prod.
  - Create `.env.example`, secrets policy, and `.gitignore` hygiene.
  - Establish repo structure: `services/api`, `services/worker`, `services/bento-resume-ml`, `k8s/`, `infra/azure/`, `ops/`, `prompts/`, `evals/`.
  - Decide branching model: trunk + PRs; protected `main`.
- Why:
  - Clean foundations prevent rework and make cloud deploys predictable.
- Concepts:
  - Environments (dev/stage/prod), least privilege, Git branching.
- Azure:
  - Azure Portal basics; Resource Groups per env.
- Done when:
  - Repo layout exists; RGs created; docs/READMEs added.

### Week 2 — Containerize API and Worker (roadmap-02-containers)

- What:
  - Write Dockerfiles for FastAPI and CrewAI worker.
  - Add Docker Compose for local multi-service dev.
- Why:
  - Containers make your app portable and reproducible.
- Concepts:
  - Container images, layers, tags, health endpoints.
- Done when:
  - `docker compose up` runs api + worker locally; basic health checks pass.

### Week 3 — Async jobs with Azure Service Bus (roadmap-03-queue)

- What:
  - In FastAPI: `POST /v1/jobs` enqueues to Service Bus, returns `202 + job_id`.
  - In Worker: consume from Service Bus; update DB status.
- Why:
  - Keeps API fast; heavy work moves to background.
- Concepts:
  - Queues, at-least-once processing, DLQ, idempotency.
- Azure:
  - Service Bus queue + DLQ; SDK in Python.
- Done when:
  - Submitting a job immediately returns; worker processes it and updates status.

### Week 4 — BentoML + ONNX Runtime microservice (roadmap-04-bento-onnx)

- What:
  - Create `services/bento-resume-ml` with endpoints:
    - `/parse_resume`, `/extract_skills`, `/score_match`
  - Package ONNX models and containerize via `bentoml containerize`.
- Why:
  - Fast, cheap, deterministic ML for structure; LLM focuses on writing.
- Concepts:
  - ONNX Runtime sessions, Bento services, versioned model packaging.
- Done when:
  - You can `docker run` Bento and hit its endpoints locally.

### Week 5 — Wire workers to Bento (roadmap-05-wire-bento)

- What:
  - Worker calls Bento first; persists structured outputs (sections, skills, scores).
  - Then calls LLM to rewrite résumé using structured facts.
- Why:
  - Better quality and lower LLM cost; repeatable pipelines.
- Concepts:
  - Service-to-service HTTP, retries, timeouts, circuit breakers.
- Done when:
  - End-to-end local run produces improved tailored résumé files.

### Week 6 — Kubernetes manifests and autoscaling (roadmap-06-k8s-local)

- What:
  - Author Deployments/Services for api, worker, bento; add HPA and probes.
  - Use kind/minikube or your cloud dev AKS for a local-like cluster test.
- Why:
  - Prepare for cloud deployment with stable runtime configs.
- Concepts:
  - Deployments, Services, Ingress, HPA, requests/limits, readiness/liveness.
- Done when:
  - All three services run in K8s; only api is exposed via Ingress.

### Week 7 — Provision Azure core resources (roadmap-07-azure-core)

- What:
  - Using Terraform/Bicep, create: AKS, ACR, PostgreSQL, Blob Storage, Service Bus, Key Vault, Log Analytics + App Insights.
- Why:
  - Managed services give reliability and observability out of the box.
- Concepts:
  - IaC, state, variables, modules; managed identities.
- Done when:
  - `terraform apply` (or Bicep) stands up all core services.

### Week 8 — Networking and secrets (roadmap-08-networking)

- What:
  - VNet + private endpoints for Blob, Postgres, Service Bus, Azure OpenAI.
  - Enable Managed Identity/Workload Identity; mount secrets via Key Vault CSI.
- Why:
  - Secure-by-default networking and secret management.
- Concepts:
  - Private Link, subnets, NSGs, Key Vault, identities and RBAC.
- Done when:
  - Pods access services privately; no secrets in code; rotation works.

### Week 9 — Deploy to AKS and expose API (roadmap-09-aks-deploy)

- What:
  - Push images to ACR; deploy api/worker/bento to AKS.
  - Ingress Controller (NGINX/AGIC); only `api` exposed.
- Why:
  - Controlled, scalable runtime with cluster autoscaler and HPAs.
- Concepts:
  - Image pulls from ACR, service DNS, internal vs public endpoints.
- Done when:
  - Public hostname serves FastAPI; worker and bento reachable inside cluster.

### Week 10 — API Gateway with security and policies (roadmap-10-apim)

- What:
  - Put Azure API Management in front of Ingress.
  - Configure JWT (Entra ID), rate limits, request validation, CORS.
- Why:
  - Enterprise‑grade control, observability, and secure edge.
- Concepts:
  - APIM products/policies, WAF integration (with Front Door if needed).
- Done when:
  - Public traffic must pass APIM; invalid requests blocked; valid requests succeed.

### Week 11 — Observability end-to-end (roadmap-11-observability)

- What:
  - Add OpenTelemetry to api/worker/bento; correlate traces; JSON logs; metrics.
  - Dashboards/alerts in App Insights/Azure Monitor (p95, error rate, queue age, cost).
- Why:
  - You can see bottlenecks, costs, and failures in one place.
- Concepts:
  - Tracing spans, context propagation, SLOs, alert rules.
- Done when:
  - Click a request in App Insights and see api → worker → bento → LLM spans and metrics.

### Week 12 — Guardrails and evaluations (roadmap-12-guardrails-evals)

- What:
  - Add Azure AI Content Safety; PII redaction pre‑LLM; output checks.
  - Add offline evals (Ragas/DeepEval) to CI; canary rollouts for models/prompts.
- Why:
  - Quality and safety gates for production confidence.
- Concepts:
  - Safety filters, eval datasets, thresholds, canaries and rollback.
- Done when:
  - Pipelines block bad changes; canary succeeds before full rollout.

### Key checkpoints you’ll feel week-by-week

- Weeks 1–2: You can run api + worker locally in containers.
- Week 3: API is responsive; background jobs work reliably.
- Weeks 4–5: Results improve and cost drops thanks to Bento+ONNX.
- Week 6: You’re K8s-ready with manifests and autoscaling.
- Weeks 7–9: Cloud infra up; app runs on AKS; private networking in place.
- Week 10: Secure public edge with APIM.
- Week 11: Full visibility and alerts.
- Week 12: Safety and quality gates; canary releases.

Would you like me to:

- Scaffold the `infra/azure/` Terraform modules and `k8s/` manifests that match this plan?
- Or start by containerizing your current FastAPI and worker (step 2) so you can run them with Docker Compose today?
