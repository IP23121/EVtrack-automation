#!/bin/bash

# Quick test script - just checks if everything is configured correctly
# No browser automation, no long waits

echo "⚡ Quick Setup Test (no browser automation)"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "📁 Project root: $PROJECT_ROOT"

# Check if .env file exists and has required variables
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "❌ .env file not found in $PROJECT_ROOT"
    exit 1
fi

echo "✅ .env file found"

# Check for required environment variables
required_vars=("EVTRACK_EMAIL" "EVTRACK_PASSWORD" "API_KEYS" "HEADLESS_MODE")
for var in "${required_vars[@]}"; do
    if grep -q "^$var=" "$PROJECT_ROOT/.env"; then
        echo "✅ $var configured"
    else
        echo "❌ $var missing from .env"
        exit 1
    fi
done

# Check if Python can import our modules
cd "$PROJECT_ROOT"
echo "🐍 Testing Python imports..."

python3 -c "
try:
    from api.main import app
    from automation.login import EvTrackLogin
    print('✅ All Python modules import successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
" || exit 1

# Check deployment structure
if [ -f "$PROJECT_ROOT/deployment/aws-lambda/serverless.yml" ]; then
    echo "✅ AWS Lambda deployment files found"
else
    echo "❌ AWS Lambda deployment files missing"
    exit 1
fi

echo ""
echo "🎉 Everything looks good! Ready for deployment."
echo ""
echo "To deploy:"
echo "  ./deploy-lambda.sh dev     # Deploy to development"
echo "  ./deploy-lambda.sh prod    # Deploy to production"
echo ""
echo "To test API locally (slow - starts browser):"
echo "  python run.py"
