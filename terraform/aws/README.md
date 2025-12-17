# Terraform Infrastructure as Code

This directory contains Terraform configurations for deploying Kali Safaris WhatsApp CRM infrastructure on AWS.

## Prerequisites

1. **Terraform installed** (version >= 1.0)
   ```bash
   # macOS
   brew install terraform
   
   # Ubuntu/Debian
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install terraform
   ```

2. **AWS CLI configured**
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Enter your default region
   ```

3. **AWS account with appropriate permissions**

## Quick Start

1. **Navigate to the AWS directory**:
   ```bash
   cd terraform/aws
   ```

2. **Copy and configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Set sensitive variables as environment variables**:
   ```bash
   export TF_VAR_db_password="your_secure_database_password"
   ```

4. **Initialize Terraform**:
   ```bash
   terraform init
   ```

5. **Preview changes**:
   ```bash
   terraform plan
   ```

6. **Apply configuration**:
   ```bash
   terraform apply
   ```

7. **Note the outputs**:
   ```bash
   terraform output
   ```

## Infrastructure Components

The Terraform configuration creates the following AWS resources:

### Networking
- **VPC**: Virtual Private Cloud with custom CIDR block
- **Subnets**: 2 public subnets across different availability zones
- **Internet Gateway**: For public internet access
- **Route Tables**: Routing configuration for subnets

### Compute
- **ECS Cluster**: Container orchestration cluster
- **ECR Repositories**: Docker image repositories for backend and frontend
- **Application Load Balancer**: Distributes traffic to ECS tasks
- **Target Groups**: Health check and routing for backend services

### Database
- **RDS PostgreSQL**: Managed PostgreSQL database
  - Engine version: 15.4
  - Automated backups (7 days retention)
  - Multi-AZ for production
- **ElastiCache Redis**: Managed Redis for caching
  - Engine version: 7.0
  - For Celery broker and application caching

### Security
- **Security Groups**: Firewall rules for each component
- **IAM Roles**: ECS task execution roles with proper permissions

## Configuration Files

- `main.tf`: Main infrastructure definition
- `variables.tf`: Input variable definitions
- `terraform.tfvars.example`: Example variable values
- `terraform.tfvars`: Your actual values (not committed to git)

## Estimated Costs

**Development/Staging** (minimal setup):
- EC2 (t3.micro equivalent for ECS): ~$7/month
- RDS (db.t3.micro): ~$15/month
- ElastiCache (cache.t3.micro): ~$12/month
- ALB: ~$16/month
- Data transfer: ~$5/month
- **Total**: ~$55/month

**Production** (recommended setup):
- EC2 (t3.medium for ECS): ~$30/month
- RDS (db.t3.small, Multi-AZ): ~$60/month
- ElastiCache (cache.t3.small): ~$25/month
- ALB: ~$16/month
- Data transfer: ~$20/month
- **Total**: ~$151/month

*Note: Costs vary based on usage, region, and actual resource consumption.*

## Deploying the Application

After infrastructure is created:

1. **Push Docker images to ECR**:
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and push backend
   docker build -t kalisafaris-backend:latest ./whatsappcrm_backend
   docker tag kalisafaris-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/kalisafaris-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/kalisafaris-backend:latest
   
   # Build and push frontend
   docker build -t kalisafaris-frontend:latest ./whatsapp-crm-frontend
   docker tag kalisafaris-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/kalisafaris-frontend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/kalisafaris-frontend:latest
   ```

2. **Create ECS Task Definitions** (via AWS Console or CLI)

3. **Create ECS Services** (via AWS Console or CLI)

4. **Configure DNS**:
   - Point your domain to the ALB DNS name (from terraform output)

5. **Set up SSL/TLS**:
   - Use AWS Certificate Manager for SSL certificates
   - Attach certificate to ALB HTTPS listener

## State Management

For team collaboration, configure remote state backend:

1. **Create S3 bucket for state**:
   ```bash
   aws s3 mb s3://kalisafaris-terraform-state
   ```

2. **Enable versioning**:
   ```bash
   aws s3api put-bucket-versioning \
     --bucket kalisafaris-terraform-state \
     --versioning-configuration Status=Enabled
   ```

3. **Uncomment backend configuration** in `main.tf`

4. **Initialize with backend**:
   ```bash
   terraform init -migrate-state
   ```

## Updating Infrastructure

1. **Make changes** to `main.tf` or `variables.tf`

2. **Preview changes**:
   ```bash
   terraform plan
   ```

3. **Apply changes**:
   ```bash
   terraform apply
   ```

## Destroying Infrastructure

**WARNING**: This will destroy all resources and data!

```bash
terraform destroy
```

## Security Best Practices

1. **Never commit `terraform.tfvars`** with sensitive data
2. **Use AWS Secrets Manager** for application secrets
3. **Enable MFA** on AWS root account
4. **Use IAM roles** instead of access keys where possible
5. **Enable AWS CloudTrail** for audit logging
6. **Regular security updates** on all components
7. **Restrict security group rules** to minimum required
8. **Enable encryption** for RDS and S3

## Troubleshooting

### Error: Invalid credentials
```bash
aws configure
# Re-enter credentials
```

### Error: Insufficient IAM permissions
Ensure your AWS user has these policies:
- AmazonEC2FullAccess
- AmazonECSFullAccess
- AmazonRDSFullAccess
- AmazonElastiCacheFullAccess
- IAMFullAccess
- AmazonVPCFullAccess

### Error: Resource already exists
```bash
terraform import <resource_type>.<resource_name> <resource_id>
```

### State lock issues
```bash
terraform force-unlock <lock-id>
```

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)

## Support

For issues or questions:
1. Check Terraform plan output
2. Review AWS CloudWatch logs
3. Check this documentation
4. Contact the DevOps team

---

**Last Updated**: December 2024
**Terraform Version**: >= 1.0
**AWS Provider Version**: ~> 5.0
