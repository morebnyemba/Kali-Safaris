# Kali Safaris WhatsApp CRM

⚠️ **SECURITY NOTICE**: Please read [SECURITY.md](SECURITY.md) before setting up this project. There are important security considerations regarding environment variables and credential management.

This project is a WhatsApp-based Customer Relationship Management (CRM) system designed to manage customer interactions, automate workflows, and integrate with Meta's WhatsApp Business Platform.

## Project Structure

- **whatsappcrm_backend/** - Django backend with REST API
- **whatsapp-crm-frontend/** - React frontend with Vite
- **public-website/** - Public-facing website
- **nginx_proxy/** - Nginx reverse proxy configuration
- **terraform/** - Infrastructure as Code for cloud deployment
- **.github/workflows/** - CI/CD pipeline configuration

## Features

-   **WhatsApp Integration**: Seamless integration with Meta's WhatsApp Business Platform for sending and receiving messages.
-   **Interactive Flows**: Supports Meta's interactive WhatsApp Flows for rich, guided customer experiences (e.g., booking, inquiries, service requests).
-   **Automated Workflows**: Configurable flows to automate responses, collect information, and trigger backend processes.
-   **Customer Data Management**: Stores and manages customer profiles, interaction history, and service-specific data (e.g., site assessments, installations).
-   **Notification System**: Sends automated WhatsApp notifications to customers and internal teams based on events and flow progress.
-   **Catalog Integration**: (Planned) Sync products with Meta's Product Catalog for rich product messaging.
-   **Payment Integration**: (Planned) Integrates with payment gateways for seamless transaction processing.

## Quick Start

### Prerequisites

*   **Python 3.10+**: For running the Django backend
*   **Node.js 18+**: For running the React frontend
*   **Redis**: For caching, message queuing, and WebSocket support
    *   Linux/Mac: Install via package manager (`apt-get install redis-server` or `brew install redis`)
    *   Windows: Use [Memurai](https://memurai.com/) (Redis-compatible)
*   **PostgreSQL** (Production) or **SQLite** (Development)
*   **Git**: For cloning the repository

### Environment Setup

⚠️ **IMPORTANT**: Never commit `.env` files with actual credentials!

1. **Clone the repository**:
   ```bash
   git clone https://github.com/morebnyemba/Kali-Safaris.git
   cd Kali-Safaris
   ```

2. **Set up environment variables**:
   ```bash
   # Backend
   cp whatsappcrm_backend/.env.example whatsappcrm_backend/.env
   
   # Frontend
   cp whatsapp-crm-frontend/.env.example whatsapp-crm-frontend/.env
   
   # Docker (if using)
   cp .env.example .env
   ```

3. **Edit the `.env` files** with your actual credentials (see comments in .env.example files)

## Local Setup (without Docker)

This guide details how to set up and run the Kali Safaris backend locally without Docker, using SQLite for the database and Memurai (a Redis-compatible server for Windows) for caching and message queuing.

### Prerequisites

*   **Python 3.10+**: Ensure Python is installed and added to your PATH.
*   **Git**: For cloning the repository.
*   **Memurai (Windows)**: Download and install Memurai from [Memurai.com](https://memurai.com/). Ensure it's running. This acts as your local Redis server.
*   **virtualenv (recommended)**: For managing project dependencies.

### Backend Setup

1.  **Navigate to backend directory**:
    ```bash
    cd whatsappcrm_backend
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    
    # On Linux/Mac
    source venv/bin/activate
    
    # On Windows
    .\venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment** (if not done in Quick Start):
    ```bash
    cp .env.example .env
    # Edit .env with your actual values
    ```

5.  **Run database migrations**:
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser**:
    ```bash
    python manage.py createsuperuser
    ```

7.  **Load initial notification templates**:
    ```bash
    python manage.py load_notification_templates
    ```

8.  **Start the Django development server**:
    ```bash
    python manage.py runserver
    ```
    Backend will be available at `http://localhost:8000`

9.  **Start Celery worker and beat scheduler** (in separate terminals):
    ```bash
    # Terminal 1: Celery Worker
    celery -A whatsappcrm_backend worker -l info
    
    # Terminal 2: Celery Beat (Scheduler)
    celery -A whatsappcrm_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ```

### Frontend Setup

1.  **Navigate to frontend directory**:
    ```bash
    cd whatsapp-crm-frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Configure environment** (if not done in Quick Start):
    ```bash
    cp .env.example .env
    # Edit .env with your backend URL
    ```

4.  **Start development server**:
    ```bash
    npm run dev
    ```
    Frontend will be available at `http://localhost:5173`

## Docker Setup (Production)

For detailed cloud deployment instructions, see [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md).

1.  **Configure environment variables**:
    ```bash
    cp .env.prod.example .env.prod
    cp whatsappcrm_backend/.env.example whatsappcrm_backend/.env.prod
    # Edit both files with your production values
    ```

2.  **Build and start containers**:
    ```bash
    docker-compose -f docker-compose.prod.yml up -d
    ```
    
    Or use the deployment script:
    ```bash
    ./deploy.sh
    ```

3.  **Run initial setup** (first time only):
    ```bash
    docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
    docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
    docker-compose -f docker-compose.prod.yml exec backend python manage.py load_notification_templates
    docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
    ```

4.  **Access the application**:
    - Backend API: Configure via Nginx Proxy Manager (port 81)
    - Frontend: Configure via Nginx Proxy Manager (port 81)
    - Admin Interface: `https://your-backend-domain/admin/`

## Running the Application

With the Django server, Celery worker, Celery beat, and frontend running, the application is fully operational.

- **Admin Interface**: `http://localhost:8000/admin/`
- **Frontend**: `http://localhost:5173`
- **API Documentation**: `http://localhost:8000/api/schema/swagger-ui/` (if enabled)

### Meta Integration Setup (Critical for WhatsApp Flows)

To fully utilize WhatsApp Flows, you must configure a `MetaAppConfig` in the Django Admin:

1.  Login to `http://localhost:8000/admin/`.
2.  Navigate to `Meta Integration` -> `Meta app configs`.
3.  Click `Add Meta app config` and fill in the details using your Meta App credentials (App ID, App Secret, Business Account ID, Access Token). Ensure `Is Active` is checked.
4.  **Sync WhatsApp Flows**:
    After configuring the `MetaAppConfig`, run the management command to sync the predefined WhatsApp Flows with Meta's platform:
    ```bash
    python manage.py sync_whatsapp_flows --publish
    ```
    This command registers the interactive flows defined in `flows/definitions` with Meta, making them available for use in your WhatsApp conversations.

## WhatsApp Flow Architecture

The `flows` application implements a flexible and extensible system for defining and managing interactive WhatsApp conversation flows.

### Core Concepts

-   **Flow**: A sequence of interactive steps designed to guide a user through a specific process.
-   **FlowStep**: Individual stages within a flow, each with a defined type (e.g., `send_message`, `question`, `action`, `end_flow`, `human_handover`, `switch_flow`). Each step contains a JSON-based configuration (`config`) defining its behavior.
-   **FlowTransition**: Defines how a user moves from one `FlowStep` to another based on conditions (e.g., user input matching a keyword, a variable having a certain value). Transitions can have priorities.
-   **ContactFlowState**: Tracks the current state of a contact within a flow, including the `current_flow`, `current_step`, and `flow_context_data` (a JSONField storing variables specific to the ongoing conversation).
-   **WhatsAppFlow**: Represents a Meta Interactive Flow registered with Meta's platform, linking an internal `Flow` definition to a `flow_id` on the WhatsApp Business Platform.

### Key Components

-   **`flows/services.py`**: Contains the core logic for processing incoming WhatsApp messages, evaluating transition conditions, executing step actions, and managing `ContactFlowState`. Includes dynamic action dispatching and Jinja2 templating for message personalization.
-   **`flows/models.py`**: Defines the data structures for `Flow`, `FlowStep`, `FlowTransition`, `ContactFlowState`, and `WhatsAppFlow`.
-   **`flows/schemas.py`**: Pydantic models for validating the JSON configurations of `FlowStep` (e.g., `StepConfigSendMessage`, `StepConfigQuestion`).
-   **`flows/whatsapp_flow_service.py`**: Handles communication with Meta's API for managing (creating, updating, publishing) interactive flows.
-   **`flows/whatsapp_flow_response_processor.py`**: Processes incoming webhook events from Meta containing responses to interactive flows (Native Flow Messages), updates the `ContactFlowState`, and resumes the flow engine.
-   **`flows/management/commands/sync_whatsapp_flows.py`**: A Django management command to synchronize the locally defined `WhatsAppFlow` instances with Meta's platform.
-   **`flows/definitions/`**: A directory containing Python modules that define various `Flow` configurations and `WhatsAppFlow` JSON structures.

## Meta Integration

The `meta_integration` app handles all communication with Meta's Graph API.

### Key Components

-   **`meta_integration/models.py`**: Defines `MetaAppConfig` to store credentials and configurations for connecting to the WhatsApp Business Platform. Also includes `WhatsAppWebhookEventLog` for logging incoming webhook events.
-   **`meta_integration/utils.py`**: Utility functions for sending messages via the WhatsApp Business Platform API.
-   **`meta_integration/catalog_service.py`**: Manages synchronization of product data with Meta's Product Catalog, ensuring products are correctly listed for use in WhatsApp messages.

## Notifications

The `notifications` app manages sending automated notifications to contacts and internal staff.

### Key Components

-   **`notifications/models.py`**: Defines `NotificationTemplate` for storing reusable message templates.
-   **`notifications/services.py`**: Provides functions for queuing and sending notifications, often used by flow actions.
-   **`flows/management/commands/load_notification_templates.py`**: A management command to load and update predefined notification templates into the database.

## Best Practices

### Security

- **Never commit `.env` files** - Always use `.env.example` as templates
- **Rotate credentials regularly** - Especially after any exposure or team changes
- **Use strong passwords** - Generate random passwords for databases and services
- **Enable HTTPS in production** - Use Let's Encrypt for free SSL certificates
- **Keep dependencies updated** - Regularly update packages to patch security vulnerabilities
- **Review logs regularly** - Monitor for unauthorized access attempts

### Development

- **Use virtual environments** - Isolate project dependencies
- **Run linters before committing** - Use ESLint for frontend, flake8/black for backend
- **Write tests** - Add tests for new features and bug fixes
- **Document changes** - Keep documentation in sync with code changes
- **Use meaningful commit messages** - Follow conventional commit format

### Production

- **Set DEBUG=False** - Never run with DEBUG=True in production
- **Use PostgreSQL** - Don't use SQLite in production
- **Enable Redis password** - Secure Redis if exposed to network
- **Configure proper logging** - Use centralized logging for monitoring
- **Set up backups** - Regular automated backups of database and media files
- **Monitor performance** - Use tools like django-prometheus for metrics

## Troubleshooting

### Backend Issues

**Database connection errors:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection settings in .env
# Verify DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
```

**Celery tasks not running:**
```bash
# Verify Redis is running
redis-cli ping  # Should return PONG

# Check Celery worker logs
celery -A whatsappcrm_backend worker -l debug

# Verify CELERY_BROKER_URL in .env
```

**Migration errors:**
```bash
# Reset migrations (development only!)
python manage.py migrate --fake-initial

# Or create fresh migrations
python manage.py makemigrations
python manage.py migrate
```

### Frontend Issues

**API connection errors:**
```bash
# Verify VITE_API_BASE_URL in whatsapp-crm-frontend/.env
# Check backend is running and accessible
# Check CORS settings in backend settings.py
```

**Build errors:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Docker Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs backend

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Permission errors:**
```bash
# Fix ownership of volumes
sudo chown -R $USER:$USER .

# Or reset volumes (will lose data!)
docker-compose down -v
docker-compose up -d
```

## Cloud Deployment

The project includes comprehensive cloud deployment support:

### CI/CD Pipeline
- **GitHub Actions** workflow for automated testing and deployment
- Automated builds on push to main/develop branches
- Docker image building and publishing
- Automated deployments to staging and production

### Infrastructure as Code
- **Terraform** configurations for AWS deployment
- Automated provisioning of:
  - VPC, subnets, and networking
  - ECS cluster for container orchestration
  - RDS PostgreSQL database
  - ElastiCache Redis
  - Application Load Balancer
  - ECR for Docker images

### Documentation
- [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) - Comprehensive cloud deployment guide
- [terraform/aws/README.md](terraform/aws/README.md) - Terraform usage instructions
- [deploy.sh](deploy.sh) - Production deployment script

### Quick Cloud Deployment
```bash
# Using the deployment script
./deploy.sh

# Or using Terraform (AWS)
cd terraform/aws
terraform init
terraform plan
terraform apply
```

See [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is proprietary. All rights reserved.

## Support

For issues and questions:
- Check existing documentation in this README
- Review [SECURITY.md](SECURITY.md) for security-related concerns
- Contact the development team

---

**Last Updated**: December 2024
