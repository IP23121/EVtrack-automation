from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
import logging
import time
import os
import tempfile

logger = logging.getLogger(__name__)

class VisitorAddAutomation:
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

    async def add_visitor(self, visitor_data, files=None):
        """Add a new visitor following the exact EVTrack workflow."""
        try:
            await self.update_progress(0, "Starting visitor creation...")
            
            # Step 1: Login straight to the dashboard link
            await self.update_progress(5, "Navigating to visitor dashboard...")
            self.driver.get('https://app.evtrack.com/visitor/dashboard')
            
            # Quick login check
            if '/login' in self.driver.current_url:
                raise Exception("Not logged in to EVTrack")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            await self.update_progress(10, "Clicking Add button...")
            
            # Step 2: Click the "Add" button
            try:
                add_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.dt-button.btn.btn-primary[type="button"] span'))
                )
                add_button.click()
                self.logger.info("Successfully clicked Add button")
            except Exception as e:
                # Try alternative selector for the Add button
                try:
                    add_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'dt-button') and contains(@class, 'btn-primary')]//span[text()='Add']")
                    add_button.click()
                    self.logger.info("Successfully clicked Add button (alternative selector)")
                except Exception as e2:
                    self.logger.error(f"Could not find Add button: {str(e)} | {str(e2)}")
                    raise Exception("Could not find or click Add button on visitor dashboard")
            
            # Wait for the add visitor form to load
            await self.update_progress(15, "Waiting for add visitor form to load...")
            
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, 'visitorProfileForm'))
                )
                self.logger.info("Add visitor form loaded successfully")
            except TimeoutException:
                self.logger.error("Add visitor form did not load within 15 seconds")
                raise Exception("Add visitor form failed to load")
            
            await self.update_progress(20, "Form loaded, starting to fill visitor information...")
            
            # Step 3: Fill in all the form fields based on the visitor_data
            await self._fill_visitor_form(visitor_data, files)
            
            await self.update_progress(90, "Submitting visitor form...")
            
            # Step 4: Click the "Add Visitor" submit button
            try:
                submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn.btn-primary[type="submit"]')
                submit_button.click()
                self.logger.info("Successfully clicked Add Visitor submit button")
            except Exception as e:
                self.logger.error(f"Could not find or click submit button: {str(e)}")
                raise Exception("Could not find or click Add Visitor submit button")
            
            # Wait for form submission to complete
            await self.update_progress(95, "Processing visitor creation...")
            time.sleep(3)
            
            # Check if we were redirected to success page or back to dashboard
            current_url = self.driver.current_url
            if 'visitor/dashboard' in current_url or 'visitor/list' in current_url or 'visitor/edit' in current_url:
                await self.update_progress(100, "Visitor created successfully!")
                self.logger.info("Visitor creation appears successful - redirected to dashboard/list/edit page")
                
                # Try to extract visitor UUID from URL if we're on edit page
                visitor_uuid = None
                if 'visitor/edit' in current_url and 'uuid=' in current_url:
                    try:
                        visitor_uuid = current_url.split('uuid=')[1].split('&')[0]
                        self.logger.info(f"Extracted visitor UUID: {visitor_uuid}")
                    except:
                        pass
                
                return {
                    'success': True,
                    'message': f"Visitor {visitor_data.get('first_name', '')} {visitor_data.get('last_name', '')} added successfully".strip(),
                    'visitor_uuid': visitor_uuid,
                    'redirect_url': current_url
                }
            else:
                # Still on add form - check for validation errors
                try:
                    # Look for any error messages on the form
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, '.alert-danger, .error, .has-error')
                    if error_elements:
                        error_message = error_elements[0].text
                        self.logger.error(f"Form validation error: {error_message}")
                        raise Exception(f"Form validation failed: {error_message}")
                except:
                    pass
                
                await self.update_progress(100, "Visitor creation may have failed")
                self.logger.warning("Still on add form after submission - creation may have failed")
                return {
                    'success': False,
                    'message': 'Visitor creation status unclear - form submission completed but still on add page',
                    'current_url': current_url
                }
                
        except Exception as e:
            await self.update_progress(100, f"Error: {str(e)}")
            self.logger.error(f"Error in add_visitor: {str(e)}")
            raise

    async def _fill_visitor_form(self, visitor_data, files=None):
        """Fill all the visitor form fields matching the EVTrack form structure."""
        try:
            # Map frontend field names to EVTrack form field IDs based on the HTML you provided
            field_mappings = {
                # Basic Information
                'initials': 'initials',
                'first_name': 'firstName', 
                'last_name': 'lastName',
                'id_number': 'identityNr',
                'company': 'company',
                'email': 'email',
                'address': 'address',
                'date_of_birth': 'dateOfBirth',
                'comments': 'comments',
                'alt_number': 'alternativeNumberPlaceholder',  # International phone input
                
                # Nationality and Country dropdowns
                'nationality': 'nationality',
                'country_of_issue': 'countryOfIssue',
                
                # Visit reason dropdown  
                'reason_for_visit': 'visitReasonId'
            }
            
            await self.update_progress(25, "Filling text fields...")
            
            # Fill text input fields
            for field_name, form_id in field_mappings.items():
                if field_name in visitor_data and visitor_data[field_name]:
                    try:
                        # Handle special cases
                        if form_id in ['nationality', 'countryOfIssue', 'visitReasonId']:
                            # These are dropdown selects - handle separately
                            continue
                        elif form_id in ['mobileNumberPlaceholder', 'alternativeNumberPlaceholder']:
                            # These are international phone number inputs - handle separately
                            continue
                        else:
                            # Regular text input or textarea
                            element = self.driver.find_element(By.ID, form_id)
                            element.clear()
                            element.send_keys(visitor_data[field_name])
                            self.logger.info(f"Filled {field_name}: {visitor_data[field_name]}")
                    except Exception as e:
                        self.logger.warning(f"Could not fill field {field_name} ({form_id}): {str(e)}")
            
            await self.update_progress(35, "Handling phone numbers...")
            
            # Handle mobile number with international selector
            if 'mobile' in visitor_data and visitor_data['mobile']:
                await self._fill_international_phone('mobileNumberPlaceholder', visitor_data['mobile'])
            
            # Handle alternative number with international selector  
            if 'alt_number' in visitor_data and visitor_data['alt_number']:
                await self._fill_international_phone('alternativeNumberPlaceholder', visitor_data['alt_number'])
            
            await self.update_progress(45, "Setting checkboxes...")
            
            # Handle checkbox fields
            checkbox_mappings = {
                'first_nations': 'firstNations1',
                'disability': 'peopleOfDetermination1'  # Note: form uses 'peopleOfDetermination1'
            }
            
            for field_name, checkbox_id in checkbox_mappings.items():
                if field_name in visitor_data:
                    try:
                        checkbox = self.driver.find_element(By.ID, checkbox_id)
                        should_check = visitor_data[field_name] in ['true', True, 'Yes', 'yes', '1', 1]
                        
                        if should_check and not checkbox.is_selected():
                            checkbox.click()
                            self.logger.info(f"Checked {field_name}")
                        elif not should_check and checkbox.is_selected():
                            checkbox.click()
                            self.logger.info(f"Unchecked {field_name}")
                    except Exception as e:
                        self.logger.warning(f"Could not handle checkbox {field_name} ({checkbox_id}): {str(e)}")
            
            await self.update_progress(55, "Setting dropdown selections...")
            
            # Handle dropdown/select fields
            dropdown_mappings = {
                'nationality': ('id', 'nationality'),
                'country_of_issue': ('id', 'countryOfIssue'), 
                'reason_for_visit': ('name', 'visitReasonId')  # This field uses name, not id
            }
            
            for field_name, (locator_type, selector) in dropdown_mappings.items():
                if field_name in visitor_data and visitor_data[field_name]:
                    try:
                        if locator_type == 'id':
                            select_element = self.driver.find_element(By.ID, selector)
                        else:
                            select_element = self.driver.find_element(By.NAME, selector)
                        select = Select(select_element)
                        
                        # Try to select by visible text first
                        try:
                            select.select_by_visible_text(visitor_data[field_name])
                            self.logger.info(f"Selected {field_name} by text: {visitor_data[field_name]}")
                        except:
                            # Try to select by value
                            try:
                                select.select_by_value(visitor_data[field_name])
                                self.logger.info(f"Selected {field_name} by value: {visitor_data[field_name]}")
                            except:
                                # Try partial match
                                options = select.options
                                for option in options:
                                    if visitor_data[field_name].lower() in option.text.lower():
                                        select.select_by_visible_text(option.text)
                                        self.logger.info(f"Selected {field_name} by partial match: {option.text}")
                                        break
                    except Exception as e:
                        self.logger.warning(f"Could not set dropdown {field_name} ({selector}): {str(e)}")
            
            await self.update_progress(70, "Processing file uploads...")
            
            # Handle file uploads using Uppy interface
            if files:
                await self._handle_file_uploads(files)
            
            await self.update_progress(85, "Form filling completed")
            self.logger.info("Visitor form filling completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error filling visitor form: {str(e)}")
            raise

    async def _fill_international_phone(self, input_id, phone_number):
        """Fill international phone number using the intl-tel-input widget."""
        try:
            # The phone number might come in various formats
            # For now, just put the full number in the input field
            phone_input = self.driver.find_element(By.ID, input_id)
            phone_input.clear()
            phone_input.send_keys(phone_number)
            self.logger.info(f"Filled phone number {input_id}: {phone_number}")
            
            # The intl-tel-input library should handle country detection automatically
            time.sleep(1)  # Give it time to process
            
        except Exception as e:
            self.logger.warning(f"Could not fill international phone {input_id}: {str(e)}")

    async def _handle_file_uploads(self, files):
        """Handle file uploads using the Uppy interface."""
        try:
            file_mappings = {
                'photo_upload': 'photo',
                'signature_upload': 'signature', 
                'id_document_upload': 'copyOfId'
            }
            
            for file_key, uppy_field_id in file_mappings.items():
                if file_key in files:
                    file_info = files[file_key]
                    await self._upload_file_to_uppy(uppy_field_id, file_info)
                    
        except Exception as e:
            self.logger.error(f"Error handling file uploads: {str(e)}")
            # Don't raise exception for file upload errors - continue with form submission

    async def _upload_file_to_uppy(self, field_id, file_info):
        """Upload a file to an Uppy widget exactly like the HTML site."""
        try:
            self.logger.info(f"Uploading file for {field_id}: {file_info.get('filename', 'unknown')} ({len(file_info.get('file_data', b''))} bytes)")
            
            # Find the Uppy widget container
            uppy_container_id = f"uppy-{field_id}"
            
            # Wait for Uppy container to be available
            uppy_container = None
            for attempt in range(10):
                try:
                    uppy_container = self.driver.find_element(By.ID, uppy_container_id)
                    if uppy_container:
                        break
                except:
                    time.sleep(0.5)
                    
            if not uppy_container:
                self.logger.error(f"Could not find Uppy container: {uppy_container_id}")
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
                pass
            
            # Look for the file input within the Uppy widget
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
                self.logger.error(f"Could not find file input in Uppy container: {uppy_container_id}")
                return False
            
            # Create a temporary file with the uploaded content
            file_extension = os.path.splitext(file_info['filename'])[1] if file_info.get('filename') else '.tmp'
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_info['file_data'])
                temp_file_path = temp_file.name
            
            try:
                # Upload the file using the file input
                file_input.send_keys(temp_file_path)
                self.logger.info(f"File uploaded to Uppy for {field_id}")
                
                # Quick wait for upload processing (optimized for speed)
                time.sleep(1.5)  # Reduced wait time
                
                # Quick verification - don't wait too long
                for attempt in range(3):  # Only 3 attempts = 3 seconds max
                    try:
                        # Check if file appears in dashboard (quick check)
                        uploaded_files = uppy_container.find_elements(By.CSS_SELECTOR, 
                            '.uppy-Dashboard-Item, .uppy-Dashboard-files .uppy-Dashboard-Item')
                        if uploaded_files:
                            self.logger.info(f"File appears in dashboard for {field_id}")
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
                            self.logger.info(f" Clicked Save button for {field_id}")
                            time.sleep(1)  # Quick save wait
                            break
                    except:
                        continue
                
                # Verify the upload by checking for uploaded file items
                uploaded_files = uppy_container.find_elements(By.CSS_SELECTOR, '.uppy-Dashboard-Item, .uppy-Dashboard-files .uppy-Dashboard-Item')
                
                # Also check the hidden input field
                hidden_input_value = None
                try:
                    hidden_input = self.driver.find_element(By.ID, field_id)
                    hidden_input_value = hidden_input.get_attribute('value')
                except:
                    pass
                
                success = len(uploaded_files) > 0 or (hidden_input_value and hidden_input_value.strip())
                
                if success:
                    self.logger.info(f" File upload verified for {field_id}: {file_info['filename']}")
                else:
                    self.logger.warning(f" File upload verification failed for {field_id}")
                
                return success
                
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Could not upload file for {field_id}: {str(e)}")
            import traceback
            self.logger.warning(f"Traceback: {traceback.format_exc()}")
            return False
