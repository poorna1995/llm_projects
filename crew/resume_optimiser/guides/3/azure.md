I'll scaffold the repo structure and template files for Week 1 (directories, .env.example, README stubs, .gitignore hygiene) so you can start immediately, then I’ll explain the concepts and the step-by-step actions to complete Week 1.

[1 tool called]

I’ll guide you through Week 1 step by step so you understand what you’re doing and why. Follow these steps in order; you can complete them in 1–2 days.

### Concepts you need (simple)

- Environments: separate “dev”, “staging”, “prod” to avoid breaking production while testing.
- Resource Group (RG): a named folder in Azure that holds cloud resources for one environment.
- Least privilege: give each app or person only the access they need, nothing more.
- Trunk-based Git: one main branch (`main`) with short-lived feature branches merged via PRs.

### Prerequisites (one-time)

- Install Azure CLI: `brew install azure-cli`
- Login: `az login`
- If you have multiple subscriptions: `az account list -o table` then `az account set --subscription "<SUBSCRIPTION_NAME_OR_ID>"`

### Step 1: Create Azure resource groups for each environment

- Why: clean isolation and cost tracking per env.
- Command (pick your Azure region, e.g., `eastus`):

```bash
az group create --name rg-resume-optimiser-dev --location eastus
az group create --name rg-resume-optimiser-staging --location eastus
az group create --name rg-resume-optimiser-prod --location eastus
```

- Verify:

```bash
az group list -o table
```

### Step 2: Set up repo structure

- Why: consistent folders let you iterate fast and deploy cleanly.
- Create directories (you can do this in Finder or Terminal):

```bash
mkdir -p services/api services/worker services/bento-resume-ml
mkdir -p k8s/base k8s/overlays/dev k8s/overlays/staging k8s/overlays/prod
mkdir -p infra/azure ops/dashboards ops/runbooks prompts evals
```

- What each directory is for:
  - `services/api`: FastAPI orchestration (public API)
  - `services/worker`: CrewAI workers (long jobs)
  - `services/bento-resume-ml`: BentoML + ONNX Runtime service
  - `k8s/`: Kubernetes manifests/Helm (base and per-env overlays)
  - `infra/azure`: Terraform/Bicep for Azure (AKS, APIM, Service Bus, Blob, Postgres, Key Vault)
  - `ops/`: dashboards, runbooks, observability configs
  - `prompts/`: versioned prompts and policies
  - `evals/`: offline evaluation datasets and thresholds

### Step 3: Create .gitignore and .env.example

- Why: avoid committing secrets and clutter; align local env variables across team.

Add to `.gitignore` (if not already present):

```gitignore
.env
.env.*
.venv/
__pycache__/
*.pyc
.DS_Store
dist/
build/
*.egg-info/
.coverage
htmlcov/
.pytest_cache/
.cache/
```

Create `.env.example` (template only, never real secrets):

```env
APP_ENV=dev
LOG_LEVEL=INFO

AZURE_SUBSCRIPTION_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

AZURE_SERVICE_BUS_NAMESPACE=
AZURE_SERVICE_BUS_QUEUE_NAME=
AZURE_SERVICE_BUS_CONNECTION_STRING=

AZURE_STORAGE_ACCOUNT=
AZURE_BLOB_CONTAINER=
AZURE_STORAGE_CONNECTION_STRING=

AZURE_POSTGRES_HOST=
AZURE_POSTGRES_DB=
AZURE_POSTGRES_USER=
AZURE_POSTGRES_PASSWORD=

AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_NAME=

AZURE_KEY_VAULT_NAME=
AZURE_APPINSIGHTS_CONNECTION_STRING=

BENTO_URL=http://resume-ml:3000
OTEL_EXPORTER_OTLP_ENDPOINT=
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501
```

- Concept: in development you’ll use a local `.env` (not committed) populated from this template. In cloud, secrets come from Key Vault (not from `.env`).

### Step 4: Write a short secrets policy

- Why: to stay safe from day 1.
- Put this in `ops/runbooks/secrets_policy.md` (short and clear):
  - Never commit `.env` or keys/tokens to Git.
  - Use Azure Key Vault for all secrets in cloud.
  - Local dev: copy `.env.example` to `.env` and fill locally.
  - Rotate credentials quarterly or on suspicion of compromise.

### Step 5: Add READMEs to each main folder

- Why: future you (and teammates) need quick context.
- Minimal content (1–3 lines each):
  - `services/api/README.md`: “FastAPI orchestration service; public API.”
  - `services/worker/README.md`: “CrewAI worker; consumes jobs from Service Bus.”
  - `services/bento-resume-ml/README.md`: “Internal BentoML + ONNX service for parsing/extraction/scoring.”
  - `k8s/README.md`: “Base manifests and environment overlays.”
  - `infra/azure/README.md`: “Terraform/Bicep modules for AKS, APIM, Service Bus, Blob, Postgres, Key Vault, Monitor.”
  - `ops/README.md`: “Dashboards, runbooks, observability.”
  - `prompts/README.md`: “Versioned prompts/policies.”
  - `evals/README.md`: “Offline eval datasets and thresholds.”

### Step 6: Decide your branching model and protect main

- Why: safe, consistent delivery.
- Use trunk-based development:
  - Create feature branches like `feat/queue-integration` or `fix/api-timeout`.
  - Open PRs to `main`, require review + status checks (tests/lint).
  - Enable “Require pull request reviews before merging” on `main`.
  - Optional: Conventional Commits (e.g., `feat: add service bus enqueue`).
- In GitHub:
  - Settings → Branches → Add branch protection rule → `main` → require PR, status checks, disallow force push.

### Step 7: Document what’s done (acceptance checklist)

- In `crew/resume_optimiser/guides/2/detail.md` (or a new `WEEK_1.md`), add a short checklist:
  - RGs created: `rg-resume-optimiser-dev`, `rg-resume-optimiser-staging`, `rg-resume-optimiser-prod`
  - Repo folders created and described
  - `.gitignore` updated; `.env.example` created
  - Secrets policy file created
  - Branch protection enabled on `main`

### (Optional) Step 8: Prepare CI/CD identity now (will help later)

- Why: Your pipelines will need scoped access to the dev resource group.
- Create a service principal scoped to dev RG:

```bash
az ad sp create-for-rbac \
  --name spn-resume-optimiser-dev \
  --role Contributor \
  --scopes $(az group show -n rg-resume-optimiser-dev --query id -o tsv)
```

- Save the output (appId, password, tenant). Do NOT commit. You’ll store these in GitHub Actions secrets or Key Vault later.

### Understanding the flow you just set up

- You created isolated “folders” in Azure for each environment where your future resources (AKS, Service Bus, Blob, Postgres, Key Vault) will live.
- Your repo now mirrors your runtime architecture: API (public), Worker (background), Bento (internal inference), infra definitions, k8s manifests, operations, prompts, evals.
- Your team (even if it’s just you) has rules for secrets and Git, which reduces risk and makes future steps (containers, Kubernetes, Azure deploys) smoother.

If you want, I can generate the folder skeletons and template files for you automatically, or we can proceed to Week 2 (containerizing API and Worker) and I’ll give you precise Dockerfiles and a minimal Docker Compose to run locally.
