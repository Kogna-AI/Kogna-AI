# CI/CD Quick Reference

Quick commands and tips for working with the CI/CD pipeline.

## Local Testing

### Test Frontend Locally

```bash
cd frontend
npm install
npm run lint          # Run Biome linting
npm run format        # Auto-format code
npm run build         # Test production build
npm run dev           # Start dev server
```

### Test Backend Locally

```bash
cd Backend
pip install -r requirements.txt
black --check .       # Check formatting
black .              # Auto-format code
isort --check-only . # Check import sorting
isort .              # Sort imports
flake8 .             # Run linting
pytest -v            # Run tests
uvicorn api:app --reload  # Start dev server
```

### Test with Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run specific service
docker-compose up backend
docker-compose up frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Remove volumes
docker-compose down -v
```

### Build Docker Images Locally

```bash
# Build backend
cd Backend
docker build -t kogna-backend:local .

# Build frontend
cd frontend
docker build \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=your-key \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -t kogna-frontend:local .

# Run locally
docker run -p 8000:8000 --env-file ../.env kogna-backend:local
docker run -p 3000:3000 kogna-frontend:local
```

## GitHub Actions

### Trigger Workflows

```bash
# Push to trigger CI
git push origin your-branch

# Manually trigger deployment workflow
gh workflow run deploy-aws-ecs.yml

# Manually trigger with environment
gh workflow run deploy-aws-ecs.yml -f environment=staging
```

### Monitor Workflows

```bash
# List recent workflow runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log

# Watch a running workflow
gh run watch
```

### Cancel Workflows

```bash
# Cancel a running workflow
gh run cancel <run-id>

# Cancel all running workflows
gh run list --status in_progress --json databaseId -q '.[].databaseId' | xargs -I {} gh run cancel {}
```

## AWS ECS Commands

### View Services

```bash
# List clusters
aws ecs list-clusters

# Describe services
aws ecs describe-services \
  --cluster kogna-cluster \
  --services kogna-backend-service kogna-frontend-service

# List tasks
aws ecs list-tasks --cluster kogna-cluster --service-name kogna-backend-service
```

### View Logs

```bash
# Tail backend logs
aws logs tail /ecs/kogna-backend --follow

# Tail frontend logs
aws logs tail /ecs/kogna-frontend --follow

# Filter logs
aws logs tail /ecs/kogna-backend --follow --filter-pattern "ERROR"

# View logs from specific time
aws logs tail /ecs/kogna-backend --since 1h
```

### Force New Deployment

```bash
# Force new deployment (useful for latest tag)
aws ecs update-service \
  --cluster kogna-cluster \
  --service kogna-backend-service \
  --force-new-deployment

aws ecs update-service \
  --cluster kogna-cluster \
  --service kogna-frontend-service \
  --force-new-deployment
```

### Scale Services

```bash
# Scale backend
aws ecs update-service \
  --cluster kogna-cluster \
  --service kogna-backend-service \
  --desired-count 2

# Scale frontend
aws ecs update-service \
  --cluster kogna-cluster \
  --service kogna-frontend-service \
  --desired-count 3
```

### Rollback

```bash
# List task definition revisions
aws ecs list-task-definitions --family-prefix kogna-backend --sort DESC

# Update service to previous revision
aws ecs update-service \
  --cluster kogna-cluster \
  --service kogna-backend-service \
  --task-definition kogna-backend-task:5  # Replace with desired revision
```

### Stop Tasks

```bash
# Stop a specific task
aws ecs stop-task \
  --cluster kogna-cluster \
  --task <task-id>

# Stop all tasks in a service (service will restart them)
aws ecs list-tasks --cluster kogna-cluster --service-name kogna-backend-service \
  --query 'taskArns[]' --output text | \
  xargs -I {} aws ecs stop-task --cluster kogna-cluster --task {}
```

## ECR Commands

### View Images

```bash
# List images in repository
aws ecr describe-images \
  --repository-name kogna-backend \
  --query 'sort_by(imageDetails,& imagePushedAt)[-10:]' \
  --output table

# List all image tags
aws ecr list-images \
  --repository-name kogna-backend \
  --filter tagStatus=TAGGED
```

### Push Images Manually

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag kogna-backend:local <account-id>.dkr.ecr.us-east-1.amazonaws.com/kogna-backend:manual
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/kogna-backend:manual
```

### Clean Up Old Images

```bash
# Delete untagged images
aws ecr list-images \
  --repository-name kogna-backend \
  --filter tagStatus=UNTAGGED \
  --query 'imageIds[*]' \
  --output json | \
  jq -r '.[] | "\(.imageDigest)"' | \
  xargs -I {} aws ecr batch-delete-image \
    --repository-name kogna-backend \
    --image-ids imageDigest={}
```

## Git Workflow

### Feature Branch Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: your feature description"

# Push to GitHub (triggers CI)
git push origin feature/your-feature-name

# Create pull request
gh pr create --title "Add your feature" --body "Description"

# After PR is approved and merged, deployment will trigger automatically
```

### Hotfix Workflow

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix

# Make fix and commit
git add .
git commit -m "fix: critical bug description"

# Push and create PR
git push origin hotfix/critical-fix
gh pr create --title "Hotfix: critical bug" --body "Description" --base main

# After merge, deployment triggers automatically
```

## Environment Variables

### Add GitHub Secret

```bash
# Using GitHub CLI
gh secret set SECRET_NAME -b "secret-value"

# For environment-specific secrets
gh secret set SECRET_NAME -b "secret-value" -e production
```

### Update AWS Secrets Manager

```bash
# Create secret
aws secretsmanager create-secret \
  --name kogna/openai-key \
  --secret-string "sk-your-key-here"

# Update secret
aws secretsmanager update-secret \
  --secret-id kogna/openai-key \
  --secret-string "sk-your-new-key-here"

# Retrieve secret
aws secretsmanager get-secret-value \
  --secret-id kogna/openai-key \
  --query SecretString \
  --output text
```

## Troubleshooting

### CI Failing

```bash
# View workflow logs
gh run view --log

# Re-run failed jobs
gh run rerun <run-id> --failed

# Re-run entire workflow
gh run rerun <run-id>
```

### Deployment Issues

```bash
# Check service events
aws ecs describe-services \
  --cluster kogna-cluster \
  --services kogna-backend-service \
  --query 'services[0].events[0:10]'

# Check task status
aws ecs describe-tasks \
  --cluster kogna-cluster \
  --tasks <task-id>

# View task stopped reason
aws ecs describe-tasks \
  --cluster kogna-cluster \
  --tasks <task-id> \
  --query 'tasks[0].stoppedReason'
```

### Container Issues

```bash
# Execute command in running container
aws ecs execute-command \
  --cluster kogna-cluster \
  --task <task-id> \
  --container kogna-backend \
  --interactive \
  --command "/bin/bash"

# Note: Requires ECS Exec to be enabled on the service
```

## Performance Monitoring

### CloudWatch Metrics

```bash
# CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=kogna-backend-service Name=ClusterName,Value=kogna-cluster \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average

# Memory utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=kogna-backend-service Name=ClusterName,Value=kogna-cluster \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average
```

## Useful Aliases

Add these to your `.bashrc` or `.zshrc`:

```bash
# Docker Compose shortcuts
alias dc='docker-compose'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclogs='docker-compose logs -f'

# AWS shortcuts
alias ecs-services='aws ecs describe-services --cluster kogna-cluster --services kogna-backend-service kogna-frontend-service'
alias ecs-logs-backend='aws logs tail /ecs/kogna-backend --follow'
alias ecs-logs-frontend='aws logs tail /ecs/kogna-frontend --follow'
alias ecs-tasks='aws ecs list-tasks --cluster kogna-cluster'

# GitHub shortcuts
alias gh-runs='gh run list'
alias gh-watch='gh run watch'
```

---

For more detailed information, see [CI-CD-SETUP.md](./CI-CD-SETUP.md)
