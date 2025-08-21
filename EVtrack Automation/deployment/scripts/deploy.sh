#!/bin/bash

# EvTrack Automation API - AWS Lambda Deployment Script

echo " Starting EvTrack API deployment to AWS Lambda..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAMBDA_DIR="$PROJECT_ROOT/deployment/aws-lambda"

echo " Project root: $PROJECT_ROOT"
echo " Lambda config: $LAMBDA_DIR"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo " AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if Node.js and npm are installed
if ! command -v npm &> /dev/null; then
    echo " npm not found. Please install Node.js and npm first."
    exit 1
fi

# Change to Lambda directory
cd "$LAMBDA_DIR"

# Install Serverless Framework dependencies
echo " Installing Serverless Framework dependencies..."
npm install

# Install Python dependencies in project root
echo " Installing Python dependencies..."
cd "$PROJECT_ROOT"
pip install -r requirements.txt

# Return to Lambda directory for deployment
cd "$LAMBDA_DIR"

# Deploy to AWS Lambda
echo " Deploying to AWS Lambda..."
STAGE=${1:-dev}
echo "Deploying to stage: $STAGE"

npx serverless deploy --stage $STAGE

if [ $? -eq 0 ]; then
    echo " Deployment successful!"
    echo " Getting API endpoint..."
    npx serverless info --stage $STAGE
else
    echo " Deployment failed!"
    exit 1
fi
