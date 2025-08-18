import base64
from selenium.webdriver.common.by import By
from utils.selenium_utils import wait_for_element

class BadgeAutomation:
    def __init__(self, driver):
        self.driver = driver
        
    def get_badge(self, visitor_id: str):
        self.driver.get(f'https://app.evtrack.com/visitors/{visitor_id}/badge')
        
        # Wait for badge element to be visible
        badge_element = wait_for_element(self.driver, By.CSS_SELECTOR, '[data-testid="visitor-badge"]')
        
        # Take screenshot of badge element
        screenshot = badge_element.screenshot_as_png
        
        # Convert to base64 for API response
        return base64.b64encode(screenshot).decode('utf-8')
