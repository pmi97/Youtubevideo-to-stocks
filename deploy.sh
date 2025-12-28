#!/bin/bash

# =============================================================================
# YouTube Agent - Deployment Script
# Usage:
#   ./deploy.sh --init        # First-time setup (creates infrastructure)
#   ./deploy.sh               # Deploy code changes only
# =============================================================================

set -e

# Check for --init flag
INIT_MODE=false
if [ "$1" = "--init" ]; then
  INIT_MODE=true
fi

echo "🚀 Starting Deployment Process..."

# =============================================================================
# INIT MODE: First-time infrastructure setup
# =============================================================================
if [ "$INIT_MODE" = true ]; then
  echo "📦 First-time setup..."
  
  # Load environment variables from .env file
  if [ -f .env ]; then
    echo "� Loading configuration from .env file..."
    set -a  # Export all variables
    source .env
    set +a
  else
    echo "❌ Error: .env file not found."
    echo "   Copy .env.example to .env and fill in your values."
    exit 1
  fi
  
  # Prompt for alert email (not in .env)
  read -p "Email for billing alerts: " ALERT_EMAIL
  
  # Map .env variable names to terraform variable names
  SMTP_USER=${FROM_EMAIL:-""}
  SMTP_HOST=${SMTP_SERVER:-"smtp.gmail.com"}
  
  cd infrastructure
  
  # Initialize Terraform if needed
  if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
  fi
  
  # Step 1: Create ECR first (so we can push image before Lambda is created)
  echo "🏗️  Step 1/3: Creating ECR repository..."
  terraform apply -target=aws_ecr_repository.backend \
    -var="alert_email=$ALERT_EMAIL" \
    -var="gemini_api_key=$GEMINI_API_KEY" \
    -var="youtube_api_key=$YOUTUBE_API_KEY" \
    -var="smtp_user=$SMTP_USER" \
    -var="smtp_pass=$SMTP_PASS" \
    -var="from_email=$FROM_EMAIL" \
    -var="webshare_proxy_username=$WEBSHARE_PROXY_USERNAME" \
    -var="webshare_proxy_password=$WEBSHARE_PROXY_PASSWORD"
  
  # Get ECR URL (region uses default since output not available after targeted apply)
  ECR_URL=$(terraform output -raw ecr_repository_url)
  AWS_REGION="us-east-1"
  
  cd ..
  
  # Step 2: Build and push Docker image
  echo "📦 Step 2/3: Building and pushing Docker image..."
  aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL
  docker build --platform linux/amd64 --provenance=false -t youtube-agent-backend -f backend/Dockerfile .
  docker tag youtube-agent-backend:latest $ECR_URL:latest
  docker push $ECR_URL:latest
  
  # Step 3: Create remaining infrastructure
  echo "🏗️  Step 3/3: Creating remaining infrastructure (Lambda, S3, CloudFront, etc.)..."
  cd infrastructure
  terraform apply \
    -var="alert_email=$ALERT_EMAIL" \
    -var="gemini_api_key=$GEMINI_API_KEY" \
    -var="youtube_api_key=$YOUTUBE_API_KEY" \
    -var="smtp_user=$SMTP_USER" \
    -var="smtp_pass=$SMTP_PASS" \
    -var="from_email=$FROM_EMAIL" \
    -var="webshare_proxy_username=$WEBSHARE_PROXY_USERNAME" \
    -var="webshare_proxy_password=$WEBSHARE_PROXY_PASSWORD"
  cd ..
  
  echo ""
  echo "✅ Infrastructure created!"
  echo "✨ Your app is live at: https://$(terraform -chdir=infrastructure output -raw frontend_url)"
  exit 0
fi

# =============================================================================
# DEPLOY MODE: Regular code deployment
# =============================================================================

# 1. Extract Infrastructure Details (Assuming terraform apply was already run)
echo "🔍 Extracting configuration from Terraform..."
if ! terraform -chdir=infrastructure output -json > /dev/null 2>&1; then
  echo "❌ Error: Terraform state not found."
  echo "   Run './deploy.sh --init' for first-time setup."
  exit 1
fi

# 2. Extract Infrastructure Details
BACKEND_URL=$(terraform -chdir=infrastructure output -raw backend_url)
ECR_URL=$(terraform -chdir=infrastructure output -raw ecr_repository_url)
S3_BUCKET=$(terraform -chdir=infrastructure output -raw s3_bucket_id)
AWS_REGION=$(terraform -chdir=infrastructure output -raw aws_region)

echo "📍 Backend URL: $BACKEND_URL"
echo "📍 ECR URL: $ECR_URL"
echo "📍 S3 Bucket: $S3_BUCKET"

# 3. Build & Push Backend
echo "📦 Building and Pushing Backend Image..."
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# Build for Linux/AMD64 (Lambda standard) - provenance=false required for Lambda
docker build --platform linux/amd64 --provenance=false -t youtube-agent-backend -f backend/Dockerfile .
docker tag youtube-agent-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Trigger Lambda update to pull the new image
echo "🔄 Updating Lambda function..."
aws lambda update-function-code --function-name youtube-agent-backend --image-uri $ECR_URL:latest --region $AWS_REGION > /dev/null

# 4. Build & Deploy Frontend
echo "🌐 Building and Deploying Frontend..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  pnpm install
fi

# Build React app with the Backend URL injected
VITE_API_URL="${BACKEND_URL}api" pnpm build

# Sync files to S3
echo "📤 Uploading to S3..."
aws s3 sync dist/ s3://$S3_BUCKET --delete

cd ..

echo "✅ Deployment Complete!"
echo "✨ Your app is live at: https://$(terraform -chdir=infrastructure output -raw frontend_url)"
