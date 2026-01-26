# VIMS Backend - Vehicle Inspection Management System

**Production-Ready Django Backend optimized for 100,000+ concurrent users**

## 🚀 Features

- ✅ **Scalable Architecture**: Load balanced with Nginx, horizontal scaling ready
- ✅ **High Performance**: Redis caching, connection pooling, read replicas support
- ✅ **Async Processing**: Celery for background tasks (photo processing, reports, attention scores)
- ✅ **Role-Based Access Control**: 10 roles with hierarchical scope filtering
- ✅ **Security**: JWT authentication, MFA support, audit logging
- ✅ **Data Integrity**: Read-only machine test data, geofence validation
- ✅ **Monitoring**: Prometheus metrics, health checks for Kubernetes
- ✅ **API Documentation**: OpenAPI/Swagger integration ready

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Installation](#installation)
4. [Running the Application](#running-the-application)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Deployment](#deployment)
8. [Performance Optimization](#performance-optimization)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional but recommended)

### Local Development Setup

```bash
# 1. Clone and navigate to project
cd C:\Users\tayey\360ground\VIMS\vims-backend

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
copy .env.example .env
# Edit .env with your database credentials

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Load initial data (roles, permissions)
python manage.py loaddata fixtures/roles.json
python manage.py loaddata fixtures/initial_data.json

# 8. Run development server
python manage.py runserver 0.0.0.0:8000
```

### Docker Quick Start (Recommended)

```bash
# 1. Start all services
docker-compose up -d

# 2. Run migrations
docker-compose exec web1 python manage.py migrate

# 3. Create superuser
docker-compose exec web1 python manage.py createsuperuser

# 4. Access application
# API: http://localhost/api/
# Admin: http://localhost/admin/
# Health: http://localhost/health/
```

---

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   Nginx LB      │  (Load Balancer + Static Files)
│   Port 80/443   │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───▼───┐  ┌────────┐  ┌────────┐
│ Web1  │  │  Web2  │  │  Web3  │  (Django Apps)
│ :8000 │  │ :8000  │  │ :8000  │
└───┬───┘  └───┬────┘  └───┬────┘
    │          │           │
    └──────────┼───────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────────┐   ┌────────▼──────┐
│ PostgreSQL │   │  Redis Cache  │
│  :5432     │   │  :6379        │
└────────────┘   └───────────────┘
                         │
                 ┌───────┴──────┐
                 │              │
            ┌────▼────┐  ┌──────▼──────┐
            │ Celery  │  │Celery Beat  │
            │ Worker  │  │ (Scheduler) │
            └─────────┘  └─────────────┘
```

### Components

1. **Nginx**: Reverse proxy, load balancer, serves static files
2. **Django (3 instances)**: API application servers
3. **PostgreSQL**: Primary database (with read replica support)
4. **Redis**: Cache + Celery broker/backend
5. **Celery Worker**: Background task processing
6. **Celery Beat**: Periodic task scheduler

---

## 💾 Installation

### System Requirements

**Minimum** (Development):
- 4 GB RAM
- 2 CPU cores
- 20 GB disk space

**Recommended** (Production - 100K users):
- 64 GB RAM (Database)
- 32 vCPU (16 for app, 16 for DB)
- 500 GB SSD
- Load balancer (ALB/NLB)

### Database Setup

```sql
-- Create database and user
CREATE DATABASE vims_db;
CREATE USER vims_user WITH PASSWORD 'vims_password';
ALTER ROLE vims_user SET client_encoding TO 'utf8';
ALTER ROLE vims_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE vims_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE vims_db TO vims_user;

-- Enable required extensions
\c vims_db
CREATE EXTENSION IF NOT EXISTS postgis;  -- For geofencing
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy search
```

### Redis Setup

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install redis-server

# Configure Redis for production
sudo nano /etc/redis/redis.conf
# Set: maxmemory 2gb
# Set: maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis
```

---

## 🚀 Running the Application

### Development Mode

```bash
# Terminal 1: Django dev server
python manage.py runserver

# Terminal 2: Celery worker
celery -A vims worker -l info

# Terminal 3: Celery beat
celery -A vims beat -l info
```

### Production Mode (Docker)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart web1

# Scale web servers
docker-compose up -d --scale web1=5
```

### Production Mode (Manual)

```bash
# Start Gunicorn
gunicorn vims.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 4 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

# Start Celery worker
celery -A vims worker \
    -l info \
    --concurrency=8 \
    --max-tasks-per-child=1000

# Start Celery beat
celery -A vims beat -l info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 📡 API Endpoints

### Authentication

```http
POST /api/auth/login/
POST /api/auth/token/
POST /api/auth/token/refresh/
POST /api/auth/token/verify/
```

### Users

```http
GET    /api/users/              # List users (scope-filtered)
POST   /api/users/              # Create user
GET    /api/users/{id}/         # Get user details
PUT    /api/users/{id}/         # Update user
DELETE /api/users/{id}/         # Delete user
POST   /api/users/{id}/change_password/
POST   /api/users/{id}/assign_role/
```

### Inspections

```http
GET    /api/inspections/        # List inspections (paginated)
POST   /api/inspections/        # Create inspection
GET    /api/inspections/{id}/   # Get inspection details
PUT    /api/inspections/{id}/   # Update inspection
GET    /api/inspections/{id}/machine_tests/
GET    /api/inspections/{id}/photos/
POST   /api/inspections/{id}/validate_geofence/
```

### Centers

```http
GET    /api/centers/            # List centers (scope-filtered)
POST   /api/centers/            # Create center
GET    /api/centers/{id}/       # Get center details
PUT    /api/centers/{id}/       # Update center
GET    /api/centers/{id}/attention_score/
GET    /api/centers/{id}/devices/
POST   /api/centers/{id}/configure_geofence/
```

### Reports

```http
GET    /api/reports/dashboard/            # Dashboard metrics
GET    /api/reports/scorecard/            # Executive scorecard
GET    /api/reports/trends/               # Trend analysis
GET    /api/reports/operational/          # Operational reports
GET    /api/reports/evidence_completeness/
GET    /api/reports/compliance/           # Compliance reports
POST   /api/reports/generate/             # Generate custom report (async)
```

### Health & Monitoring

```http
GET    /health/                 # Basic health check
GET    /health/ready/           # Readiness check (K8s)
GET    /health/live/            # Liveness check (K8s)
GET    /metrics/                # Prometheus metrics
```

---

## 🗄️ Database Schema

### Core Tables

```
users                    # User accounts
roles                    # Role definitions
role_assignments         # User role assignments with scope
delegation_policies      # Role assignment permissions

inspections              # Vehicle inspections
machine_tests            # Automated test results (READ-ONLY)
visual_checklist_items   # 30-point checklist results
inspection_photos        # Evidence photos with GPS
inspection_videos        # Evidence videos

centers                  # Inspection centers
center_devices           # Registered machines
center_cameras           # Camera registry
center_geofences         # Geofence boundaries

admin_units              # Hierarchical governance structure
institutions             # Government/private institutions

audit_logs               # Complete audit trail
fraud_alerts             # Fraud detection alerts
```

### Indexes (Optimized for Performance)

```sql
-- Key indexes for fast queries
CREATE INDEX idx_inspections_center_date ON inspections(center_id, created_at);
CREATE INDEX idx_inspections_plate ON inspections(plate_number);
CREATE INDEX idx_inspections_status ON inspections(status, created_at);
CREATE INDEX idx_users_scope ON role_assignments(scope_type, scope_ids);
CREATE INDEX idx_centers_attention ON centers(attention_score DESC);
```

---

## 🌐 Deployment

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vims-backend
spec:
  replicas: 10
  selector:
    matchLabels:
      app: vims-backend
  template:
    metadata:
      labels:
        app: vims-backend
    spec:
      containers:
      - name: django
        image: your-registry/vims-backend:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: vims-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health/live/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vims-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vims-backend
  minReplicas: 10
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### AWS/Cloud Deployment Checklist

- [ ] Set up RDS PostgreSQL (Multi-AZ) with read replicas
- [ ] Set up ElastiCache Redis cluster
- [ ] Configure Application Load Balancer (ALB)
- [ ] Set up S3 bucket for media files
- [ ] Configure CloudFront CDN for static assets
- [ ] Set up Auto Scaling Groups (min: 10, max: 50 instances)
- [ ] Configure CloudWatch alarms and dashboards
- [ ] Set up VPC with private subnets for DB
- [ ] Configure Security Groups (DB: port 5432, Redis: 6379, App: 8000)
- [ ] Enable RDS automated backups
- [ ] Set up SSL certificates (ACM)
- [ ] Configure Route53 for DNS

---

## ⚡ Performance Optimization

### 1. Database Optimization

```python
# Use select_related for foreign keys
inspections = Inspection.objects.select_related('center', 'inspector')

# Use prefetch_related for many-to-many
inspections = Inspection.objects.prefetch_related('machine_tests', 'photos')

# Only fetch needed fields
inspections = Inspection.objects.only('id', 'plate_number', 'status')

# Bulk operations
Inspection.objects.bulk_create(inspections_list)
Inspection.objects.bulk_update(inspections_list, ['status'])
```

### 2. Caching Strategy

```python
from django.core.cache import cache

# Cache dashboard metrics (5 min)
cache_key = f'dashboard_metrics:{user.id}'
metrics = cache.get(cache_key)
if not metrics:
    metrics = calculate_metrics()
    cache.set(cache_key, metrics, timeout=300)

# Cache role assignments (1 hour)
roles = cache.get('roles_list')
if not roles:
    roles = Role.objects.filter(enabled=True).values()
    cache.set('roles_list', list(roles), timeout=3600)
```

### 3. Celery Tasks

```python
# Use for expensive operations
@shared_task
def process_inspection_photos(inspection_id):
    # Process photos in background
    pass

@shared_task
def generate_daily_report():
    # Generate reports without blocking API
    pass
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Specific app
pytest apps/users/tests/

# Run linting
flake8 apps/
black apps/ --check
mypy apps/
```

### Load Testing

```bash
# Install Locust
pip install locust

# Run load test
locust -f locustfile.py --users 100000 --spawn-rate 1000 --host http://localhost

# Access web UI: http://localhost:8089
```

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps db

# Connect to database
docker-compose exec db psql -U vims_user -d vims_db

# Check migrations
python manage.py showmigrations
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Celery Tasks Not Running

```bash
# Check worker logs
docker-compose logs celery_worker

# Purge queue
celery -A vims purge

# Inspect active tasks
celery -A vims inspect active
```

### Performance Issues

```bash
# Check database query count
DEBUG=True python manage.py runserver
# Use Django Debug Toolbar

# Profile slow queries
python manage.py dbshell
# Run: EXPLAIN ANALYZE SELECT ...

# Check Redis memory
redis-cli INFO memory
```

---

## 📚 Additional Documentation

- [API Documentation](docs/API.md)
- [Database Schema](docs/DATABASE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security Guide](docs/SECURITY.md)
- [Development Guide](docs/DEVELOPMENT.md)

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test
3. Run linting: `black . && flake8`
4. Commit: `git commit -m "Add new feature"`
5. Push: `git push origin feature/new-feature`
6. Create Pull Request

---

## 📞 Support

For issues and questions:
- **Email**: support@vims.gov.et
- **Documentation**: https://docs.vims.gov.et
- **GitHub Issues**: https://github.com/vims/backend/issues

---

## 📝 License

Copyright © 2025 VIMS. All rights reserved.

---

**Built with ❤️ for Ethiopian Vehicle Inspection Management**

#   A p p s   s t r u c t u r e   c r e a t e d 
 
 



