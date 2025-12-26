#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting Deployment Process..."

# 1. Extract Infrastructure Details (Assuming terraform apply was already run)
echo "🔍 Extracting configuration from Terraform..."
if ! terraform -chdir=infrastructure output -json > /dev/null 2>&1; then
  echo "❌ Error: Terraform state not found. Please run 'terraform apply' inside the infrastructure folder first."
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
echo "✨ Your app is live at: $(terraform -chdir=infrastructure output -raw frontend_url)"
