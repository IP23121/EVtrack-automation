from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from utils.selenium_utils import wait_for_element, fill_text_field
import logging
import time
import base64
import io
import tempfile
import os

class VisitorCreateUpdateAutomation:
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

    def _upload_file_safely(self, file_key, file_data):
        """Upload a file to the Uppy Dashboard system exactly like the HTML site"""
        try:
            # Handle file data - ensure we have the correct structure
            if isinstance(file_data, dict):
                filename = file_data.get('filename')
                file_content = file_data.get('content') or file_data.get('file_data')
                content_type = file_data.get('content_type', 'application/octet-stream')
                
                if not filename or not file_content:
                    self.logger.error(f"Missing filename or content in file_data for {file_key}")
                    return False
            else:
                self.logger.error(f"File data is not a dict for {file_key}: {type(file_data)}")
                return False
                
            self.logger.info(f"Uploading {file_key}: {filename} ({len(file_content)} bytes)")
            
            # Map file keys to Uppy container IDs exactly like the HTML site
            uppy_id_map = {
                'photo': 'uppy-photo',
                'signature': 'uppy-signature', 
                'id_document': 'uppy-copyOfId'
            }
            
            uppy_id = uppy_id_map.get(file_key)
            if not uppy_id:
                self.logger.error(f"Unknown file key: {file_key}")
                return False
            
            # Wait for Uppy container to be present and ready
            uppy_container = None
            for attempt in range(5):
                try:
                    uppy_container = self.driver.find_element(By.ID, uppy_id)
                    if uppy_container:
                        break
                except:
                    time.sleep(1)
                    
            if not uppy_container:
                self.logger.error(f"Could not find Uppy container: {uppy_id}")
                return False
            
            # Clear any existing files in the Uppy dashboard
            try:
                remove_buttons = uppy_container.find_elements(By.CSS_SELECTOR, '.uppy-Dashboard-Item-action--remove, .uppy-u-reset.uppy-c-btn.uppy-Dashboard-Item-action.uppy-Dashboard-Item-action--remove')
                for button in remove_buttons:
                    if button.is_displayed():
                        try:
                            button.click()
                            time.sleep(0.3)
                        except:
                            pass
            except:
                pass  # Ignore removal errors
            
            # Find the file input within the Uppy dashboard
            file_input = None
            input_selectors = [
                'input[type="file"].uppy-Dashboard-input',
                'input[type="file"][name="files[]"]',
                'input[type="file"]'
            ]
            
            for selector in input_selectors:
                try:
                    file_input = uppy_container.find_element(By.CSS_SELECTOR, selector)
                    if file_input:
                        break
                except:
                    continue
                    
            if not file_input:
                self.logger.error(f"Could not find file input in Uppy container: {uppy_id}")
                return False
            
            # Process file content - handle both base64 and binary data
            if isinstance(file_content, str):
                if file_content.startswith('data:'):
                    # Remove data URL prefix and decode
                    header, data = file_content.split(',', 1)
                    file_content = base64.b64decode(data)
                else:
                    # Assume it's base64 encoded
                    try:
                        file_content = base64.b64decode(file_content)
                    except:
                        # If base64 decode fails, treat as plain text
                        file_content = file_content.encode('utf-8')
            
            # Create temporary file for upload
            file_extension = os.path.splitext(filename)[1] if filename else '.tmp'
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload the file using Selenium
                file_input.send_keys(temp_file_path)
                time.sleep(1.5)  # Quick wait for Uppy to process
                
                # Quick verification - don't wait too long
                for attempt in range(3):  # Only 3 attempts = 3 seconds max
                    try:
                        # Check if file appears in dashboard (quick check)
                        uploaded_files = uppy_container.find_elements(By.CSS_SELECTOR, 
                            '.uppy-Dashboard-Item, .uppy-Dashboard-files .uppy-Dashboard-Item')
                        if uploaded_files:
                            self.logger.info(f"File appears in dashboard for {file_key}")
                            break
                    except:
                        pass
                    time.sleep(1)
                
                # Quick save button click (try only the most common selectors)
                save_button_selectors = [
                    'button.uppy-DashboardContent-save',  # Most likely selector
                    '.uppy-StatusBar-actionBtn--upload'   # Fallback
                ]
                
                for selector in save_button_selectors:
                    try:
                        save_button = uppy_container.find_element(By.CSS_SELECTOR, selector)
                        if save_button.is_displayed() and save_button.is_enabled():
                            save_button.click()
                            self.logger.info(f" Clicked Save button for {file_key}")
                            time.sleep(1)  # Quick save wait
                            break
                    except:
                        continue
                
                # Verify upload by checking for file items in the dashboard
                uploaded_files = uppy_container.find_elements(By.CSS_SELECTOR, '.uppy-Dashboard-Item, .uppy-Dashboard-files .uppy-Dashboard-Item')
                
                # Also check the hidden input field to see if it has a value
                hidden_input_value = None
                try:
                    hidden_input = self.driver.find_element(By.ID, file_key)
                    hidden_input_value = hidden_input.get_attribute('value')
                except:
                    pass
                
                success = len(uploaded_files) > 0 or (hidden_input_value and hidden_input_value.strip())
                
                if success:
                    self.logger.info(f" Successfully uploaded {file_key}: {filename}")
                    
                    # Wait a bit more for Uppy to fully process the file
                    time.sleep(1)
                    
                    return True
                else:
                    self.logger.warning(f" Upload verification failed for {file_key}: {filename}")
                    return False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to upload {file_key}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def update_visitor_profile(self, search_term, visitor_data, files=None):
        """Update a visitor profile with form data and files"""
        try:
            await self.update_progress(5, "Starting visitor profile update...")
            updated_fields = []
            
            # Import VisitorSearchAutomation to find the visitor first
            from automation.visitor_search import VisitorSearchAutomation
            
            search_automation = VisitorSearchAutomation(self.driver)
            search_automation.set_websocket(self.websocket)
            
            # Use the provided search term
            if not search_term:
                # Fallback to extracting from visitor_data if search_term is not provided
                search_term = visitor_data.get('name', '') or visitor_data.get('email', '') or visitor_data.get('phone', '')
                if not search_term:
                    raise Exception("No search term provided (name, email, or phone required)")
            
            await self.update_progress(10, f"Searching for visitor: {search_term}")
            visitor_found = await search_automation.search_visitor_by_term(search_term)
            
            if not visitor_found:
                raise Exception(f"Visitor not found: {search_term}")
            
            # Navigate to visitor profile
            await self.update_progress(20, "Opening visitor profile...")
            
            # Get visitor UUID from search result
            visitor_uuid = visitor_found.get('uuid')
            if not visitor_uuid or visitor_uuid == 'undefined' or visitor_uuid == '':
                self.logger.error(f"Invalid visitor UUID: {visitor_uuid}")
                raise Exception(f"Could not get valid visitor UUID from search result. Got: {visitor_uuid}")
            
            # Navigate directly to visitor edit page using UUID
            profile_url = f'https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}'
            self.logger.info(f"Navigating to visitor profile: {profile_url}")
            
            # Validate URL before navigation
            if 'criteria' in profile_url:
                self.logger.error(f"Invalid profile URL generated: {profile_url}")
                raise Exception("Generated invalid profile URL - this would redirect to search criteria")
            
            self.driver.get(profile_url)
            
            # Check if we ended up in the wrong place
            if 'criteria' in self.driver.current_url:
                self.logger.error(f"Navigation failed - ended up at: {self.driver.current_url}")
                raise Exception("Navigation redirected to search criteria page - invalid visitor UUID")
            
            # Quick login check
            if '/login' in self.driver.current_url:
                raise Exception("Session expired - please re-login")
                raise Exception("Session expired - please re-login")
            
            # Wait for profile page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input, select, textarea'))
            )
            
            # Click on Profile tab
            await self.update_progress(30, "Switching to Profile tab...")
            try:
                # Try multiple selectors for the Profile tab
                profile_selectors = [
                    "//a[contains(@href, '#profile')]",
                    "//a[contains(text(), 'Profile')]", 
                    "//button[contains(text(), 'Profile')]",
                    ".nav-link[href*='profile']",
                    "a[data-target*='profile']"
                ]
                
                profile_tab = None
                for selector in profile_selectors:
                    try:
                        if selector.startswith("//"):
                            profile_tab = self.driver.find_element(By.XPATH, selector)
                        else:
                            profile_tab = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if profile_tab:
                    profile_tab.click()
                    time.sleep(2)  # Wait for tab to switch
                    self.logger.info("Successfully clicked Profile tab")
                else:
                    self.logger.info("Profile tab not found - assuming we're already on the profile page")
                    
            except Exception as e:
                self.logger.info(f"Could not switch to Profile tab: {str(e)} - continuing anyway")
            
            await self.update_progress(40, "Updating form fields...")
            
            # Handle text fields
            text_fields = {
                'name': 'name',
                'email': 'email',
                'phone': 'phone',
                'alt_number': 'altNumber',
                'company': 'company',
                'purpose_of_visit': 'purposeOfVisit',
                'emergency_contact_name': 'emergencyContactName',
                'emergency_contact_phone': 'emergencyContactPhone'
            }
            
            for field_key, field_id in text_fields.items():
                if field_key in visitor_data and visitor_data[field_key] and str(visitor_data[field_key]).strip():
                    try:
                        element = self.driver.find_element(By.ID, field_id)
                        element.clear()
                        element.send_keys(str(visitor_data[field_key]).strip())
                        updated_fields.append(field_key)
                        self.logger.info(f"Updated {field_key}: {visitor_data[field_key]}")
                    except NoSuchElementException:
                        self.logger.warning(f"Field {field_key} (ID: {field_id}) not found on page")
                    except Exception as e:
                        self.logger.warning(f"Error updating field {field_key}: {str(e)}")
            
            # Handle select/dropdown fields
            select_fields = {
                'gender': 'gender'
            }
            
            for field_key, field_id in select_fields.items():
                if field_key in visitor_data and visitor_data[field_key] and str(visitor_data[field_key]).strip():
                    try:
                        select_element = Select(self.driver.find_element(By.ID, field_id))
                        value = str(visitor_data[field_key]).strip()
                        
                        # Try to select by visible text first
                        try:
                            select_element.select_by_visible_text(value)
                            updated_fields.append(field_key)
                            self.logger.info(f"Updated {field_key}: {value}")
                        except:
                            # If that fails, try by value
                            try:
                                select_element.select_by_value(value)
                                updated_fields.append(field_key)
                                self.logger.info(f"Updated {field_key}: {value}")
                            except:
                                self.logger.warning(f"Could not select option '{value}' for {field_key}")
                                
                    except Exception as e:
                        self.logger.warning(f"Error updating select {field_key}: {str(e)}")
            
            # Handle reason for visit dropdown (uses name attribute instead of consistent ID)
            if 'reason_for_visit' in visitor_data and visitor_data['reason_for_visit'] and str(visitor_data['reason_for_visit']).strip():
                try:
                    select_element = Select(self.driver.find_element(By.NAME, 'visitReasonId'))
                    value = str(visitor_data['reason_for_visit']).strip()
                    
                    # Try to select by visible text first
                    try:
                        select_element.select_by_visible_text(value)
                        updated_fields.append('reason_for_visit')
                        self.logger.info(f"Updated reason_for_visit: {value}")
                    except:
                        # If that fails, try by value
                        try:
                            select_element.select_by_value(value)
                            updated_fields.append('reason_for_visit')
                            self.logger.info(f"Updated reason_for_visit: {value}")
                        except:
                            self.logger.warning(f"Could not select option '{value}' for reason_for_visit")
                            
                except Exception as e:
                    self.logger.warning(f"Error updating reason_for_visit: {str(e)}")
            
            # Handle nationality and country of issue dropdowns
            country_fields = {
                'nationality': 'nationality',
                'country_of_issue': 'countryOfIssue'
            }
            
            for field_key, field_id in country_fields.items():
                if field_key in visitor_data and visitor_data[field_key] and str(visitor_data[field_key]).strip():
                    try:
                        select_element = Select(self.driver.find_element(By.ID, field_id))
                        value = str(visitor_data[field_key]).strip()
                        
                        # Get all available options
                        options = select_element.options
                        selected = False
                        
                        # Try exact match first
                        for option in options:
                            option_text = option.text.strip()
                            if option_text.lower() == value.lower():
                                select_element.select_by_value(option.get_attribute('value'))
                                updated_fields.append(field_key)
                                self.logger.info(f"Updated {field_key}: {option_text} (exact match)")
                                selected = True
                                break
                        
                        # If no exact match, try partial match
                        if not selected:
                            for option in options:
                                option_text = option.text.strip().lower()
                                if value.lower() in option_text or option_text in value.lower():
                                    select_element.select_by_value(option.get_attribute('value'))
                                    updated_fields.append(field_key)
                                    self.logger.info(f"Updated {field_key}: {option.text} (partial match)")
                                    selected = True
                                    break
                        
                        # If still no match, try common country name mappings
                        if not selected:
                            country_mappings = {
                                'usa': 'united states',
                                'us': 'united states',
                                'america': 'united states',
                                'uk': 'united kingdom',
                                'britain': 'united kingdom',
                                'uae': 'united arab emirates',
                                'emirates': 'united arab emirates',
                                'antigua & barbuda': 'antigua and barbuda',
                                'bosnia & herzegovina': 'bosnia and herzegovina',
                                'trinidad & tobago': 'trinidad and tobago',
                                'st. kitts & nevis': 'saint kitts and nevis',
                                'st. lucia': 'saint lucia',
                                'st. vincent & the grenadines': 'saint vincent and the grenadines'
                            }
                            
                            # Try direct mapping first
                            mapped_value = country_mappings.get(value.lower(), value.lower())
                            for option in options:
                                option_text = option.text.strip().lower()
                                if mapped_value == option_text:
                                    select_element.select_by_value(option.get_attribute('value'))
                                    updated_fields.append(field_key)
                                    self.logger.info(f"Updated {field_key}: {option.text} (mapped match)")
                                    selected = True
                                    break
                            
                            # If still no match, try replacing & with 'and' and vice versa
                            if not selected:
                                alternatives = []
                                if '&' in value:
                                    alternatives.append(value.replace('&', 'and'))
                                if ' and ' in value:
                                    alternatives.append(value.replace(' and ', ' & '))
                                
                                for alt_value in alternatives:
                                    for option in options:
                                        if option.text.strip().lower() == alt_value.lower():
                                            select_element.select_by_value(option.get_attribute('value'))
                                            updated_fields.append(field_key)
                                            self.logger.info(f"Updated {field_key}: {option.text} (alternative match)")
                                            selected = True
                                            break
                                    if selected:
                                        break
                        
                        if not selected:
                            self.logger.warning(f"Could not find country option for '{value}' in {field_key}")
                                
                    except Exception as e:
                        self.logger.warning(f"Error updating country field {field_key}: {str(e)}")
            
            await self.update_progress(80, "Handling file uploads...")
            
            # Handle file uploads if provided
            if files:
                file_fields = ['photo', 'signature', 'id_document']
                
                for file_key in file_fields:
                    file_upload_key = f'{file_key}_upload'
                    if file_upload_key in files:
                        success = self._upload_file_safely(file_key, files[file_upload_key])
                        if success:
                            updated_fields.append(file_key)
            
            await self.update_progress(90, "Saving changes...")
            
            # Save the form - use the exact button from the HTML
            try:
                # Find the specific Save button with exact attributes
                save_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"][name="action"][value="save"]#submitBtn')
                
                if save_button.is_displayed() and save_button.is_enabled():
                    self.logger.info("Found Save button - clicking now")
                    
                    # Scroll to button to ensure it's visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
                    time.sleep(0.5)
                    
                    # Click the save button
                    save_button.click()
                    self.logger.info("Save button clicked successfully")
                    
                    await self.update_progress(95, "Waiting for save confirmation...")
                    
                    # Wait briefly for save to process
                    time.sleep(3)
                    
                    # Simple success - don't navigate anywhere else
                    await self.update_progress(100, "Visitor profile updated successfully!")
                    
                    return {
                        "success": True,
                        "message": "Visitor profile updated successfully",
                        "updated_fields": updated_fields
                    }
                else:
                    raise Exception("Save button found but not clickable")
                    
            except NoSuchElementException:
                self.logger.error("Could not find Save button with exact selector")
                raise Exception("Save button not found on page")
                
            except Exception as e:
                error_msg = f"Error clicking save button: {str(e)}"
                self.logger.error(error_msg)
                # Try to handle alert
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    self.logger.error(f"Alert during save: {alert_text}")
                    alert.accept()
                    error_msg += f" Alert: {alert_text}"
                except:
                    pass
                
                return {
                    "success": False,
                    "message": error_msg,
                    "updated_fields": updated_fields
                }
        
        except Exception as e:
            self.logger.error(f"Error updating visitor profile: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating visitor profile: {str(e)}",
                "updated_fields": []
            }
