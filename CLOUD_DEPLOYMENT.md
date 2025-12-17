# Cloud Deployment Guide

This guide provides comprehensive instructions for deploying the Kali Safaris WhatsApp CRM to various cloud platforms.

## Table of Contents
- [Prerequisites](#prerequisites)
- [CI/CD Pipeline](#cicd-pipeline)
- [Cloud Platform Options](#cloud-platform-options)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying to the cloud, ensure you have:

1. **Docker Hub Account** (or another container registry)
2. **Cloud Provider Account** (AWS, Azure, GCP, or DigitalOcean)
3. **Domain Name** (for production deployment)
4. **SSL Certificate** (Let's Encrypt recommended)
5. **GitHub Secrets Configured**:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub password or access token
   - Cloud provider credentials (varies by platform)

## CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that automatically:

### On Pull Requests and Pushes to Main/Develop:
- Tests the backend (Python/Django)
- Tests the frontend (React/Vite)
- Runs linting and security checks
- Builds Docker images

### On Push to Develop Branch:
- Deploys to staging environment

### On Push to Main Branch:
- Deploys to production environment

### Setting Up GitHub Actions

1. **Configure Secrets** in your GitHub repository:
   ```
   Settings → Secrets and variables → Actions → New repository secret
   ```

   Required secrets:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
   - Additional secrets based on your cloud provider

2. **Enable GitHub Actions**:
   - The workflow will run automatically on push/PR

3. **Configure Environments**:
   ```
   Settings → Environments → New environment
   ```
   
   Create two environments:
   - `staging`: For develop branch deployments
   - `production`: For main branch deployments (add protection rules)

## Cloud Platform Options

### Option 1: AWS (Amazon Web Services)

#### Using ECS (Elastic Container Service)

1. **Create ECR Repositories**:
   ```bash
   aws ecr create-repository --repository-name kali-safaris-backend
   aws ecr create-repository --repository-name kali-safaris-frontend
   ```

2. **Create ECS Cluster**:
   ```bash
   aws ecs create-cluster --cluster-name kali-safaris-cluster
   ```

3. **Deploy using Docker Compose**:
   - Use AWS ECS CLI or AWS Copilot
   - Configure task definitions
   - Set up load balancer
   - Configure Auto Scaling

4. **Database and Redis**:
   - Use Amazon RDS (PostgreSQL)
   - Use Amazon ElastiCache (Redis)

#### Using EC2 (Virtual Machines)

1. **Launch EC2 Instance**:
   - Ubuntu 22.04 LTS
   - t3.medium or larger
   - Configure security groups (ports 80, 443, 22)

2. **SSH to instance and install Docker**:
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo systemctl enable docker
   sudo usermod -aG docker ubuntu
   ```

3. **Clone repository and deploy**:
   ```bash
   git clone https://github.com/morebnyemba/Kali-Safaris.git
   cd Kali-Safaris
   cp .env.example .env
   # Edit .env with production values
   docker-compose up -d
   ```

### Option 2: DigitalOcean

#### Using App Platform (Managed)

1. **Connect GitHub Repository**:
   - Go to App Platform in DigitalOcean dashboard
   - Connect your GitHub account
   - Select the Kali-Safaris repository

2. **Configure Components**:
   - Backend: `whatsappcrm_backend/Dockerfile`
   - Frontend: `whatsapp-crm-frontend/Dockerfile`
   - Database: Managed PostgreSQL
   - Redis: Managed Redis

3. **Environment Variables**:
   - Configure all environment variables from `.env.example`

4. **Deploy**:
   - Click "Create Resources"
   - App Platform handles building and deployment

#### Using Droplets (VPS)

1. **Create Droplet**:
   - Ubuntu 22.04 LTS
   - 4GB RAM minimum
   - Enable monitoring

2. **Setup Script**:
   ```bash
   #!/bin/bash
   # Run this on your droplet
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo apt install docker-compose -y
   
   # Clone project
   git clone https://github.com/morebnyemba/Kali-Safaris.git
   cd Kali-Safaris
   
   # Setup environment
   cp .env.example .env
   # Edit .env file with your values
   nano .env
   
   # Start services
   docker-compose up -d
   ```

3. **Configure Domain and SSL**:
   - Point your domain to droplet IP
   - Use Nginx Proxy Manager (included in docker-compose.yml)
   - Configure SSL with Let's Encrypt

### Option 3: Azure

#### Using Azure Container Instances (ACI)

1. **Create Resource Group**:
   ```bash
   az group create --name kali-safaris-rg --location eastus
   ```

2. **Create Container Registry**:
   ```bash
   az acr create --resource-group kali-safaris-rg \
     --name kalisafarisacr --sku Basic
   ```

3. **Build and Push Images**:
   ```bash
   az acr build --registry kalisafarisacr \
     --image backend:latest ./whatsappcrm_backend
   az acr build --registry kalisafarisacr \
     --image frontend:latest ./whatsapp-crm-frontend
   ```

4. **Deploy Containers**:
   ```bash
   az container create --resource-group kali-safaris-rg \
     --name kali-safaris-backend \
     --image kalisafarisacr.azurecr.io/backend:latest \
     --cpu 2 --memory 4
   ```

### Option 4: Google Cloud Platform (GCP)

#### Using Cloud Run (Serverless)

1. **Build and Push to GCR**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/backend ./whatsappcrm_backend
   gcloud builds submit --tag gcr.io/PROJECT_ID/frontend ./whatsapp-crm-frontend
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy backend \
     --image gcr.io/PROJECT_ID/backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Setup Cloud SQL (PostgreSQL)**:
   ```bash
   gcloud sql instances create kali-safaris-db \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1
   ```

## Docker Deployment

### Production Docker Compose

Create a `docker-compose.prod.yml` for production:

```yaml
version: '3.8'

services:
  backend:
    image: ${DOCKER_USERNAME}/kali-safaris-backend:latest
    env_file:
      - .env.prod
    restart: always
    depends_on:
      - db
      - redis
    
  frontend:
    image: ${DOCKER_USERNAME}/kali-safaris-frontend:latest
    restart: always
    depends_on:
      - backend
  
  # ... other services
```

### Deployment Commands

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Stop old containers
docker-compose -f docker-compose.prod.yml down

# Start new containers
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

## Environment Configuration

### Critical Environment Variables

**Backend (.env.prod)**:
```bash
# Django
SECRET_KEY=<generate-strong-random-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_SETTINGS_MODULE=whatsappcrm_backend.settings

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/dbname
DB_NAME=production_db
DB_USER=prod_user
DB_PASSWORD=<strong-password>
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=<your-phone-number-id>
WHATSAPP_BUSINESS_ACCOUNT_ID=<your-business-account-id>
WHATSAPP_APP_ID=<your-app-id>
WHATSAPP_APP_SECRET=<your-app-secret>
WHATSAPP_ACCESS_TOKEN=<your-access-token>

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=<email-password>
```

**Frontend (.env.prod)**:
```bash
VITE_API_BASE_URL=https://api.your-domain.com
VITE_WS_URL=wss://api.your-domain.com/ws
```

### Security Best Practices

1. **Never commit .env files**
2. **Use strong, random passwords**
3. **Rotate credentials regularly**
4. **Use environment-specific configurations**
5. **Enable HTTPS/SSL everywhere**
6. **Set up firewall rules**
7. **Enable database backups**
8. **Use secrets management** (AWS Secrets Manager, Azure Key Vault, etc.)

## Monitoring and Logging

### Application Monitoring

1. **Install Sentry** (Error Tracking):
   ```bash
   pip install sentry-sdk
   ```
   
   Add to `settings.py`:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
   ```

2. **Setup Prometheus** (Metrics):
   ```bash
   pip install django-prometheus
   ```

3. **Configure Grafana** (Visualization):
   - Connect to Prometheus
   - Import Django dashboards

### Log Management

1. **Centralized Logging**:
   - CloudWatch (AWS)
   - Azure Monitor (Azure)
   - Cloud Logging (GCP)
   - Papertrail/Loggly (Platform-agnostic)

2. **Docker Logging**:
   ```yaml
   services:
     backend:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

### Health Checks

Add to your Django app:
```python
# urls.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    path('health/', health_check),
]
```

Configure in docker-compose:
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Troubleshooting

### Common Issues

1. **Container Fails to Start**:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **Database Connection Errors**:
   - Check database host and port
   - Verify credentials
   - Ensure database is running
   ```bash
   docker-compose exec backend python manage.py dbshell
   ```

3. **Static Files Not Loading**:
   ```bash
   docker-compose exec backend python manage.py collectstatic --noinput
   ```

4. **Celery Tasks Not Running**:
   ```bash
   docker-compose logs celery_io_worker
   docker-compose restart celery_io_worker
   ```

5. **Memory Issues**:
   - Increase container memory limits
   - Check for memory leaks
   - Monitor with `docker stats`

### Performance Optimization

1. **Database Optimization**:
   - Add indexes to frequently queried fields
   - Use connection pooling
   - Enable query caching

2. **Redis Optimization**:
   - Configure maxmemory policy
   - Use Redis clustering for scale

3. **Application Optimization**:
   - Enable Django caching
   - Use CDN for static files
   - Optimize queries (use select_related, prefetch_related)

## Backup and Disaster Recovery

### Database Backups

**Automated Backup Script**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
gzip $BACKUP_FILE

# Delete backups older than 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

**Cron Job**:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
gunzip backup_20240101_020000.sql.gz
docker-compose exec -T db psql -U $DB_USER $DB_NAME < backup_20240101_020000.sql
```

## Scaling

### Horizontal Scaling

1. **Load Balancer**:
   - AWS: Application Load Balancer
   - Azure: Azure Load Balancer
   - GCP: Cloud Load Balancing
   - DigitalOcean: Load Balancer

2. **Multiple Backend Instances**:
   ```bash
   docker-compose up -d --scale backend=3
   ```

3. **Database Read Replicas**:
   - Setup read replicas for database
   - Configure Django to use read replicas

### Vertical Scaling

- Increase CPU/Memory for containers
- Use larger VM instances
- Optimize database performance

## Cost Optimization

1. **Use reserved instances** (AWS, Azure)
2. **Enable auto-scaling** (scale down during low traffic)
3. **Use spot instances** for non-critical workloads
4. **Optimize image sizes** (multi-stage builds)
5. **Use CDN** for static content
6. **Monitor and eliminate waste**

## Security Checklist

- [ ] SSL/TLS enabled (HTTPS)
- [ ] Firewall configured (only necessary ports open)
- [ ] Strong passwords and secrets
- [ ] Regular security updates
- [ ] Database backups enabled
- [ ] Secrets not in code/git
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Regular vulnerability scans
- [ ] Audit logs enabled
- [ ] IP whitelisting (if applicable)

## Support and Maintenance

### Regular Maintenance Tasks

- **Daily**: Monitor logs and metrics
- **Weekly**: Review security alerts, update dependencies
- **Monthly**: Review costs, optimize performance, test backups
- **Quarterly**: Security audit, disaster recovery testing

### Getting Help

- Check logs: `docker-compose logs -f`
- Review documentation in this repository
- Contact the development team
- Review [SECURITY.md](SECURITY.md) for security issues

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Maintained By**: Development Team

## Quick Reference

### Useful Commands

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Execute command in container
docker-compose exec backend python manage.py migrate

# Update and restart
git pull origin main
docker-compose pull
docker-compose up -d

# Clean up
docker system prune -a
```

### Important URLs

- **Production API**: https://api.your-domain.com
- **Production Frontend**: https://your-domain.com
- **Admin Panel**: https://api.your-domain.com/admin/
- **Nginx Proxy Manager**: https://your-domain.com:81
- **Monitoring Dashboard**: https://monitoring.your-domain.com
