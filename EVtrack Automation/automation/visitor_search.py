from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
import time
import re

logger = logging.getLogger(__name__)

class VisitorSearchAutomation:
    def __init__(self, driver):
        self.driver = driver
        self.websocket = None
        self.logger = logging.getLogger(__name__)
        
    def set_websocket(self, websocket):
        self.websocket = websocket
    
    async def update_progress(self, percent, status):
        if self.websocket:
            await self.websocket.send_json({
                "type": "progress",
                "percent": percent,
                "status": status
            })
        self.logger.info(f"Progress: {percent}% - {status}")

    async def search_visitor_by_term(self, search_term):
        """Search for a visitor using the visitor list page."""
        try:
            await self.update_progress(10, f"Searching for visitor: {search_term}")
            
            # Navigate to visitor list page - exact URL from requirements
            self.driver.get('https://app.evtrack.com/visitor/list')
            
            # Login check - if we're redirected to login, we need credentials from the calling method
            if '/login' in self.driver.current_url:
                self.logger.info("Redirected to login page - login will be handled by InvitationAutomation")
                raise Exception("Not logged in - login required")

            # Wait for table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'dataTables_wrapper'))
            )
            
            # Find the search input using exact HTML structure
            # HTML: <label>Search:<input type="search" class="form-control input-sm" placeholder="" aria-controls="listTable"></label>
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"][aria-controls="listTable"]'))
            )
            
            # Clear any existing search and enter the new term
            search_input.clear()
            time.sleep(0.5)  # Brief pause after clearing
            search_input.send_keys(search_term)
            
            # Wait for search to process - look for table to update
            time.sleep(2)  # Reduced wait time
            
            await self.update_progress(50, "Processing search results...")
            
            # Get table results
            table = self.driver.find_element(By.ID, 'listTable')
            
            # Wait a bit more for the table to fully load the search results
            time.sleep(1)
            
            rows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')
            
            # Check if no results found
            if not rows or len(rows) == 0:
                self.logger.info(f"No table rows found for search term: {search_term}")
                return None
                
            if len(rows) == 1:
                first_row_text = rows[0].text.strip()
                if "No matching records found" in first_row_text or "No data available" in first_row_text:
                    self.logger.info(f"No matching records found for search term: {search_term}")
                    return None
            
            # Log how many results we found
            self.logger.info(f"Found {len(rows)} rows in search results")
            
            # Get the first visitor result
            if rows:
                first_row = rows[0]
                cols = first_row.find_elements(By.TAG_NAME, 'td')
                
                self.logger.info(f"First row has {len(cols)} columns")
                
                if len(cols) >= 1:  # At least one column
                    # Simple and reliable UUID extraction
                    uuid = None
                    
                    # Find any link with 'edit?uuid=' in the href (based on your example)
                    edit_links = first_row.find_elements(By.CSS_SELECTOR, 'a[href*="edit?uuid="]')
                    if edit_links:
                        href = edit_links[0].get_attribute('href')
                        self.logger.info(f"Found edit link: {href}")
                        # Extract UUID: edit?uuid=a4c7e9e2-ed73-4a5a-84a9-423259d41c0c
                        if 'uuid=' in href:
                            uuid = href.split('uuid=')[1].split('&')[0]
                            self.logger.info(f"Extracted UUID: {uuid}")
                    else:
                        self.logger.warning("No edit link found in search result row")
                    
                    if uuid:
                        visitor_data = {
                            'uuid': uuid,
                            'first_name': cols[1].text.strip() if len(cols) > 1 else '',
                            'last_name': cols[2].text.strip() if len(cols) > 2 else '',
                            'mobile': cols[3].text.strip() if len(cols) > 3 else '',
                            'status': cols[0].text.strip() if len(cols) > 0 else ''
                        }
                        
                        self.logger.info(f"Successfully found visitor: {visitor_data['first_name']} {visitor_data['last_name']} (UUID: {uuid})")
                        return visitor_data
                    else:
                        self.logger.warning("Could not find UUID in search result row")
                        # Log the row HTML for debugging
                        self.logger.debug(f"Row HTML: {first_row.get_attribute('outerHTML')}")
                        return None
                else:
                    self.logger.warning("First row has no columns")
            
            self.logger.info(f"Could not extract visitor data from search results for: {search_term}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error searching for visitor: {str(e)}")
            return None

    async def search_visitor_case_insensitive(self, search_term):
        """
        Perform a more efficient search - try exact search first, then fallbacks only if needed.
        """
        try:
            await self.update_progress(5, f"Searching for visitor: {search_term}")
            
            # First try the original search term
            self.logger.info(f"Trying exact search for: {search_term}")
            result = await self.search_visitor_by_term(search_term)
            if result:
                self.logger.info(f"Found visitor on exact search: {result.get('first_name', '')} {result.get('last_name', '')}")
                return result
            
            # Only try variations if exact search failed
            self.logger.info(f"Exact search failed for '{search_term}', trying variations...")
            
            # Try different case variations
            variations_to_try = []
            
            if search_term != search_term.lower():
                variations_to_try.append(search_term.lower())
            if search_term != search_term.title():
                variations_to_try.append(search_term.title())
            if search_term != search_term.upper():
                variations_to_try.append(search_term.upper())
            
            # Try case variations first
            for variation in variations_to_try:
                self.logger.info(f"Trying case variation: {variation}")
                result = await self.search_visitor_by_term(variation)
                if result:
                    self.logger.info(f"Found visitor with case variation: {result.get('first_name', '')} {result.get('last_name', '')}")
                    return result
            
            # Only if all simple variations fail, try name parts
            if ' ' in search_term.strip():
                parts = search_term.strip().split()
                
                # Try first name only
                if len(parts) >= 1:
                    first_name = parts[0]
                    self.logger.info(f"Trying first name only: {first_name}")
                    result = await self.search_visitor_by_term(first_name)
                    if result:
                        # Verify match
                        full_name = f"{result.get('first_name', '')} {result.get('last_name', '')}".lower()
                        if any(part.lower() in full_name for part in parts):
                            self.logger.info(f"Found visitor by first name: {result.get('first_name', '')} {result.get('last_name', '')}")
                            return result
                
                # Try last name only  
                if len(parts) >= 2:
                    last_name = parts[-1]
                    self.logger.info(f"Trying last name only: {last_name}")
                    result = await self.search_visitor_by_term(last_name)
                    if result:
                        # Verify match
                        full_name = f"{result.get('first_name', '')} {result.get('last_name', '')}".lower()
                        if any(part.lower() in full_name for part in parts):
                            self.logger.info(f"Found visitor by last name: {result.get('first_name', '')} {result.get('last_name', '')}")
                            return result
            
            self.logger.info(f"No visitor found for '{search_term}' or any variations")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in visitor search: {str(e)}")
            return None

    async def get_visitor_details_by_uuid(self, visitor_uuid):
        """Get detailed visitor information by UUID."""
        try:
            # Navigate directly to visitor edit page
            profile_url = f'https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}'
            self.driver.get(profile_url)
            
            # Quick login check
            if '/login' in self.driver.current_url:
                raise Exception("Not logged in")
            
            # Wait for page load
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input, select, textarea'))
            )
            
            # Navigate to Profile tab if needed
            try:
                profile_tab = self.driver.find_element(By.XPATH, "//a[contains(@href, '#profile') or contains(text(), 'Profile')]")
                profile_tab.click()
                time.sleep(1)
            except:
                pass  # Already on profile or profile tab not needed
            
            # Extract basic visitor information
            visitor_info = {
                "uuid": visitor_uuid,
                "first_name": "",
                "last_name": "",
                "email": "",
                "mobile": "",
                "company": ""
            }
            
            # Extract text input fields
            text_fields = {
                "first_name": "firstName", 
                "last_name": "lastName",
                "email": "email",
                "company": "company"
            }
            
            for field_name, field_id in text_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    value = element.get_attribute("value") or ""
                    if value.strip():
                        visitor_info[field_name] = value.strip()
                except:
                    pass
            
            # Extract phone number (may be in international format field)
            try:
                # Try the placeholder input field first
                mobile_element = self.driver.find_element(By.ID, "mobileNumberPlaceholder")
                mobile_value = mobile_element.get_attribute("value") or ""
                
                # If no value in placeholder, try the hidden input field
                if not mobile_value.strip():
                    hidden_mobile = self.driver.find_element(By.ID, "mobileNumber")
                    mobile_value = hidden_mobile.get_attribute("value") or ""
                
                if mobile_value.strip():
                    visitor_info["mobile"] = mobile_value.strip()
            except:
                pass
            
            return visitor_info
            
        except Exception as e:
            self.logger.error(f"Error getting visitor details: {str(e)}")
            return None
