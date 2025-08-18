from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.selenium_utils import wait_for_element, fill_text_field, click_element
import time
import logging

logger = logging.getLogger(__name__)

class EvTrackLogin:
    def __init__(self, driver):
        self.driver = driver
        
    async def login(self, email, password):
        try:
            # Navigate to login page
            logger.info("Navigating to login page")
            self.driver.get('https://app.evtrack.com/login')
            
            # Wait for login form with multiple selectors
            login_form_found = False
            selectors = [
                (By.CSS_SELECTOR, 'input[name="username"]'),
                (By.CSS_SELECTOR, 'input[type="email"]'),
                (By.CSS_SELECTOR, 'form input[type="text"]')
            ]
            
            for selector_type, selector in selectors:
                try:
                    logger.info(f"Trying to find login form with selector: {selector}")
                    wait_for_element(self.driver, selector_type, selector, timeout=5)
                    login_form_found = True
                    logger.info("Login form found")
                    break
                except Exception:
                    continue
                    
            if not login_form_found:
                raise Exception("Could not find login form after multiple attempts")
            
            # Wait for page to load
            time.sleep(2)
            
            # Wait for login form
            logger.info("Waiting for login form")
            wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                'input[name="username"]',
                timeout=20
            )
            
            logger.info("Login form found, filling credentials")
            # Fill credentials with multiple selector attempts
            username_selectors = [
                ('input[name="username"]', 'name'),
                ('input[type="email"]', 'type'),
                ('input[name="email"]', 'name')
            ]
            
            username_filled = False
            for selector, attr_type in username_selectors:
                try:
                    fill_text_field(self.driver, By.CSS_SELECTOR, selector, email)
                    username_filled = True
                    logger.info(f"Username filled using {attr_type} selector")
                    break
                except Exception:
                    continue
                    
            if not username_filled:
                raise Exception("Could not fill username/email field")
                
            # Fill password with similar fallbacks
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    fill_text_field(self.driver, By.CSS_SELECTOR, selector, password)
                    password_filled = True
                    logger.info("Password field filled")
                    break
                except Exception:
                    continue
                    
            if not password_filled:
                raise Exception("Could not fill password field")
                
            time.sleep(1)  # Wait for fields to settle
            
            # Click login button
            logger.info("Clicking login button")
            click_element(self.driver, By.CSS_SELECTOR, '.btn.btn-lg.btn-warning.btn-block')
            
            # Wait for successful login with multiple verification attempts
            logger.info("Waiting for successful login")
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                time.sleep(2)
                current_url = self.driver.current_url.lower()
                
                if "login" not in current_url:
                    logger.info(f"Successfully logged in, current URL: {current_url}")
                    break
                    
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Login verification failed, still on: {current_url}")
                    # Try to capture any error messages
                    try:
                        error_messages = self.driver.find_elements(By.CSS_SELECTOR, '.alert, .error, .message')
                        if error_messages:
                            error_text = ' | '.join([msg.text for msg in error_messages])
                            raise Exception(f"Login failed: {error_text}")
                    except:
                        pass
                    raise Exception("Login failed: Still on login page after multiple attempts")
                
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise Exception(f"Login failed: {str(e)}")
