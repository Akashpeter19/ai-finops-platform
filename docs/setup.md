# Setup Guide

## Prerequisites

- AWS account with Cost Explorer enabled
- macOS with Homebrew
- Python 3.11
- Terraform 1.7+
- Docker Desktop

## Local setup

```bash
# Clone the repo
git clone https://github.com/Akashpeter19/ai-finops-platform
cd ai-finops-platform

# Set up Python environment
cd lambda
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

## AWS deployment

```bash
# Configure AWS credentials
aws configure --profile finops

# Deploy infrastructure
cd terraform
terraform init
terraform apply
```

## Grafana dashboard

```bash
# Start Grafana locally
cd docker
docker compose up -d

# Open in browser
open http://127.0.0.1:3000
# Login: admin / admin
```

## Environment variables

| Variable | Description | Default |
|---|---|---|
| APP_REGION | AWS region | us-east-1 |
| DB_PATH | SQLite database path | /tmp/finops.db |
| PROJECT_NAME | Resource name prefix | ai-finops |

## Secrets

The Slack webhook URL is stored in AWS SSM Parameter Store:

```bash
aws ssm put-parameter \
  --name "/finops/slack_webhook_url" \
  --value "https://hooks.slack.com/..." \
  --type SecureString \
  --profile finops
```
