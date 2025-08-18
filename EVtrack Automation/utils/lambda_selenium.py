"""
Lambda-optimized Selenium utilities for AWS Lambda environment
Uses chrome-aws-lambda layer for headless browser support
"""

import os
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def start_driver_lambda(headless=True):
    """
    Start Chrome driver optimized for AWS Lambda
    
    Args:
        headless (bool): Whether to run in headless mode (should always be True in Lambda)
        
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    
    # Detect if we're running in Lambda
    is_lambda = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
    
    if is_lambda:
        # Lambda environment configuration
        chrome_options = Options()
        chrome_options.binary_location = '/opt/chrome/chrome'
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-tools')
        chrome_options.add_argument('--no-zygote')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.add_argument('--v=99')
        chrome_options.add_argument('--data-path=/tmp/chrome-user-data')
        chrome_options.add_argument('--homedir=/tmp')
        chrome_options.add_argument('--disk-cache-dir=/tmp/chrome-cache')
        
        # Set window size for consistent rendering
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Use chromedriver from lambda layer
        service = Service('/opt/chromedriver')
        
        # Create driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    else:
        # Local development - fall back to regular selenium utils
        from utils.selenium_utils import start_driver
        driver = start_driver(headless=headless)
    
    # Set timeouts
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    
    return driver


def cleanup_temp_files():
    """
    Clean up temporary files created during Lambda execution
    """
    try:
        # Clean Chrome temp files
        temp_dirs = ['/tmp/chrome-user-data', '/tmp/chrome-cache']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not clean temp files: {e}")
