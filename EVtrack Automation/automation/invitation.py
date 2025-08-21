from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import logging
import time

logger = logging.getLogger(__name__)

class InvitationAutomation:
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

    def check_login_required(self):
        """Check if we're on the login page and need to log in."""
        return '/login' in self.driver.current_url

    async def handle_login_if_needed(self, username=None, password=None):
        """Handle login if we're redirected to login page."""
        if not self.check_login_required():
            return True
        
        if not username or not password:
            raise Exception("Login required but no credentials provided")
        
        try:
            await self.update_progress(10, "Logging in...")
            
            # Fill username field using exact HTML structure
            # HTML: <input class="form-control" autocomplete="username" placeholder="User ID" type="text" id="username" name="username">
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(username)
            
            # Fill password field using exact HTML structure  
            # HTML: <input class="form-control" autocomplete="current-password" placeholder="Password" type="password" id="password" name="password">
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button using exact HTML structure
            # HTML: <button type="submit" class="btn btn-lg btn-warning btn-block">Login</button>
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"].btn.btn-lg.btn-warning.btn-block')
            login_button.click()
            
            # Wait for login to complete
            time.sleep(3)
            
            # Check if login was successful
            if self.check_login_required():
                raise Exception("Login failed - still on login page")
            
            self.logger.info("Login successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise Exception(f"Login failed: {str(e)}")

    async def invite_visitor(self, search_term, invite_data=None, username=None, password=None):
        """Invite a visitor by searching first, then generating an invitation."""
        try:
            await self.update_progress(0, f"Searching for visitor: {search_term}")
            self.logger.info(f"Starting invitation process for: {search_term}")
            
            # Import here to avoid circular imports
            from .visitor_search import VisitorSearchAutomation
            search_automation = VisitorSearchAutomation(self.driver)
            search_automation.set_websocket(self.websocket)
            
            # First, navigate to visitor list and handle login if needed
            self.driver.get('https://app.evtrack.com/visitor/list')
            await self.handle_login_if_needed(username, password)
            
            # Search for the visitor - try exact search first
            visitor = await search_automation.search_visitor_by_term(search_term)
            
            # Only try case-insensitive search if exact search failed
            if not visitor or not isinstance(visitor, dict) or not visitor.get('uuid'):
                self.logger.info("Exact search failed, trying case-insensitive search...")
                visitor = await search_automation.search_visitor_case_insensitive(search_term)
            
            # Final check for valid visitor
            if not visitor or not isinstance(visitor, dict) or not visitor.get('uuid'):
                self.logger.error(f"No visitor found for search term: {search_term}")
                raise Exception(f"No visitor found for search term: {search_term}")
            
            # Get the visitor's UUID
            visitor_uuid = visitor['uuid']
            visitor_name = f"{visitor.get('first_name', '')} {visitor.get('last_name', '')}".strip()
            
            self.logger.info(f"Found visitor: {visitor_name} (UUID: {visitor_uuid})")
            await self.update_progress(25, f"Navigating to visitor profile: {visitor_uuid}")
            
            # Navigate to visitor edit page using the exact URL pattern
            edit_url = f'https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}'
            self.logger.info(f"Navigating to: {edit_url}")
            self.driver.get(edit_url)
            
            # Handle login if needed
            await self.handle_login_if_needed(username, password)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.nav-tabs, .nav-tabs, .tabs'))
            )
            
            await self.update_progress(40, "Navigating to Invite tab...")
            
            # Click the Invite tab using exact HTML structure
            # HTML: <a id="invite-btn" href="#invite"><svg...><span>Invite</span></a>
            try:
                invite_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "invite-btn"))
                )
                
                # Scroll into view and click
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", invite_tab)
                time.sleep(0.5)
                
                # Click the invite tab
                invite_tab.click()
                time.sleep(2)
                
                self.logger.info("Successfully clicked Invite tab")
                
            except Exception as e:
                self.logger.error(f"Could not find or click Invite tab: {str(e)}")
                raise Exception("Could not find Invite tab")
            
            # Wait for invite form to load - exact HTML structure
            # HTML: <form action="/visitor/invite" class="form-horizontal" method="post">
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'form[action="/visitor/invite"].form-horizontal'))
            )
            
            await self.update_progress(60, "Filling invitation form...")
            
            # Fill form fields with exact HTML IDs and values from the provided HTML
            # The HTML form has these exact field names and IDs
            
            # Set Type dropdown
            # HTML: <select class="form-control" id="credentialReaderType" name="credentialReaderType">
            credential_type = invite_data.get("credentialReaderType", "QR_CODE")
            try:
                select_element = self.driver.find_element(By.ID, "credentialReaderType")
                select = Select(select_element)
                select.select_by_value(credential_type)
                self.logger.info(f"Set Type to {credential_type}")
                
                # Trigger change event for vehicle visibility
                self.driver.execute_script("""
                    var event = new Event('change', { bubbles: true });
                    document.getElementById('credentialReaderType').dispatchEvent(event);
                """)
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"Could not set Type: {str(e)}")
            
            # Set reason for visit using exact HTML structure
            # HTML: <select class="form-control" id="647" name="visitReasonId">
            visit_reason_id = invite_data.get("visitReasonId", "647")  # Default: Parent Pickup/Dropoff
            try:
                self.logger.info(f"Attempting to set visitReasonId to: {visit_reason_id}")
                
                # Try JavaScript approach first since element might not be directly interactable
                success = self.driver.execute_script("""
                    var select = document.querySelector('select[name="visitReasonId"]');
                    if (select) {
                        select.value = arguments[0];
                        var event = new Event('change', { bubbles: true });
                        select.dispatchEvent(event);
                        return true;
                    }
                    return false;
                """, visit_reason_id)
                
                if success:
                    self.logger.info(f"Successfully set visitReasonId to {visit_reason_id} using JavaScript")
                    
                    # Verify the selection
                    selected_value = self.driver.execute_script("""
                        var select = document.querySelector('select[name="visitReasonId"]');
                        return select ? select.value : null;
                    """)
                    self.logger.info(f"Verified visitReasonId selection: {selected_value}")
                else:
                    raise Exception("JavaScript method failed - select element not found")
                
            except Exception as e:
                self.logger.error(f"JavaScript method failed for visitReasonId: {str(e)}")
                # Try traditional Selenium approach as fallback
                try:
                    # Wait longer and try to make element visible
                    time.sleep(1)
                    select_element = self.driver.find_element(By.NAME, "visitReasonId")
                    
                    # Try to make it visible/interactable
                    self.driver.execute_script("""
                        arguments[0].style.display = 'block';
                        arguments[0].style.visibility = 'visible';
                        arguments[0].style.opacity = '1';
                    """, select_element)
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", select_element)
                    time.sleep(0.5)
                    
                    select = Select(select_element)
                    select.select_by_value(visit_reason_id)
                    
                    # Trigger change event
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var event = new Event('change', { bubbles: true });
                        element.dispatchEvent(event);
                    """, select_element)
                    
                    self.logger.info(f"Successfully set visitReasonId using fallback method: {visit_reason_id}")
                    
                except Exception as e2:
                    self.logger.error(f"All methods failed for visitReasonId: {str(e2)}")
                    # Use JavaScript to force set the value even if element is hidden
                    try:
                        self.driver.execute_script(f"""
                            var selects = document.querySelectorAll('select');
                            for (var i = 0; i < selects.length; i++) {{
                                if (selects[i].name === 'visitReasonId' || selects[i].id === 'visitReasonId') {{
                                    selects[i].value = '{visit_reason_id}';
                                    var event = new Event('change', {{ bubbles: true }});
                                    selects[i].dispatchEvent(event);
                                    break;
                                }}
                            }}
                        """)
                        self.logger.info(f"Forced visitReasonId to {visit_reason_id} using JavaScript")
                    except Exception as e3:
                        self.logger.warning(f"Could not set visitReasonId - continuing with default: {str(e3)}")
            
            # Set location (required field)
            # HTML: <select class="form-control" required="" id="locationId" name="locationId">
            location_id = invite_data.get("locationId", "")
            if location_id:
                try:
                    select_element = self.driver.find_element(By.ID, "locationId")
                    select = Select(select_element)
                    
                    # Log available options for debugging
                    options = [(option.get_attribute('value'), option.text) for option in select.options]
                    self.logger.info(f"Available locationId options: {options}")
                    
                    select.select_by_value(location_id)
                    self.logger.info(f"Successfully set locationId to {location_id}")
                    
                    # Verify the selection
                    selected_value = select.first_selected_option.get_attribute('value')
                    selected_text = select.first_selected_option.text
                    self.logger.info(f"Verified locationId selection: value='{selected_value}', text='{selected_text}'")
                    
                except Exception as e:
                    self.logger.error(f"Could not set locationId: {str(e)}")
                    # Try alternative selectors
                    try:
                        select_element = self.driver.find_element(By.NAME, "locationId")
                        select = Select(select_element)
                        select.select_by_value(location_id)
                        self.logger.info(f"Set locationId using name selector: {location_id}")
                    except Exception as e2:
                        self.logger.error(f"Alternative locationId selector also failed: {str(e2)}")
            else:
                self.logger.warning("locationId is required but not provided or is empty")
            
            # Handle date and time fields with exact HTML IDs
            # HTML IDs: activateDate, activateTime, expiryDate, expiryTime
            date_time_fields = {
                "activateDate": invite_data.get("activateDate", ""),
                "activateTime": invite_data.get("activateTime", ""),
                "expiryDate": invite_data.get("expiryDate", ""),
                "expiryTime": invite_data.get("expiryTime", "")
            }
            
            for field_id, field_value in date_time_fields.items():
                if field_value:
                    try:
                        element = self.driver.find_element(By.ID, field_id)
                        # Clear the field first
                        element.clear()
                        # Set the value
                        element.send_keys(field_value)
                        self.logger.info(f"Set {field_id} to {field_value}")
                        
                        # Trigger change/blur events for validation
                        self.driver.execute_script(f"""
                            var element = document.getElementById('{field_id}');
                            if (element) {{
                                var changeEvent = new Event('change', {{ bubbles: true }});
                                var blurEvent = new Event('blur', {{ bubbles: true }});
                                element.dispatchEvent(changeEvent);
                                element.dispatchEvent(blurEvent);
                            }}
                        """)
                        
                    except Exception as e:
                        self.logger.warning(f"Could not set {field_id}: {str(e)}")
            
            # Set visitor UUID (hidden field) if provided
            # HTML: <input type="hidden" id="visitorUuid" name="visitorUuid" value="...">
            visitor_uuid_field = invite_data.get("visitorUuid", "")
            if visitor_uuid_field:
                try:
                    hidden_field = self.driver.find_element(By.ID, "visitorUuid")
                    # Use JavaScript to set hidden field value
                    self.driver.execute_script(f"""
                        var hiddenField = document.getElementById('visitorUuid');
                        if (hiddenField) {{
                            hiddenField.value = '{visitor_uuid_field}';
                        }}
                    """)
                    self.logger.info(f"Set visitorUuid to {visitor_uuid_field}")
                except Exception as e:
                    self.logger.warning(f"Could not set visitorUuid: {str(e)}")
            else:
                # If not provided, use the visitor UUID we found during search
                try:
                    hidden_field = self.driver.find_element(By.ID, "visitorUuid")
                    current_value = hidden_field.get_attribute('value')
                    if current_value:
                        self.logger.info(f"visitorUuid already set to: {current_value}")
                    else:
                        # Set it to the visitor UUID we found
                        self.driver.execute_script(f"""
                            var hiddenField = document.getElementById('visitorUuid');
                            if (hiddenField) {{
                                hiddenField.value = '{visitor_uuid}';
                            }}
                        """)
                        self.logger.info(f"Set visitorUuid to: {visitor_uuid}")
                except Exception as e:
                    self.logger.warning(f"Could not handle visitorUuid: {str(e)}")
            
            await self.update_progress(90, "Generating invitation...")
            
            # Submit the form by clicking Generate Invite button using exact HTML structure
            # HTML: <button class="btn btn-primary" value="generate" name="action" type="submit">Generate Invite</button>
            try:
                generate_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[value="generate"][name="action"].btn.btn-primary'))
                )
                
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", generate_button)
                time.sleep(0.3)
                
                # Click the button
                generate_button.click()
                
                self.logger.info("Successfully clicked Generate Invite button")
                
            except Exception as e:
                # Fallback to alternative selectors
                generate_clicked = False
                fallback_selectors = [
                    'button[type="submit"][name="action"]',
                    'button.btn-primary[type="submit"]',
                    'input[type="submit"]',
                    'button:contains("Generate")',
                    '//button[contains(text(), "Generate")]'
                ]
                
                for selector in fallback_selectors:
                    try:
                        if selector.startswith("//"):
                            # XPath selector
                            generate_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            # CSS selector
                            generate_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if generate_button.is_displayed() and generate_button.is_enabled():
                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", generate_button)
                            time.sleep(0.3)
                            
                            try:
                                generate_button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", generate_button)
                            
                            generate_clicked = True
                            self.logger.info(f"Successfully clicked generate button using fallback selector: {selector}")
                            break
                    except Exception as e2:
                        self.logger.debug(f"Fallback selector {selector} failed: {str(e2)}")
                        continue
                
                if not generate_clicked:
                    raise Exception(f"Could not find or click Generate Invite button. Original error: {str(e)}")
            
            # Wait for success/response
            time.sleep(3)
            
            # Check if we're still on the same page or redirected
            current_url = self.driver.current_url
            self.logger.info(f"After submission, current URL: {current_url}")
            
            # Look for success indicators
            success_indicators = [
                "Invitation generated successfully",
                "Invite sent",
                "Generated successfully",
                "success"
            ]
            
            page_text = self.driver.page_source.lower()
            invitation_successful = any(indicator.lower() in page_text for indicator in success_indicators)
            
            if invitation_successful:
                await self.update_progress(100, "Invitation generated successfully")
            else:
                # Check for error messages
                error_indicators = [
                    "error",
                    "failed",
                    "invalid",
                    "please try again"
                ]
                
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    self.logger.warning("Possible error detected in page content")
                
                await self.update_progress(100, "Invitation process completed")
            
            return {
                'success': True,
                'message': 'Visitor invitation generated successfully',
                'visitor_uuid': visitor_uuid,
                'visitor_name': visitor_name,
                'invite_settings': {
                    'type': invite_data.get("credentialReaderType", "QR_CODE"),
                    'reason_for_visit_id': invite_data.get("visitReasonId", "647"),
                    'location_id': invite_data.get("locationId", ""),
                    'activate_date': invite_data.get("activateDate", ""),
                    'activate_time': invite_data.get("activateTime", ""),
                    'expiry_date': invite_data.get("expiryDate", ""),
                    'expiry_time': invite_data.get("expiryTime", "")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error inviting visitor: {str(e)}")
            await self.update_progress(100, "Failed to generate invitation")
            raise
