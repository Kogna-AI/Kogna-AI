# CI/CD Pipeline Setup Guide

This guide will help you set up and configure the CI/CD pipeline for the Kogna-AI project using GitHub Actions and AWS ECS.

## Overview

The CI/CD pipeline consists of three main workflows:

1. **Frontend CI** - Linting, formatting, and building the Next.js frontend
2. **Backend CI** - Linting, testing, and building the FastAPI backend
3. **AWS ECS Deployment** - Building Docker images and deploying to AWS ECS

## Prerequisites

Before you can use the CI/CD pipeline, you need to:

### 1. GitHub Secrets Configuration

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

#### Frontend Secrets
- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anonymous key
- `NEXT_PUBLIC_API_URL` - Your backend API URL (e.g., https://api.kogna.ai)

#### Backend Secrets
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service role key
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic (Claude) API key (if using)
- `GOOGLE_API_KEY` - Google API key (if using)
- `SERP_API_KEY` - SerpAPI key (if using)

#### AWS Deployment Secrets
- `AWS_ACCESS_KEY_ID` - AWS access key with ECR and ECS permissions
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key

### 2. AWS Infrastructure Setup

You need to set up the following AWS resources before deploying:

#### 2.1 Create ECR Repositories

```bash
# Create ECR repository for backend
aws ecr create-repository \
    --repository-name kogna-backend \
    --region us-east-1

# Create ECR repository for frontend
aws ecr create-repository \
    --repository-name kogna-frontend \
    --region us-east-1
```

#### 2.2 Create ECS Cluster

```bash
aws ecs create-cluster \
    --cluster-name kogna-cluster \
    --region us-east-1
```

#### 2.3 Create Task Definitions

**Backend Task Definition** (`backend-task-definition.json`):

```json
{
  "family": "kogna-backend-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "kogna-backend",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/kogna-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "SUPABASE_URL", "value": "YOUR_SUPABASE_URL"},
        {"name": "DATABASE_URL", "value": "YOUR_DATABASE_URL"}
      ],
      "secrets": [
        {
          "name": "SUPABASE_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:kogna/supabase-key"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:kogna/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/kogna-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Frontend Task Definition** (`frontend-task-definition.json`):

```json
{
  "family": "kogna-frontend-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "kogna-frontend",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/kogna-frontend:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NEXT_PUBLIC_SUPABASE_URL", "value": "YOUR_SUPABASE_URL"},
        {"name": "NEXT_PUBLIC_SUPABASE_ANON_KEY", "value": "YOUR_ANON_KEY"},
        {"name": "NEXT_PUBLIC_API_URL", "value": "https://api.kogna.ai"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/kogna-frontend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task definitions:

```bash
aws ecs register-task-definition \
    --cli-input-json file://backend-task-definition.json

aws ecs register-task-definition \
    --cli-input-json file://frontend-task-definition.json
```

#### 2.4 Create ECS Services

**Backend Service:**

```bash
aws ecs create-service \
    --cluster kogna-cluster \
    --service-name kogna-backend-service \
    --task-definition kogna-backend-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID:targetgroup/kogna-backend-tg/xxxxx,containerName=kogna-backend,containerPort=8000"
```

**Frontend Service:**

```bash
aws ecs create-service \
    --cluster kogna-cluster \
    --service-name kogna-frontend-service \
    --task-definition kogna-frontend-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID:targetgroup/kogna-frontend-tg/xxxxx,containerName=kogna-frontend,containerPort=3000"
```

#### 2.5 Create Application Load Balancer (Optional but Recommended)

Set up an ALB with target groups for both frontend and backend services to expose them to the internet.

### 3. IAM Permissions

Create an IAM user or role with the following permissions for GitHub Actions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole"
    }
  ]
}
```

## Local Development

### Running with Docker Compose

```bash
# Create a .env file in the root directory with your environment variables
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Running without Docker

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Backend:**
```bash
cd Backend
pip install -r requirements.txt
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

## CI/CD Workflows

### 1. Frontend CI Workflow

**Trigger:** Push or PR to `main` or `develop` branches affecting frontend files

**Steps:**
1. Checkout code
2. Setup Node.js 20
3. Install dependencies
4. Run Biome linting
5. Run Biome formatting check
6. Build Next.js application
7. Upload build artifacts

**Location:** `.github/workflows/frontend-ci.yml`

### 2. Backend CI Workflow

**Trigger:** Push or PR to `main` or `develop` branches affecting backend files

**Steps:**
1. Checkout code
2. Setup Python 3.11
3. Install dependencies
4. Run Black formatting check
5. Run isort import sorting check
6. Run Flake8 linting
7. Run pytest tests
8. Build Docker image
9. Upload Docker image artifact (on main branch only)

**Location:** `.github/workflows/backend-ci.yml`

### 3. AWS ECS Deployment Workflow

**Trigger:** Push to `main` branch or manual workflow dispatch

**Steps:**
1. Build and push backend Docker image to ECR
2. Build and push frontend Docker image to ECR
3. Deploy backend to ECS
4. Deploy frontend to ECS
5. Notify deployment status

**Location:** `.github/workflows/deploy-aws-ecs.yml`

## Testing the Pipeline

### 1. Test Frontend CI

```bash
git checkout -b test-frontend-ci
# Make a change to a frontend file
echo "// test" >> frontend/src/app/page.tsx
git add frontend/src/app/page.tsx
git commit -m "test: frontend CI"
git push origin test-frontend-ci
# Create a PR and check the CI status
```

### 2. Test Backend CI

```bash
git checkout -b test-backend-ci
# Make a change to a backend file
echo "# test" >> Backend/api.py
git add Backend/api.py
git commit -m "test: backend CI"
git push origin test-backend-ci
# Create a PR and check the CI status
```

### 3. Test Deployment

```bash
# Merge your PR to main
git checkout main
git pull origin main
# The deployment workflow will automatically trigger
```

## Monitoring and Debugging

### View Workflow Runs

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Select the workflow you want to monitor
4. Click on a specific run to see detailed logs

### View ECS Deployment Status

```bash
# Check service status
aws ecs describe-services \
    --cluster kogna-cluster \
    --services kogna-backend-service kogna-frontend-service

# View task logs
aws logs tail /ecs/kogna-backend --follow
aws logs tail /ecs/kogna-frontend --follow
```

### Common Issues

#### 1. Build Failures

- Check that all required secrets are set in GitHub
- Verify that dependencies are correctly specified in package.json/requirements.txt
- Check the build logs for specific error messages

#### 2. Deployment Failures

- Verify AWS credentials are correct and have proper permissions
- Check that ECS cluster, services, and task definitions exist
- Verify that ECR repositories exist
- Check CloudWatch logs for container errors

#### 3. Test Failures

- Run tests locally first: `pytest -v` (backend)
- Check that test environment variables are set
- Review test logs in the GitHub Actions output

## Environment-Specific Deployments

To deploy to different environments (staging, production):

1. Update the workflow file to use environment-specific configurations
2. Create separate ECS services and task definitions for each environment
3. Use GitHub Environments to manage environment-specific secrets

## Rollback Procedure

If a deployment fails or introduces issues:

```bash
# List recent task definitions
aws ecs list-task-definitions --family-prefix kogna-backend --sort DESC

# Update service to use previous task definition
aws ecs update-service \
    --cluster kogna-cluster \
    --service kogna-backend-service \
    --task-definition kogna-backend-task:PREVIOUS_REVISION
```

## Best Practices

1. **Always test locally** before pushing to GitHub
2. **Use feature branches** and create PRs for code review
3. **Monitor CI/CD runs** to catch issues early
4. **Keep secrets secure** - never commit them to the repository
5. **Review deployment logs** after each deployment
6. **Set up alerts** for deployment failures
7. **Maintain separate environments** for development, staging, and production
8. **Tag releases** for easier rollback and tracking

## Next Steps

1. Set up test suites (currently minimal testing exists)
2. Configure monitoring and alerting (CloudWatch, DataDog, etc.)
3. Implement blue-green deployments for zero-downtime updates
4. Set up automated database migrations
5. Configure auto-scaling policies for ECS services
6. Implement security scanning in the pipeline
7. Add performance testing to the CI pipeline

## Support

For issues with the CI/CD pipeline, please:
1. Check the GitHub Actions logs
2. Review CloudWatch logs for ECS tasks
3. Consult the AWS ECS documentation
4. Contact the DevOps team

---

Last updated: 2025-01-22
