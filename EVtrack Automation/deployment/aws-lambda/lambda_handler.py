"""
AWS Lambda handler for EvTrack Automation API
This file adapts the FastAPI application to work with AWS Lambda
"""

import os
import sys

# Add the project root to Python path for imports
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from mangum import Mangum
from api.main import app

# Configure for Lambda environment
os.environ.setdefault('HEADLESS_MODE', 'True')  # Force headless mode in Lambda

# Create the Lambda handler using Mangum
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    AWS Lambda entry point
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        HTTP response formatted for API Gateway
    """
    return handler(event, context)
