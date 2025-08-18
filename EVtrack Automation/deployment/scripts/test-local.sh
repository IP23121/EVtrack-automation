#!/bin/bash

# Local testing script for Lambda function

echo "🧪 Testing EvTrack API Lambda function locally..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAMBDA_DIR="$PROJECT_ROOT/deployment/aws-lambda"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 Lambda config: $LAMBDA_DIR"

# Change to Lambda directory
cd "$LAMBDA_DIR"

# Check if serverless-offline is available
if ! npx serverless offline --help > /dev/null 2>&1; then
    echo "📦 Installing serverless-offline..."
    npm install
fi

# Set environment variables for local testing
export HEADLESS_MODE=true
export AWS_LAMBDA_FUNCTION_NAME=evtrack-api-local

echo "🌐 Starting local Lambda server..."
echo "📱 API will be available at: http://localhost:3000"
echo "📖 Swagger docs at: http://localhost:3000/docs/swagger"
echo ""
echo "Press Ctrl+C to stop"

npx serverless offline --host 0.0.0.0 --port 3000
