# Production Deployment Guide

## Resume Optimizer - Enterprise Deployment

### Prerequisites

#### 1. Infrastructure Requirements

- **Cloud Provider**: AWS/Azure/GCP account
- **Kubernetes Cluster**: EKS/GKE/AKS (or local minikube for testing)
- **Container Registry**: ECR/GCR/ACR
- **Database**: PostgreSQL 13+ with high availability
- **Cache**: Redis 6+ with clustering
- **Storage**: S3/GCS/Azure Blob with versioning
- **Monitoring**: Prometheus + Grafana + ELK Stack

#### 2. Development Tools

- **kubectl**: Kubernetes command-line tool
- **helm**: Package manager for Kubernetes
- **terraform**: Infra structure as Code
- **docker**: Container runtime
- **git**: Version control

### Phase 1: Infrastructure Setup

#### 1.1 AWS Infrastructure (Terraform)

```hcl
# main.tf
provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "resume-optimizer-vpc"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = "resume-optimizer-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier = "resume-optimizer-db"
  engine     = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"
  allocated_storage = 100
  storage_encrypted = true

  db_name  = "resume_optimizer"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "resume-optimizer-final-snapshot"
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "resume-optimizer-redis"
  description                = "Redis cluster for resume optimizer"

  node_type                  = "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = "default.redis7"

  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true

  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
}
```

#### 1.2 Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: resume-optimizer
  labels:
    name: resume-optimizer

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: resume-optimizer
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/resume_optimizer"
  REDIS_URL: "redis://redis:6379"
  S3_BUCKET: "resume-optimizer-storage"
  LOG_LEVEL: "INFO"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: resume-optimizer
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-key>
  SERPER_API_KEY: <base64-encoded-key>
  AWS_ACCESS_KEY_ID: <base64-encoded-key>
  AWS_SECRET_ACCESS_KEY: <base64-encoded-key>
  JWT_SECRET: <base64-encoded-secret>

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-optimizer-api
  namespace: resume-optimizer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: resume-optimizer-api
  template:
    metadata:
      labels:
        app: resume-optimizer-api
    spec:
      containers:
        - name: api
          image: resume-optimizer:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DATABASE_URL
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: OPENAI_API_KEY
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: resume-optimizer-api-service
  namespace: resume-optimizer
spec:
  selector:
    app: resume-optimizer-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: resume-optimizer-ingress
  namespace: resume-optimizer
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
    - hosts:
        - api.resume-optimizer.com
      secretName: resume-optimizer-tls
  rules:
    - host: api.resume-optimizer.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: resume-optimizer-api-service
                port:
                  number: 80
```

### Phase 2: Database Migration

#### 2.1 Database Schema

```sql
-- migrations/001_initial_schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_url TEXT NOT NULL,
    company_name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    progress TEXT,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Files table
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    content_type VARCHAR(100),
    hash VARCHAR(64) UNIQUE,
    s3_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_files_hash ON files(hash);
CREATE INDEX idx_files_job_id ON files(job_id);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2 Database Connection Pool

```python
# database/connection.py
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"),
            min_size=10,
            max_size=20,
            command_timeout=60
        )

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if not self.pool:
            await self.create_pool()

        async with self.pool.acquire() as connection:
            yield connection

db_manager = DatabaseManager()
```

### Phase 3: Application Updates

#### 3.1 Async FastAPI with Database Integration

```python
# api/async_api.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
import uuid

from database.connection import db_manager
from models import JobCreate, JobResponse, UserCreate, UserResponse
from services.job_service import JobService
from services.auth_service import AuthService

app = FastAPI(
    title="Resume Optimizer API",
    description="Enterprise-grade resume optimization service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security
security = HTTPBearer()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.resume-optimizer.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.resume-optimizer.com", "*.resume-optimizer.com"]
)

# Dependency injection
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.post("/jobs", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Create a new resume optimization job"""
    async with db_manager.get_connection() as conn:
        job_service = JobService(conn)
        job_id = await job_service.create_job(
            user_id=current_user,
            job_url=job.job_url,
            company_name=job.company_name
        )

        # Start background processing
        background_tasks.add_task(
            process_job_async,
            job_id,
            job.job_url,
            job.company_name
        )

        return JobResponse(
            id=job_id,
            status="queued",
            created_at=datetime.utcnow()
        )

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get job status and results"""
    async with db_manager.get_connection() as conn:
        job_service = JobService(conn)
        job = await job_service.get_job(job_id, current_user)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

# Health checks
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/ready")
async def readiness_check():
    """Readiness check with dependencies"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "s3": await check_s3()
    }

    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")
```

#### 3.2 Background Job Processing

```python
# services/job_processor.py
import asyncio
from celery import Celery
from celery.signals import task_prerun, task_postrun
import logging

# Celery configuration
celery_app = Celery(
    'resume_optimizer',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000
)

@celery_app.task(bind=True, name='process_resume_optimization')
def process_resume_optimization(self, job_id: str, job_url: str, company_name: str):
    """Process resume optimization in background"""
    try:
        # Update job status
        update_job_status(job_id, 'running', 'Initializing agents...')

        # Initialize CrewAI
        from resume_optimiser.crew import ResumeCrew
        crew_instance = ResumeCrew()
        crew_instance.setup(job_url, company_name)

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 25, 'status': 'Analyzing job requirements...'}
        )

        # Run optimization
        result = crew_instance.crew().kickoff(inputs={
            "job_url": job_url,
            "company_name": company_name
        })

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 75, 'status': 'Generating optimized resume...'}
        )

        # Process results
        output_files = process_output_files(job_id, result)

        # Update job status
        update_job_status(
            job_id,
            'completed',
            'Optimization completed successfully',
            result={'output_files': output_files}
        )

        return {'status': 'completed', 'result': output_files}

    except Exception as exc:
        # Update job status with error
        update_job_status(job_id, 'failed', f'Optimization failed: {str(exc)}')
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start"""
    logging.info(f"Starting task {task.name} with ID {task_id}")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log task completion"""
    logging.info(f"Completed task {task.name} with ID {task_id}, state: {state}")
```

### Phase 4: Monitoring & Observability

#### 4.1 Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: "kubernetes-pods"
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)

  - job_name: "resume-optimizer-api"
    static_configs:
      - targets: ["resume-optimizer-api-service:8000"]
    metrics_path: /metrics
    scrape_interval: 10s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093
```

#### 4.2 Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Resume Optimizer - Production Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      },
      {
        "title": "Active Jobs",
        "type": "graph",
        "targets": [
          {
            "expr": "active_jobs",
            "legendFormat": "Active Jobs"
          }
        ]
      }
    ]
  }
}
```

### Phase 5: CI/CD Pipeline

#### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-west-2
  ECR_REPOSITORY: resume-optimizer
  EKS_CLUSTER: resume-optimizer-cluster

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/ --cov=src/ --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/resume-optimizer-api \
            resume-optimizer-api=$ECR_REGISTRY/$ECR_REPOSITORY:${{ github.sha }} \
            --namespace=resume-optimizer
          kubectl rollout status deployment/resume-optimizer-api --namespace=resume-optimizer
```

### Phase 6: Security Hardening

#### 6.1 Security Policies

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: resume-optimizer-network-policy
  namespace: resume-optimizer
spec:
  podSelector:
    matchLabels:
      app: resume-optimizer-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - namespaceSelector:
            matchLabels:
              name: redis
      ports:
        - protocol: TCP
          port: 6379
```

#### 6.2 Pod Security Policy

```yaml
# k8s/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: resume-optimizer-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - "configMap"
    - "emptyDir"
    - "projected"
    - "secret"
    - "downwardAPI"
    - "persistentVolumeClaim"
  runAsUser:
    rule: "MustRunAsNonRoot"
  seLinux:
    rule: "RunAsAny"
  fsGroup:
    rule: "RunAsAny"
```

### Deployment Commands

```bash
# 1. Deploy infrastructure
terraform init
terraform plan
terraform apply

# 2. Deploy database
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# 4. Deploy monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# 5. Verify deployment
kubectl get pods -n resume-optimizer
kubectl get services -n resume-optimizer
kubectl get ingress -n resume-optimizer

# 6. Check logs
kubectl logs -f deployment/resume-optimizer-api -n resume-optimizer

# 7. Scale deployment
kubectl scale deployment resume-optimizer-api --replicas=5 -n resume-optimizer
```

This production deployment guide provides a comprehensive roadmap for taking your Resume Optimizer to enterprise scale!
