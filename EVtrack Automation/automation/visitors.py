from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils.selenium_utils import wait_for_element, fill_text_field
from .visitor_add import VisitorAddAutomation
import logging
import time

logger = logging.getLogger(__name__)

class VisitorAutomation:
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

    async def get_visitor_detail(self, visitor_id):
        """Get detailed information from the Profile tab form - ALL AVAILABLE FIELDS."""
        try:
            await self.update_progress(0, "Getting visitor details...")
            
            # Navigate directly to visitor edit page
            profile_url = f'https://app.evtrack.com/visitor/edit?uuid={visitor_id}'
            self.driver.get(profile_url)
            
            # Quick login check
            if '/login' in self.driver.current_url:
                raise Exception("Not logged in")
            
            # Wait for page load
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input, select, textarea'))
            )
            
            await self.update_progress(25, "Navigating to Profile tab...")

            # Navigate to Profile tab first
            try:
                profile_tab = self.driver.find_element(By.XPATH, "//a[contains(@href, '#profile') or contains(text(), 'Profile')]")
                profile_tab.click()
                time.sleep(2)
                self.logger.info("Successfully clicked Profile tab")
            except Exception as e:
                self.logger.warning(f"Could not find or click Profile tab: {str(e)}")
                # Try alternative selectors
                try:
                    profile_tab = self.driver.find_element(By.XPATH, "//ul[@class='nav nav-tabs']//a[contains(text(), 'Profile')]")
                    profile_tab.click()
                    time.sleep(2)
                except:
                    self.logger.error("Failed to locate Profile tab with alternative selectors")
            
            await self.update_progress(50, "Extracting profile information...")

            # Initialize visitor info with all expected fields
            visitor_info = {
                "uuid": visitor_id,
                "first_name": "Not provided",
                "last_name": "Not provided", 
                "gender": "Not provided",
                "reason_for_visit": "Not provided",
                "created_by": "Not provided",
                "portrait_url": "Not provided",
                "profile_url": profile_url,
                "initials": "Not provided",
                "id_nr": "Not provided",
                "first_nations": "Not provided",
                "people_of_determination": "Not provided",
                "company": "Not provided",
                "mobile_number": "Not provided",
                "alt_number": "Not provided",
                "email": "Not provided",
                "address": "Not provided",
                "date_of_birth": "Not provided",
                "nationality": "Not provided",
                "country_of_issue": "Not provided",
                "comments": "Not provided",
                "photo": "Not provided",
                "signature": "Not provided",
                "copy_of_id": "Not provided"
            }
            
            # Extract UUID from hidden field
            try:
                uuid_element = self.driver.find_element(By.ID, "uuid")
                uuid_value = uuid_element.get_attribute("value")
                if uuid_value and uuid_value.strip():
                    visitor_info["uuid"] = uuid_value.strip()
            except Exception as e:
                self.logger.debug(f"Could not extract UUID: {str(e)}")
            
            await self.update_progress(65, "Extracting form fields...")
            
            # Extract text input fields from profile tab
            text_fields = {
                "initials": "initials",
                "first_name": "firstName", 
                "last_name": "lastName",
                "id_nr": "identityNr",
                "company": "company",
                "email": "email",
                "address": "address",
                "date_of_birth": "dateOfBirth",
                "comments": "comments"
            }
            
            for field_name, field_id in text_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    if element.tag_name == "textarea":
                        value = element.text or element.get_attribute("value") or ""
                    else:
                        value = element.get_attribute("value") or ""
                    
                    if value and value.strip():
                        visitor_info[field_name] = value.strip()
                        
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")
            
            # Extract checkbox fields (First Nations and People of Determination)
            checkbox_fields = {
                "first_nations": "firstNations1",
                "people_of_determination": "peopleOfDetermination1"
            }
            
            for field_name, field_id in checkbox_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    is_checked = element.is_selected()
                    visitor_info[field_name] = "Yes" if is_checked else "No"
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")
            
            await self.update_progress(75, "Extracting dropdown fields...")
            
            # Extract select/dropdown fields
            select_fields = {
                "gender": ("id", "gender"),
                "nationality": ("id", "nationality"), 
                "country_of_issue": ("id", "countryOfIssue"),
                "reason_for_visit": ("name", "visitReasonId")  # This field uses name, not id
            }
            
            for field_name, (locator_type, selector) in select_fields.items():
                try:
                    if locator_type == "id":
                        select_element = self.driver.find_element(By.ID, selector)
                    else:
                        select_element = self.driver.find_element(By.NAME, selector)
                    selected_option = select_element.find_element(By.CSS_SELECTOR, "option:checked")
                    value = selected_option.text.strip()
                    # Skip default/empty option values
                    if value and value not in ["None", "", "Select...", "Choose..."]:
                        visitor_info[field_name] = value
                        
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")
            
            await self.update_progress(85, "Extracting contact information...")
            
            # Extract international phone number fields
            phone_fields = {
                "mobile_number": "mobileNumberPlaceholder",
                "alt_number": "alternativeNumberPlaceholder"
            }
            
            for field_name, field_id in phone_fields.items():
                try:
                    # Try the placeholder input field first
                    element = self.driver.find_element(By.ID, field_id)
                    value = element.get_attribute("value") or ""
                    
                    # If no value in placeholder, try the hidden input field
                    if not value or not value.strip():
                        hidden_field_id = field_id.replace("Placeholder", "")
                        hidden_element = self.driver.find_element(By.ID, hidden_field_id)
                        value = hidden_element.get_attribute("value") or ""
                    
                    if value and value.strip():
                        visitor_info[field_name] = value.strip()
                        
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")
            
            await self.update_progress(95, "Extracting file attachments...")
            
            # Extract file upload status
            file_fields = {
                "photo": "photo",
                "signature": "signature", 
                "copy_of_id": "copyOfId"
            }
            
            for field_name, field_id in file_fields.items():
                try:
                    # Check hidden file input
                    element = self.driver.find_element(By.ID, field_id)
                    value = element.get_attribute("value") or ""
                    
                    # Also check for Uppy file widget indicators
                    uppy_container = self.driver.find_element(By.CSS_SELECTOR, f"#{field_id}UploadContainer")
                    uppy_files = uppy_container.find_elements(By.CSS_SELECTOR, ".uppy-Dashboard-files .uppy-Dashboard-Item")
                    
                    if value and value.strip():
                        visitor_info[field_name] = "Available"
                    elif uppy_files:
                        visitor_info[field_name] = "Available"
                        
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")
            
            # Set portrait URL based on photo availability
            if visitor_info["photo"] == "Available":
                visitor_info["portrait_url"] = "Available"
            
            # Extract created by information (may be in metadata or other fields)
            try:
                # Look for created by information in various places
                created_by_selectors = [
                    "input[name='createdBy']",
                    "#createdBy",
                    "[data-field='created_by']"
                ]
                
                for selector in created_by_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        value = element.get_attribute("value") or element.text
                        if value and value.strip():
                            visitor_info["created_by"] = value.strip()
                            break
                    except:
                        continue
                        
            except Exception as e:
                self.logger.debug(f"Could not extract created_by: {str(e)}")

            await self.update_progress(100, "Profile details extracted successfully")
            self.logger.info(f"Successfully extracted visitor details for UUID: {visitor_info['uuid']}")
            
            # Count populated fields for logging
            populated_fields = len([v for v in visitor_info.values() if v != "Not provided" and v != ""])
            self.logger.info(f"Extracted {populated_fields} populated fields out of {len(visitor_info)} total fields")
            
            return visitor_info

        except Exception as e:
            self.logger.error(f"Error getting visitor details: {str(e)}")
            await self.update_progress(100, "Failed to get details")
            raise

    async def get_visitor_summary(self, search_term=None):
        """Get visitor summary - if search_term provided, search for specific visitor with full details.
        If no search_term, get all visitors from the list page."""
        try:
            if search_term:
                # Specific visitor search with comprehensive details
                await self.update_progress(0, f"Searching for specific visitor: {search_term}")
                
                from .visitor_search import VisitorSearchAutomation
                search_automation = VisitorSearchAutomation(self.driver)
                if self.websocket:
                    search_automation.set_websocket(self.websocket)
                
                visitor_data = await search_automation.search_visitor_case_insensitive(search_term)
                
                if not visitor_data:
                    await self.update_progress(100, "No visitors found")
                    return []
                
                visitor_uuid = visitor_data['uuid']
                visitor_name = f"{visitor_data.get('first_name', '')} {visitor_data.get('last_name', '')}".strip()
                
                await self.update_progress(50, f"Getting comprehensive profile for {visitor_name}")
                
                from .visitor_details import VisitorDetailsAutomation
                details_automation = VisitorDetailsAutomation(self.driver)
                if self.websocket:
                    details_automation.set_websocket(self.websocket)
                
                profile_data = await details_automation.get_comprehensive_visitor_profile(visitor_uuid)
                
                # Convert comprehensive profile to visitor summary format
                comprehensive_visitor = {
                    'uuid': visitor_uuid,
                    'first_name': profile_data.get('basic_info', {}).get('first_name', ''),
                    'last_name': profile_data.get('basic_info', {}).get('last_name', ''),
                    'mobile': profile_data.get('contact_info', {}).get('mobile_number', ''),
                    'email': profile_data.get('contact_info', {}).get('email', ''),
                    'company': profile_data.get('contact_info', {}).get('company', ''),
                    'nationality': profile_data.get('personal_details', {}).get('nationality', ''),
                    'country_of_issue': profile_data.get('personal_details', {}).get('country_of_issue', ''),
                    'reason_for_visit': profile_data.get('visit_info', {}).get('reason_for_visit', ''),
                    'created_by': profile_data.get('metadata', {}).get('created_by', ''),
                    'created_at': profile_data.get('metadata', {}).get('created_at', ''),
                    'updated_at': profile_data.get('metadata', {}).get('updated_at', ''),
                    'status': 'Current',
                    'profile_url': f"https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}"
                }
                
                # Add all additional fields from profile
                for section_name, section_data in profile_data.items():
                    if isinstance(section_data, dict):
                        for field_name, field_value in section_data.items():
                            if field_name not in comprehensive_visitor and field_value:
                                comprehensive_visitor[field_name] = field_value
                
                await self.update_progress(100, f"Complete profile retrieved for {visitor_name}")
                return [comprehensive_visitor]
            
            else:
                # Get all visitors from the list page
                await self.update_progress(0, "Getting all visitors from list...")
                
                # Navigate to visitor list page
                self.driver.get('https://app.evtrack.com/visitor/list')
                await self.update_progress(20, "Loading visitor list...")
                
                # Wait for page to load
                wait = WebDriverWait(self.driver, 30)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "visitor-list")))
                
                await self.update_progress(40, "Extracting visitor data...")
                
                # Get all visitor rows from the table
                visitor_rows = self.driver.find_elements(By.CSS_SELECTOR, ".visitor-list tr.visitor-row")
                visitors = []
                
                for i, row in enumerate(visitor_rows):
                    try:
                        # Extract basic visitor info from the list row
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 5:  # Ensure we have enough columns
                            
                            # Get UUID from the row's data attributes or edit link
                            uuid = None
                            edit_link = row.find_element(By.CSS_SELECTOR, "a[href*='edit']")
                            if edit_link:
                                href = edit_link.get_attribute('href')
                                if 'uuid=' in href:
                                    uuid = href.split('uuid=')[1].split('&')[0]
                            
                            if not uuid:
                                continue
                                
                            visitor = {
                                'uuid': uuid,
                                'first_name': cells[0].text.strip() if len(cells) > 0 else '',
                                'last_name': cells[1].text.strip() if len(cells) > 1 else '',
                                'mobile': cells[2].text.strip() if len(cells) > 2 else '',
                                'email': cells[3].text.strip() if len(cells) > 3 else '',
                                'company': cells[4].text.strip() if len(cells) > 4 else '',
                                'nationality': cells[5].text.strip() if len(cells) > 5 else '',
                                'status': 'Current',
                                'profile_url': f"https://app.evtrack.com/visitor/edit?uuid={uuid}"
                            }
                            visitors.append(visitor)
                            
                        progress = 40 + (i / len(visitor_rows) * 50)
                        await self.update_progress(int(progress), f"Processed {i+1}/{len(visitor_rows)} visitors")
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing visitor row {i}: {str(e)}")
                        continue
                
                await self.update_progress(100, f"Retrieved {len(visitors)} visitors")
                return visitors
                
        except Exception as e:
            self.logger.error(f"Error getting visitor summary: {str(e)}")
            await self.update_progress(100, "Error occurred")
            raise

    async def create_update_visitor(self, visitor_data, files=None):
        """Create or update a visitor using the new EVTrack workflow."""
        try:
            # Use the new VisitorAddAutomation class for adding visitors
            visitor_add_automation = VisitorAddAutomation(self.driver)
            visitor_add_automation.set_websocket(self.websocket)
            
            result = await visitor_add_automation.add_visitor(visitor_data, files)
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating visitor: {str(e)}")
            await self.update_progress(100, f"Failed to create visitor: {str(e)}")
            raise

    async def update_visitor(self, search_term, visitor_data, files=None):
        """Update existing visitor by searching first."""
        try:
            await self.update_progress(0, f"Searching for visitor: {search_term}")
            
            # First, search for the visitor
            visitors = await self.get_visitor_summary(search_term)
            
            if not visitors:
                raise Exception(f"No visitor found for search term: {search_term}")
            
            # Get the first visitor's UUID
            visitor_uuid = visitors[0]['uuid']
            
            await self.update_progress(30, f"Updating visitor: {visitor_uuid}")
            
            # Navigate to edit page
            edit_url = f'https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}'
            self.driver.get(edit_url)
            
            # Wait for form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'form'))
            )
            
            await self.update_progress(60, "Updating visitor fields...")
            
            # Update form fields
            field_mappings = {
                'first_name': 'firstName',
                'last_name': 'lastName', 
                'email': 'email',
                'mobile': 'mobile',
                'company': 'company',
                'nationality': 'nationality',
                'country_of_issue': 'countryOfIssue',
                'reason_for_visit': 'reasonForVisit'
            }
            
            updated_fields = []
            for field_key, form_name in field_mappings.items():
                if field_key in visitor_data and visitor_data[field_key]:
                    try:
                        element = self.driver.find_element(By.NAME, form_name)
                        element.clear()
                        element.send_keys(visitor_data[field_key])
                        updated_fields.append(field_key)
                    except Exception:
                        continue
            
            await self.update_progress(90, "Saving changes...")
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
            submit_button.click()
            
            time.sleep(2)
            
            await self.update_progress(100, "Visitor updated successfully")
            return {
                'success': True, 
                'message': 'Visitor updated successfully',
                'updated_fields': updated_fields,
                'uuid': visitor_uuid
            }
            
        except Exception as e:
            self.logger.error(f"Error updating visitor: {str(e)}")
            await self.update_progress(100, "Failed to update visitor")
            raise

    async def get_visitor_badge(self, search_term):
        """Generate and retrieve a visitor badge by searching for the visitor first."""
        try:
            await self.update_progress(0, f"Searching for visitor: {search_term}")
            
            # Use the new VisitorSearchAutomation for reliable search
            from .visitor_search import VisitorSearchAutomation
            search_automation = VisitorSearchAutomation(self.driver)
            if self.websocket:
                search_automation.set_websocket(self.websocket)
            
            # Search for the visitor using the reliable search method
            visitor_data = await search_automation.search_visitor_case_insensitive(search_term)
            
            if not visitor_data:
                raise Exception(f"No visitor found for search term: {search_term}")
            
            # Get the visitor's UUID and name
            visitor_uuid = visitor_data['uuid']
            visitor_name = f"{visitor_data.get('first_name', '')} {visitor_data.get('last_name', '')}".strip()
            
            await self.update_progress(50, f"Generating badge for: {visitor_name}")
            
            # Get the badge URL - DO NOT navigate to it to avoid automatic download
            badge_url = f'https://app.evtrack.com/visitor/generate-visitor-label?uuid={visitor_uuid}'
            self.logger.info(f"Badge URL constructed: {badge_url}")
            self.logger.info("IMPORTANT: Will fetch badge using requests library - NO browser navigation!")
            
            # CRITICAL: Ensure Selenium browser NEVER navigates to badge URL
            current_url = self.driver.current_url
            self.logger.info(f"Current browser URL before badge fetch: {current_url}")
            
            # SAFETY CHECK: Block any potential navigation to badge URL  
            if 'generate-visitor-label' in current_url:
                self.logger.error("ERROR: Browser is already on badge generation page - this should never happen!")
                raise Exception("Browser navigation to badge URL detected - aborting to prevent download")
            
            # ADDITIONAL SAFETY: Ensure we don't accidentally navigate during this process
            # Store original URL to verify later
            original_url = current_url
            
            # Use requests to fetch the badge content directly (bypasses browser download)
            import requests
            
            # Get cookies from selenium session to maintain authentication
            selenium_cookies = self.driver.get_cookies()
            requests_cookies = {}
            for cookie in selenium_cookies:
                requests_cookies[cookie['name']] = cookie['value']
            
            # Create headers to make this look like a regular API request (not a download)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf,application/json,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'X-Requested-With': 'XMLHttpRequest'  # This makes it clear it's an AJAX request
            }
            
            await self.update_progress(75, "Fetching badge content using requests (no browser download)...")
            
            # Make the request with explicit headers to prevent download behavior
            self.logger.info("Making requests.get() with anti-download headers")
            response = requests.get(badge_url, cookies=requests_cookies, headers=headers, stream=True)
            self.logger.info(f"Requests completed. Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")
            
            # Ensure we close the response properly to prevent any hanging connections
            try:
                content_bytes = response.content
            finally:
                response.close()
            
            if response.status_code == 200:
                import base64
                
                # Get the content without triggering any downloads
                badge_content_bytes = content_bytes
                content_type = response.headers.get('Content-Type', 'application/pdf')
                
                # Encode PDF content for both display and download
                badge_content = base64.b64encode(badge_content_bytes).decode('utf-8')
                
                await self.update_progress(100, "Badge content fetched successfully - NO downloads triggered")
                
                self.logger.info(f"Badge content fetched for {visitor_name}. Content type: {content_type}, Size: {len(badge_content_bytes)} bytes")
                self.logger.info("CONFIRMED: No browser downloads should have occurred - content fetched via requests only")
                
                # Final check: Ensure browser URL hasn't changed (confirming no navigation occurred)
                final_url = self.driver.current_url
                self.logger.info(f"Browser URL after badge fetch: {final_url}")
                if final_url == original_url:
                    self.logger.info(" Browser URL unchanged - CONFIRMED no navigation occurred")
                else:
                    self.logger.error(f" CRITICAL: Browser URL changed from {original_url} to {final_url}")
                    raise Exception(f"Unexpected browser navigation detected - URL changed to {final_url}")
                
                return {
                    'success': True,
                    'message': 'Visitor badge generated successfully',
                    'visitor_uuid': visitor_uuid,
                    'visitor_name': visitor_name,
                    'badge_url': badge_url,
                    'badge_content': badge_content,
                    'content_type': content_type,
                    'filename': f'badge_{visitor_uuid}.pdf'
                }
            else:
                raise Exception(f"Failed to download badge. Status code: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Error generating visitor badge: {str(e)}")
            await self.update_progress(100, "Failed to generate badge")
            raise


