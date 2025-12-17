#!/bin/bash

# Kali Safaris Deployment Script
# This script automates the deployment process for production

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="/backups/postgres"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env.prod exists
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env.prod file not found!"
        log_info "Please create .env.prod from .env.example"
        exit 1
    fi
    log_info ".env.prod file found"
}

# Backup database
backup_database() {
    log_info "Creating database backup..."
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"
    
    # Source environment file to get DB credentials
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "whatsappcrm_db_prod"; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null || {
            log_warn "Database backup failed or database not running"
            return
        }
        gzip "$BACKUP_FILE"
        log_info "Database backed up to $BACKUP_FILE.gz"
    else
        log_warn "Database container not running, skipping backup"
    fi
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    log_info "Images pulled successfully"
}

# Stop containers
stop_containers() {
    log_info "Stopping containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    log_info "Containers stopped"
}

# Start containers
start_containers() {
    log_info "Starting containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    log_info "Containers started"
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python manage.py migrate --no-input
    log_info "Migrations completed"
}

# Collect static files
collect_static() {
    log_info "Collecting static files..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python manage.py collectstatic --no-input
    log_info "Static files collected"
}

# Load notification templates
load_templates() {
    log_info "Loading notification templates..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python manage.py load_notification_templates || true
    log_info "Templates loaded"
}

# Check health
check_health() {
    log_info "Checking container health..."
    sleep 10  # Wait for containers to start
    
    # Check backend health
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "whatsappcrm_backend_prod.*healthy"; then
        log_info "Backend is healthy"
    else
        log_warn "Backend health check pending..."
    fi
    
    # Show running containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
}

# Clean up old images
cleanup() {
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    log_info "Cleanup completed"
}

# Main deployment flow
main() {
    log_info "========================================="
    log_info "Kali Safaris Deployment Script"
    log_info "========================================="
    
    # Check prerequisites
    check_env_file
    
    # Ask for confirmation
    read -p "Do you want to proceed with deployment? (yes/no): " confirmation
    if [ "$confirmation" != "yes" ]; then
        log_warn "Deployment cancelled"
        exit 0
    fi
    
    # Backup existing database
    backup_database
    
    # Pull latest images
    pull_images
    
    # Stop old containers
    stop_containers
    
    # Start new containers
    start_containers
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 15
    
    # Run post-deployment tasks
    run_migrations
    collect_static
    load_templates
    
    # Check health
    check_health
    
    # Cleanup
    cleanup
    
    log_info "========================================="
    log_info "Deployment completed successfully!"
    log_info "========================================="
    log_info "Access your application:"
    log_info "  - Frontend: https://your-domain.com"
    log_info "  - Backend API: https://api.your-domain.com"
    log_info "  - Admin Panel: https://api.your-domain.com/admin/"
    log_info "  - Nginx Proxy Manager: https://your-domain.com:81"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    backup)
        backup_database
        ;;
    pull)
        pull_images
        ;;
    restart)
        stop_containers
        start_containers
        check_health
        ;;
    logs)
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f "${2:-backend}"
        ;;
    status)
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|backup|pull|restart|logs|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  backup  - Backup database only"
        echo "  pull    - Pull latest images only"
        echo "  restart - Restart all containers"
        echo "  logs    - View container logs (optional: specify service name)"
        echo "  status  - Show container status"
        echo "  cleanup - Clean up old Docker images"
        exit 1
        ;;
esac
