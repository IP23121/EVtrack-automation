import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_driver(headless=True):
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')  # updated headless arg
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            # Don't disable JavaScript as the application relies on it
            # chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Add window size to ensure elements are visible
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Add user agent to avoid detection as a bot
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36')
        
        # CRITICAL: Prevent automatic downloads and PDF auto-opening
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-background-downloads')
        chrome_options.add_argument('--disable-automatic-downloads')
        chrome_options.add_argument('--disable-download-notification')
        chrome_options.add_argument('--disable-file-downloads')
        chrome_options.add_argument('--disable-background-mode')
        
        # Set download behavior preferences to COMPLETELY BLOCK downloads
        prefs = {
            "download.default_directory": "/tmp/null_invalid_directory_to_block_downloads",  # Invalid directory
            "download.prompt_for_download": True,  # Always prompt for downloads
            "download.directory_upgrade": False,
            "download.open_pdf_in_system_reader": False,  # Don't open PDFs in system reader
            "plugins.always_open_pdf_externally": False,  # Don't open PDFs externally
            "plugins.plugins_disabled": ["Chrome PDF Viewer", "Adobe Flash Player", "Adobe Reader"],
            "profile.default_content_settings.popups": 0,  # Block popups
            "profile.default_content_setting_values.automatic_downloads": 2,  # Block automatic downloads
            "profile.default_content_setting_values.notifications": 2,  # Block notifications
            "profile.managed_default_content_settings": {
                "automatic_downloads": 2  # Block at managed policy level
            },
            "safebrowsing.enabled": False,  # Disable safe browsing that might interfere
            "profile.default_content_settings.media_stream": 2,  # Block media access
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Additional flags to prevent any file access
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-popup-blocking')  # Paradoxically helps control downloads
        
        logger.info("Added AGGRESSIVE Chrome options to COMPLETELY prevent any downloads")
        
        logger.info("Setting up Chrome driver")
        # Use webdriver_manager to handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Increase timeouts for better reliability
        driver.implicitly_wait(20)  # Increased from 10
        driver.set_page_load_timeout(60)  # Increased from 30
        driver.set_script_timeout(60)  # Increased from 30
        
        logger.info("Chrome driver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"Failed to start Chrome: {str(e)}")
        raise Exception(f"Chrome setup failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def wait_for_element(driver, by, value, timeout=20):
    logger.info(f"Waiting for element: {by}={value} (timeout: {timeout}s)")
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        logger.info(f"Element found: {by}={value}")
        return element
    except Exception as e:
        logger.error(f"Element not found: {by}={value}, error: {str(e)}")
        # Log page source for debugging (limited to avoid storage issues)
        try:
            logger.info(f"Current URL: {driver.current_url}")
            logger.debug(f"Page source preview: {driver.page_source[:200]}...")
        except Exception as source_error:
            logger.error(f"Failed to get page source: {str(source_error)}")
        raise

def click_element(driver, by, value):
    logger.info(f"Clicking element: {by}={value}")
    try:
        element = wait_for_element(driver, by, value)
        element.click()
        logger.info(f"Element clicked: {by}={value}")
    except Exception as e:
        logger.error(f"Failed to click element: {by}={value}, error: {str(e)}")
        raise

def fill_text_field(driver, by, value, text):
    logger.info(f"Filling text field: {by}={value} with text: {text[:3]}...")
    try:
        element = wait_for_element(driver, by, value)
        element.clear()
        element.send_keys(text)
        logger.info(f"Text field filled: {by}={value}")
    except Exception as e:
        logger.error(f"Failed to fill text field: {by}={value}, error: {str(e)}")
        raise
