# Cloud Deployment Quick Reference

## 🚀 Quick Start

### Using the Deployment Script (Recommended)
```bash
# Full deployment
./deploy.sh

# Check status
./deploy.sh status

# View logs
./deploy.sh logs backend

# Restart services
./deploy.sh restart

# Backup database only
./deploy.sh backup
```

### Manual Deployment
```bash
# Configure environment
cp .env.prod.example .env.prod
# Edit .env.prod with your values

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

## 📋 Pre-Deployment Checklist

- [ ] Copy `.env.prod.example` to `.env.prod`
- [ ] Fill in all environment variables in `.env.prod`
- [ ] Generate strong `SECRET_KEY` for Django
- [ ] Set strong database password
- [ ] Configure WhatsApp/Meta credentials
- [ ] Configure email settings
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Configure `CORS_ALLOWED_ORIGINS`
- [ ] Ensure `.env.prod` is in `.gitignore`

## 🏗️ Infrastructure Setup (AWS)

### Using Terraform
```bash
cd terraform/aws

# Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars

# Set database password
export TF_VAR_db_password="your_secure_password"

# Initialize
terraform init

# Preview changes
terraform plan

# Create infrastructure
terraform apply
```

## 🔐 GitHub Secrets (for CI/CD)

Configure in GitHub Repository Settings → Secrets:

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

## 📊 Monitoring Commands

```bash
# View all container status
docker-compose -f docker-compose.prod.yml ps

# View logs for all services
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f celery_io_worker

# Check health
docker-compose -f docker-compose.prod.yml exec backend python manage.py check

# Database shell
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell

# Django shell
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell
```

## 🆘 Emergency Commands

### Restart a specific service
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### View resource usage
```bash
docker stats
```

### Clean up stopped containers
```bash
docker system prune -f
```

### Backup database manually
```bash
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DB_USER $DB_NAME > backup.sql
gzip backup.sql
```

### Restore database
```bash
gunzip backup.sql.gz
docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER $DB_NAME < backup.sql
```

### Roll back deployment
```bash
# Stop current containers
docker-compose -f docker-compose.prod.yml down

# Pull previous version (replace with your tag)
export IMAGE_TAG=previous-tag
docker-compose -f docker-compose.prod.yml pull

# Start containers
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Documentation Links

- **Comprehensive Guide**: [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)
- **Terraform Guide**: [terraform/aws/README.md](terraform/aws/README.md)
- **Implementation Summary**: [CLOUD_IMPLEMENTATION_SUMMARY.md](CLOUD_IMPLEMENTATION_SUMMARY.md)
- **Security Guide**: [SECURITY.md](SECURITY.md)
- **Main README**: [README.md](README.md)

## 🔧 Common Issues

### Issue: Container won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check if environment variables are set
docker-compose -f docker-compose.prod.yml exec backend env
```

### Issue: Database connection error
```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Test connection
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

### Issue: Static files not loading
```bash
# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### Issue: Celery tasks not running
```bash
# Check Celery worker
docker-compose -f docker-compose.prod.yml logs celery_io_worker

# Restart Celery worker
docker-compose -f docker-compose.prod.yml restart celery_io_worker celery_beat
```

## 💰 Cost Estimates

### Development/Staging (AWS)
- **Monthly**: ~$55
- **Components**: Minimal instance sizes

### Production (AWS)
- **Monthly**: ~$151
- **Components**: Recommended instance sizes with high availability

*See CLOUD_DEPLOYMENT.md for detailed cost breakdown*

## 🔒 Security Reminders

- ✅ Never commit `.env.prod` to git
- ✅ Use strong, random passwords
- ✅ Rotate credentials regularly
- ✅ Enable HTTPS/SSL
- ✅ Keep dependencies updated
- ✅ Regular security audits
- ✅ Enable monitoring and alerting
- ✅ Regular backups
- ✅ Test disaster recovery

## 📞 Support

For detailed information, consult the comprehensive guides:
- [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) - Full deployment guide
- [CLOUD_IMPLEMENTATION_SUMMARY.md](CLOUD_IMPLEMENTATION_SUMMARY.md) - What was implemented

---

**Last Updated**: December 17, 2024  
**Quick Reference Version**: 1.0
