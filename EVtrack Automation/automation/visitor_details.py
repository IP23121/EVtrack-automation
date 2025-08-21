from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
import time
import base64
import requests

logger = logging.getLogger(__name__)

class VisitorDetailsAutomation:
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

    async def get_comprehensive_visitor_profile(self, visitor_uuid):
        """
        Navigate to visitor profile and extract ALL profile tab data exactly as specified.
        This follows the exact route: search -> visitor profile -> profile tab -> extract everything.
        """
        try:
            await self.update_progress(0, "Navigating to visitor profile...")
            
            # Navigate directly to visitor edit page (this is the visitor profile)
            profile_url = f'https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}'
            self.driver.get(profile_url)
            
            # Quick login check
            if '/login' in self.driver.current_url:
                raise Exception("Not logged in")
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'form, .nav-tabs'))
            )
            
            await self.update_progress(20, "Navigating to Profile tab...")

            # Navigate to Profile tab exactly as specified in the HTML
            try:
                # Look for the profile tab using the exact HTML structure provided
                profile_tab_selectors = [
                    'a[href="#profile"][data-toggle="tab"]',
                    'a[href="#profile"]',
                    '//a[contains(@href, "#profile") and contains(@data-toggle, "tab")]',
                    '//a[contains(text(), "Profile")]'
                ]
                
                profile_tab_clicked = False
                for selector in profile_tab_selectors:
                    try:
                        if selector.startswith('//'):
                            profile_tab = self.driver.find_element(By.XPATH, selector)
                        else:
                            profile_tab = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        # Scroll into view and click
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", profile_tab)
                        time.sleep(0.5)
                        profile_tab.click()
                        time.sleep(2)
                        
                        self.logger.info(f"Successfully clicked Profile tab using selector: {selector}")
                        profile_tab_clicked = True
                        break
                        
                    except Exception as e:
                        self.logger.debug(f"Profile tab selector {selector} failed: {str(e)}")
                        continue
                
                if not profile_tab_clicked:
                    self.logger.warning("Could not find Profile tab - may already be active or page structure different")
                    
            except Exception as e:
                self.logger.warning(f"Error clicking Profile tab: {str(e)}")
            
            await self.update_progress(40, "Extracting profile data from form...")

            # Wait for the profile form to be visible
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "visitorProfileForm"))
                )
            except TimeoutException:
                # Form might have different ID or structure
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "form, .form-horizontal"))
                )

            # Initialize comprehensive profile data structure based on the HTML provided
            profile_data = {
                "basic_info": {},
                "contact_info": {},
                "personal_details": {},
                "visit_info": {},
                "metadata": {
                    "uuid": visitor_uuid,
                    "profile_url": profile_url
                },
                "documents": []
            }

            await self.update_progress(50, "Extracting basic information...")

            # Extract basic info fields exactly as they appear in the HTML
            basic_info_fields = {
                "initials": "initials",
                "first_name": "firstName",
                "last_name": "lastName", 
                "id_nr": "identityNr",
                "company": "company"
            }
            
            for field_name, field_id in basic_info_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    value = element.get_attribute("value") or ""
                    if value and value.strip():
                        profile_data["basic_info"][field_name] = value.strip()
                        self.logger.debug(f"Extracted {field_name}: {value.strip()}")
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")

            await self.update_progress(60, "Extracting contact information...")

            # Extract contact info
            contact_fields = {
                "email": "email",
                "address": "address"
            }
            
            for field_name, field_id in contact_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    if element.tag_name == "textarea":
                        value = element.text or element.get_attribute("value") or ""
                    else:
                        value = element.get_attribute("value") or ""
                    if value and value.strip():
                        profile_data["contact_info"][field_name] = value.strip()
                        self.logger.debug(f"Extracted {field_name}: {value.strip()}")
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")

            # Extract phone numbers from international phone input fields  
            phone_fields = {
                "mobile_number": "mobileNumberPlaceholder",
                "alt_number": "alternativeNumberPlaceholder"
            }
            
            for field_name, field_id in phone_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    value = element.get_attribute("value") or ""
                    if value and value.strip():
                        profile_data["contact_info"][field_name] = value.strip()
                        self.logger.debug(f"Extracted {field_name}: {value.strip()}")
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")

            await self.update_progress(70, "Extracting personal details...")

            # Extract personal details
            personal_detail_fields = {
                "date_of_birth": "dateOfBirth",
                "comments": "comments"
            }
            
            for field_name, field_id in personal_detail_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    if element.tag_name == "textarea":
                        value = element.text or element.get_attribute("value") or ""
                    else:
                        value = element.get_attribute("value") or ""
                    if value and value.strip():
                        if field_name == "comments":
                            profile_data["visit_info"][field_name] = value.strip()
                        else:
                            profile_data["personal_details"][field_name] = value.strip()
                        self.logger.debug(f"Extracted {field_name}: {value.strip()}")
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")

            # Extract checkbox fields exactly as in HTML
            checkbox_fields = {
                "first_nations": "firstNations1",
                "people_of_determination": "peopleOfDetermination1"
            }
            
            for field_name, field_id in checkbox_fields.items():
                try:
                    element = self.driver.find_element(By.ID, field_id)
                    is_checked = element.is_selected()
                    if is_checked:  # Only add if checked
                        profile_data["personal_details"][field_name] = "Yes"
                        self.logger.debug(f"Extracted {field_name}: Yes")
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")

            await self.update_progress(80, "Extracting dropdown selections...")

            # Extract dropdown/select fields
            select_fields = {
                "gender": ("gender", "basic_info"),
                "nationality": ("nationality", "personal_details"),
                "country_of_issue": ("countryOfIssue", "personal_details"),
                "reason_for_visit": ("647", "visit_info")  # Note: using the ID from HTML which shows selected option
            }
            
            for field_name, (field_id, category) in select_fields.items():
                try:
                    select_element = self.driver.find_element(By.ID, field_id)
                    selected_option = select_element.find_element(By.CSS_SELECTOR, "option:checked, option[selected]")
                    value = selected_option.text.strip()
                    # Skip default/empty values
                    if value and value not in ["None", "", "Select...", "Choose..."]:
                        profile_data[category][field_name] = value
                        self.logger.debug(f"Extracted {field_name}: {value}")
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")

            await self.update_progress(90, "Extracting document information...")

            # Extract document/file information and add to documents array
            file_fields = {
                "photo": "photo",
                "signature": "signature",
                "copy_of_id": "copyOfId"
            }
            
            for field_name, field_id in file_fields.items():
                try:
                    # Check if file exists by looking at hidden input value
                    hidden_input = self.driver.find_element(By.ID, field_id)
                    file_uuid = hidden_input.get_attribute("value") or ""
                    
                    if file_uuid and file_uuid.strip():
                        # Try to find the Uppy file display to get more info
                        try:
                            uppy_container = self.driver.find_element(By.CSS_SELECTOR, f"#uppy-{field_id}")
                            file_items = uppy_container.find_elements(By.CSS_SELECTOR, ".uppy-Dashboard-Item")
                            
                            if file_items:
                                # Extract file info from Uppy display
                                file_item = file_items[0]  # Get first file
                                try:
                                    file_name_element = file_item.find_element(By.CSS_SELECTOR, ".uppy-Dashboard-Item-name")
                                    file_name = file_name_element.get_attribute("title") or file_name_element.text
                                    
                                    file_size_element = file_item.find_element(By.CSS_SELECTOR, ".uppy-Dashboard-Item-statusSize")
                                    file_size = file_size_element.text
                                    
                                    document_info = {
                                        "name": file_name,
                                        "type": field_name.replace("_", " ").title(),
                                        "size": file_size,
                                        "uuid": file_uuid.strip(),
                                        "url": f"https://app.evtrack.com/api/files/{file_uuid.strip()}"
                                    }
                                    profile_data["documents"].append(document_info)
                                    self.logger.debug(f"Extracted {field_name}: {file_name} ({file_size})")
                                    
                                except Exception as inner_e:
                                    # Fallback if we can't get detailed info
                                    document_info = {
                                        "name": f"{field_name}_{file_uuid[:8]}.jpg",
                                        "type": field_name.replace("_", " ").title(),
                                        "uuid": file_uuid.strip(),
                                        "url": f"https://app.evtrack.com/api/files/{file_uuid.strip()}"
                                    }
                                    profile_data["documents"].append(document_info)
                                    self.logger.debug(f"Extracted {field_name}: Available (UUID: {file_uuid.strip()})")
                            else:
                                document_info = {
                                    "name": f"{field_name}_{file_uuid[:8]}",
                                    "type": field_name.replace("_", " ").title(),
                                    "uuid": file_uuid.strip(),
                                    "url": f"https://app.evtrack.com/api/files/{file_uuid.strip()}"
                                }
                                profile_data["documents"].append(document_info)
                                
                        except Exception as uppy_e:
                            # Fallback if Uppy container not found
                            document_info = {
                                "name": f"{field_name}_{file_uuid[:8]}",
                                "type": field_name.replace("_", " ").title(), 
                                "uuid": file_uuid.strip(),
                                "url": f"https://app.evtrack.com/api/files/{file_uuid.strip()}"
                            }
                            profile_data["documents"].append(document_info)
                            self.logger.debug(f"Extracted {field_name}: Available (UUID: {file_uuid.strip()})")
                            
                except Exception as e:
                    self.logger.debug(f"Could not extract {field_name}: {str(e)}")

            # Extract metadata fields
            try:
                user_id_element = self.driver.find_element(By.ID, "userId")
                user_id = user_id_element.get_attribute("value") or ""
                if user_id and user_id.strip():
                    profile_data["metadata"]["user_id"] = user_id.strip()
            except Exception as e:
                self.logger.debug(f"Could not extract user_id: {str(e)}")

            await self.update_progress(100, "Profile data extraction completed")

            # Count extracted fields for logging
            total_fields = 0
            populated_fields = 0
            
            for category, fields in profile_data.items():
                if isinstance(fields, dict):
                    for field_name, field_value in fields.items():
                        total_fields += 1
                        if field_value != "Not provided" and field_value != "":
                            populated_fields += 1

            self.logger.info(f"Profile extraction completed for UUID: {visitor_uuid}")
            self.logger.info(f"Extracted {populated_fields} populated fields out of {total_fields} total fields")

            return profile_data

        except Exception as e:
            self.logger.error(f"Error extracting comprehensive visitor profile: {str(e)}")
            await self.update_progress(100, "Failed to extract profile")
            raise
