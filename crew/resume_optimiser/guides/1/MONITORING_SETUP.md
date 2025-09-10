# Monitoring & Observability Setup

## Enterprise-Grade Monitoring for Resume Optimizer

### Overview

This guide sets up comprehensive monitoring, logging, and observability for the Resume Optimizer application using industry-standard tools and practices.

## Architecture

```mermaid
graph TB
    A[Application] --> B[Prometheus]
    A --> C[Grafana]
    A --> D[ELK Stack]
    A --> E[Jaeger]
    A --> F[AlertManager]

    B --> G[Time Series DB]
    C --> B
    D --> H[Elasticsearch]
    E --> I[Distributed Tracing]
    F --> J[Slack/Email/PagerDuty]

    K[Kubernetes] --> A
    L[Load Balancer] --> A
```

## 1. Metrics Collection (Prometheus)

### 1.1 Application Metrics

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
import time
from functools import wraps

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
ACTIVE_JOBS = Gauge(
    'active_jobs_total',
    'Number of active optimization jobs',
    ['status']
)

COMPLETED_JOBS = Counter(
    'completed_jobs_total',
    'Total completed jobs',
    ['status']
)

# Performance metrics
LLM_REQUEST_DURATION = Histogram(
    'llm_request_duration_seconds',
    'LLM API request duration',
    ['provider', 'model']
)

LLM_TOKEN_USAGE = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['provider', 'model', 'type']
)

# Resource metrics
MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['type']
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

# Custom metrics
RESUME_PROCESSING_TIME = Summary(
    'resume_processing_seconds',
    'Time spent processing resumes'
)

FILE_UPLOAD_SIZE = Histogram(
    'file_upload_size_bytes',
    'Size of uploaded files',
    buckets=[1024, 10240, 102400, 1048576, 10485760]  # 1KB to 10MB
)

# Decorator for automatic metrics collection
def track_metrics(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(
                method=kwargs.get('method', 'UNKNOWN'),
                endpoint=kwargs.get('endpoint', 'UNKNOWN'),
                status_code=200
            ).inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(
                method=kwargs.get('method', 'UNKNOWN'),
                endpoint=kwargs.get('endpoint', 'UNKNOWN'),
                status_code=500
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=kwargs.get('method', 'UNKNOWN'),
                endpoint=kwargs.get('endpoint', 'UNKNOWN')
            ).observe(duration)
    return wrapper

# Start metrics server
def start_metrics_server(port=8000):
    start_http_server(port)
```

### 1.2 Database Metrics

```python
# monitoring/database_metrics.py
import asyncpg
from prometheus_client import Gauge, Counter, Histogram
import time

# Database connection metrics
DB_CONNECTIONS_ACTIVE = Gauge(
    'db_connections_active',
    'Active database connections'
)

DB_CONNECTIONS_IDLE = Gauge(
    'db_connections_idle',
    'Idle database connections'
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

DB_QUERY_ERRORS = Counter(
    'db_query_errors_total',
    'Database query errors',
    ['error_type']
)

class DatabaseMetrics:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def update_connection_metrics(self):
        """Update connection pool metrics"""
        DB_CONNECTIONS_ACTIVE.set(self.pool.get_size())
        DB_CONNECTIONS_IDLE.set(self.pool.get_idle_size())

    def track_query(self, query_type: str):
        """Decorator to track database queries"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    DB_QUERY_DURATION.labels(query_type=query_type).observe(
                        time.time() - start_time
                    )
                    return result
                except Exception as e:
                    DB_QUERY_ERRORS.labels(error_type=type(e).__name__).inc()
                    raise
            return wrapper
        return decorator
```

### 1.3 Custom Business Metrics

```python
# monitoring/business_metrics.py
from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime, timedelta

# User engagement metrics
USER_LOGINS = Counter(
    'user_logins_total',
    'Total user logins',
    ['method']  # email, oauth, etc.
)

USER_REGISTRATIONS = Counter(
    'user_registrations_total',
    'Total user registrations'
)

# Resume optimization metrics
RESUME_OPTIMIZATIONS = Counter(
    'resume_optimizations_total',
    'Total resume optimizations',
    ['status', 'company_type']
)

OPTIMIZATION_SUCCESS_RATE = Gauge(
    'optimization_success_rate',
    'Resume optimization success rate'
)

# File processing metrics
FILES_PROCESSED = Counter(
    'files_processed_total',
    'Total files processed',
    ['file_type', 'status']
)

FILE_PROCESSING_TIME = Histogram(
    'file_processing_duration_seconds',
    'File processing duration',
    ['file_type']
)

# API usage metrics
API_CALLS = Counter(
    'api_calls_total',
    'Total API calls',
    ['endpoint', 'user_type']
)

API_RATE_LIMIT_HITS = Counter(
    'api_rate_limit_hits_total',
    'API rate limit hits',
    ['endpoint', 'user_id']
)

# Cost tracking
LLM_COST_USD = Counter(
    'llm_cost_usd_total',
    'Total LLM costs in USD',
    ['provider', 'model']
)

STORAGE_COST_USD = Counter(
    'storage_cost_usd_total',
    'Total storage costs in USD',
    ['storage_type']
)

class BusinessMetrics:
    @staticmethod
    def track_resume_optimization(status: str, company_type: str = 'unknown'):
        """Track resume optimization completion"""
        RESUME_OPTIMIZATIONS.labels(
            status=status,
            company_type=company_type
        ).inc()

    @staticmethod
    def track_file_processing(file_type: str, duration: float, status: str):
        """Track file processing metrics"""
        FILES_PROCESSED.labels(
            file_type=file_type,
            status=status
        ).inc()
        FILE_PROCESSING_TIME.labels(file_type=file_type).observe(duration)

    @staticmethod
    def track_llm_cost(provider: str, model: str, cost_usd: float):
        """Track LLM costs"""
        LLM_COST_USD.labels(
            provider=provider,
            model=model
        ).inc(cost_usd)
```

## 2. Logging (ELK Stack)

### 2.1 Structured Logging

```python
# logging/structured_logger.py
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Create console handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def log(self, level: str, message: str, **kwargs):
        """Log structured message"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.upper(),
            'message': message,
            'service': 'resume-optimizer',
            **kwargs
        }

        getattr(self.logger, level.lower())(json.dumps(log_data))

    def info(self, message: str, **kwargs):
        self.log('INFO', message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log('ERROR', message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log('WARNING', message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.log('DEBUG', message, **kwargs)

    def log_exception(self, message: str, exc_info: Exception, **kwargs):
        """Log exception with stack trace"""
        self.error(message,
                  exception=str(exc_info),
                  traceback=traceback.format_exc(),
                  **kwargs)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            try:
                return json.loads(record.msg)
            except json.JSONDecodeError:
                return record.msg
        return record.msg

# Global logger instance
logger = StructuredLogger('resume-optimizer')

# Usage examples
def log_api_request(method: str, endpoint: str, user_id: str, duration: float):
    logger.info("API request completed",
               method=method,
               endpoint=endpoint,
               user_id=user_id,
               duration_seconds=duration)

def log_job_started(job_id: str, user_id: str, job_url: str):
    logger.info("Job started",
               job_id=job_id,
               user_id=user_id,
               job_url=job_url)

def log_job_completed(job_id: str, user_id: str, duration: float, status: str):
    logger.info("Job completed",
               job_id=job_id,
               user_id=user_id,
               duration_seconds=duration,
               status=status)

def log_error(error: Exception, context: Dict[str, Any]):
    logger.log_exception("Application error occurred",
                        error,
                        **context)
```

### 2.2 Log Aggregation Configuration

```yaml
# logging/filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - /var/log/containers/*resume-optimizer*.log
    processors:
      - add_kubernetes_metadata:
          host: ${NODE_NAME}
          matchers:
            - logs_path:
                logs_path: "/var/log/containers/"
      - decode_json_fields:
          fields: ["message"]
          target: "json"
          overwrite_keys: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "resume-optimizer-%{+yyyy.MM.dd}"

processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
```

### 2.3 Elasticsearch Index Templates

```json
{
  "index_patterns": ["resume-optimizer-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "resume-optimizer-policy",
      "index.lifecycle.rollover_alias": "resume-optimizer"
    },
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date"
        },
        "level": {
          "type": "keyword"
        },
        "message": {
          "type": "text",
          "analyzer": "standard"
        },
        "service": {
          "type": "keyword"
        },
        "job_id": {
          "type": "keyword"
        },
        "user_id": {
          "type": "keyword"
        },
        "duration_seconds": {
          "type": "float"
        },
        "status_code": {
          "type": "integer"
        },
        "method": {
          "type": "keyword"
        },
        "endpoint": {
          "type": "keyword"
        }
      }
    }
  }
}
```

## 3. Distributed Tracing (Jaeger)

### 3.1 OpenTelemetry Setup

```python
# tracing/setup.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import os

def setup_tracing():
    """Setup OpenTelemetry tracing"""

    # Create resource
    resource = Resource.create({
        "service.name": "resume-optimizer",
        "service.version": "2.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "production")
    })

    # Create tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)

    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
    )

    # Create span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    return tracer

# Instrument FastAPI
def instrument_fastapi(app):
    FastAPIInstrumentor.instrument_app(app)
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()

# Custom tracing decorators
def trace_function(operation_name: str):
    """Decorator to trace function execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(operation_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    raise
        return wrapper
    return decorator
```

### 3.2 Custom Spans

```python
# tracing/custom_spans.py
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

class ResumeOptimizationTracer:
    @staticmethod
    def trace_job_processing(job_id: str, job_url: str):
        """Trace resume optimization job processing"""
        with tracer.start_as_current_span("resume_optimization_job") as span:
            span.set_attribute("job.id", job_id)
            span.set_attribute("job.url", job_url)
            span.set_attribute("operation.type", "resume_optimization")
            return span

    @staticmethod
    def trace_llm_call(provider: str, model: str, prompt_tokens: int):
        """Trace LLM API calls"""
        with tracer.start_as_current_span("llm_api_call") as span:
            span.set_attribute("llm.provider", provider)
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.prompt_tokens", prompt_tokens)
            return span

    @staticmethod
    def trace_file_processing(file_type: str, file_size: int):
        """Trace file processing operations"""
        with tracer.start_as_current_span("file_processing") as span:
            span.set_attribute("file.type", file_type)
            span.set_attribute("file.size_bytes", file_size)
            return span
```

## 4. Alerting (AlertManager)

### 4.1 Alert Rules

```yaml
# monitoring/alert-rules.yml
groups:
  - name: resume-optimizer-alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # High response time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (memory_usage_bytes / 1024 / 1024 / 1024) > 1.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}GB"

      # Job processing failures
      - alert: JobProcessingFailures
        expr: rate(completed_jobs_total{status="failed"}[10m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High job failure rate"
          description: "Job failure rate is {{ $value }} per second"

      # Database connection issues
      - alert: DatabaseConnectionIssues
        expr: db_connections_active == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "No active database connections"
          description: "Database connection pool is empty"

      # LLM API failures
      - alert: LLMAPIFailures
        expr: rate(llm_request_duration_seconds_count{status="error"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "LLM API failures detected"
          description: "LLM API failure rate is {{ $value }} per second"
```

### 4.2 AlertManager Configuration

```yaml
# monitoring/alertmanager.yml
global:
  smtp_smarthost: "smtp.gmail.com:587"
  smtp_from: "alerts@resume-optimizer.com"
  smtp_auth_username: "alerts@resume-optimizer.com"
  smtp_auth_password: "your-app-password"

route:
  group_by: ["alertname", "severity"]
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: "default"
  routes:
    - match:
        severity: critical
      receiver: "critical-alerts"
    - match:
        severity: warning
      receiver: "warning-alerts"

receivers:
  - name: "default"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        channel: "#alerts"
        title: "Resume Optimizer Alert"
        text: "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}"

  - name: "critical-alerts"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        channel: "#critical-alerts"
        title: "🚨 CRITICAL: Resume Optimizer"
        text: "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
    email_configs:
      - to: "oncall@resume-optimizer.com"
        subject: "CRITICAL: Resume Optimizer Alert"
        body: "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"

  - name: "warning-alerts"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        channel: "#warnings"
        title: "⚠️ WARNING: Resume Optimizer"
        text: "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
```

## 5. Grafana Dashboards

### 5.1 Application Dashboard

```json
{
  "dashboard": {
    "title": "Resume Optimizer - Application Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
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
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "99th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "gridPos": { "h": 4, "w": 6, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      },
      {
        "title": "Active Jobs",
        "type": "singlestat",
        "gridPos": { "h": 4, "w": 6, "x": 6, "y": 8 },
        "targets": [
          {
            "expr": "active_jobs_total",
            "legendFormat": "Active Jobs"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 12 },
        "targets": [
          {
            "expr": "memory_usage_bytes / 1024 / 1024 / 1024",
            "legendFormat": "Memory Usage (GB)"
          }
        ]
      },
      {
        "title": "CPU Usage",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 12 },
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU Usage %"
          }
        ]
      }
    ]
  }
}
```

### 5.2 Business Metrics Dashboard

```json
{
  "dashboard": {
    "title": "Resume Optimizer - Business Metrics",
    "panels": [
      {
        "title": "Resume Optimizations",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "rate(resume_optimizations_total[1h])",
            "legendFormat": "{{status}} - {{company_type}}"
          }
        ]
      },
      {
        "title": "Success Rate",
        "type": "singlestat",
        "gridPos": { "h": 4, "w": 6, "x": 12, "y": 0 },
        "targets": [
          {
            "expr": "rate(resume_optimizations_total{status=\"success\"}[1h]) / rate(resume_optimizations_total[1h]) * 100",
            "legendFormat": "Success Rate %"
          }
        ]
      },
      {
        "title": "User Registrations",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "rate(user_registrations_total[1h])",
            "legendFormat": "Registrations per hour"
          }
        ]
      },
      {
        "title": "LLM Costs",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
        "targets": [
          {
            "expr": "rate(llm_cost_usd_total[1h])",
            "legendFormat": "{{provider}} - {{model}}"
          }
        ]
      }
    ]
  }
}
```

## 6. Deployment Scripts

### 6.1 Kubernetes Monitoring Stack

```bash
#!/bin/bash
# deploy-monitoring.sh

# Deploy Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123 \
  --set prometheus.prometheusSpec.retention=30d

# Deploy Jaeger
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger \
  --namespace monitoring \
  --set provisionDataStore.cassandra=false \
  --set storage.type=elasticsearch \
  --set storage.elasticsearch.host=elasticsearch.monitoring.svc.cluster.local

# Deploy ELK Stack
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch \
  --namespace monitoring \
  --set replicas=3 \
  --set volumeClaimTemplate.resources.requests.storage=10Gi

helm install kibana elastic/kibana \
  --namespace monitoring \
  --set service.type=LoadBalancer

helm install logstash elastic/logstash \
  --namespace monitoring

# Deploy Filebeat
kubectl apply -f logging/filebeat.yml

echo "Monitoring stack deployed successfully!"
echo "Grafana: http://localhost:3000 (admin/admin123)"
echo "Kibana: http://localhost:5601"
echo "Jaeger: http://localhost:16686"
```

### 6.2 Health Check Script

```bash
#!/bin/bash
# health-check.sh

echo "Checking Resume Optimizer Health..."

# Check API health
API_URL="http://localhost:8000/health"
if curl -f -s $API_URL > /dev/null; then
    echo "✅ API is healthy"
else
    echo "❌ API is unhealthy"
    exit 1
fi

# Check database connectivity
DB_URL="postgresql://user:pass@localhost:5432/resume_optimizer"
if pg_isready -d $DB_URL > /dev/null 2>&1; then
    echo "✅ Database is healthy"
else
    echo "❌ Database is unhealthy"
    exit 1
fi

# Check Redis connectivity
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is unhealthy"
    exit 1
fi

# Check S3 connectivity
if aws s3 ls s3://resume-optimizer-storage > /dev/null 2>&1; then
    echo "✅ S3 is healthy"
else
    echo "❌ S3 is unhealthy"
    exit 1
fi

echo "🎉 All services are healthy!"
```

This comprehensive monitoring setup provides enterprise-grade observability for your Resume Optimizer application!
