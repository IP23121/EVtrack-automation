from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from utils.selenium_utils import wait_for_element, click_element, fill_text_field
from models.visitor import CredentialData
import time

class CredentialAutomation:
    def __init__(self, driver):
        self.driver = driver
        
    def search_and_navigate_to_visitor(self, search_term: str):
        """Search for a visitor and navigate to their profile page - same pattern as invitation and vehicles"""
        try:
            # Navigate directly to visitor list (skip dashboard)
            self.driver.get('https://app.evtrack.com/visitor/list')
            time.sleep(3)
            
            # Find search bar and enter search term
            search_input = None
            search_selectors = [
                'input[type="search"]',
                '.search-input',
                '#search',
                'input[placeholder*="search" i]',
                'input[name*="search" i]',
                '.dataTables_filter input',
                'input[aria-label*="search" i]'
            ]
            
            for selector in search_selectors:
                try:
                    search_input = wait_for_element(self.driver, By.CSS_SELECTOR, selector, timeout=3)
                    if search_input:
                        break
                except:
                    continue
            
            if not search_input:
                print("Could not find search input")
                return None
                
            # Clear and search
            search_input.clear()
            search_input.send_keys(search_term)
            time.sleep(2)
            
            # Press Enter
            from selenium.webdriver.common.keys import Keys
            search_input.send_keys(Keys.ENTER)
            time.sleep(3)
            
            # Find and click the first visitor result
            visitor_link = None
            visitor_uuid = None
            
            link_selectors = [
                'tbody tr td a',
                'tr a[href*="uuid="]',
                '.dataTables_wrapper tbody tr td:first-child a',
                'a[href*="/visitor/edit?uuid="]',
                '.visitor-row a',
                'table tbody tr td:first-child a',
                'tbody tr:first-child td:first-child a'
            ]
            
            for selector in link_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if links:
                        visitor_link = links[0]
                        href = visitor_link.get_attribute('href')
                        
                        # Extract UUID immediately if possible
                        if 'uuid=' in href:
                            visitor_uuid = href.split('uuid=')[1].split('&')[0]
                        
                        break
                except Exception as e:
                    continue
            
            if not visitor_link:
                print(f"Could not find visitor with search term: {search_term}")
                return None
                
            # Click to go to visitor profile
            visitor_link.click()
            time.sleep(3)
            
            # If we didn't get UUID from href, get it from current URL
            if not visitor_uuid:
                current_url = self.driver.current_url
                if 'uuid=' in current_url:
                    visitor_uuid = current_url.split('uuid=')[1].split('&')[0]
            
            print(f"Navigated to visitor profile, UUID: {visitor_uuid}")
            return visitor_uuid
                
        except Exception as e:
            print(f"Error searching for visitor: {e}")
            return None
        
    def search_visitor_for_credentials(self, search_term: str):
        """Legacy method - searches and returns UUID and URL"""
        uuid = self.search_and_navigate_to_visitor(search_term)
        if uuid:
            return uuid, self.driver.current_url
        return None, None

    def add_credential_to_visitor(self, credential_data: CredentialData):
        """Add a credential to the currently loaded visitor profile - follows exact HTML structure"""
        try:
            print("Adding credential to visitor profile...")
            
            # Verify we're on the correct page
            if 'visitor/edit' not in self.driver.current_url:
                print(f"ERROR: Not on visitor edit page! Current URL: {self.driver.current_url}")
                return False
            
            # Step 1: Click on Credentials tab
            print("Step 1: Clicking Credentials tab...")
            
            credentials_tab = wait_for_element(self.driver, By.CSS_SELECTOR, 'a[href="#credentials"][data-toggle="tab"]', timeout=10)
            if not credentials_tab:
                credentials_tab = wait_for_element(self.driver, By.CSS_SELECTOR, 'a[href="#credentials"]', timeout=5)
            
            if credentials_tab:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", credentials_tab)
                time.sleep(1)
                
                try:
                    credentials_tab.click()
                except Exception as e:
                    self.driver.execute_script("arguments[0].click();", credentials_tab)
                
                time.sleep(2)
                
                # Check if we're still on the same page
                if 'visitor/edit' not in self.driver.current_url:
                    print(f"ERROR: After clicking credentials tab, we're no longer on visitor edit page!")
                    return False
                
                print("Successfully clicked Credentials tab")
            else:
                print("Could not find Credentials tab")
                return False
            
            # Step 2: Click "Add" button
            print("Step 2: Clicking Add button...")
            
            add_btn = wait_for_element(self.driver, By.CSS_SELECTOR, 'button.dt-button.btn.btn-primary', timeout=10)
            if add_btn:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", add_btn)
                time.sleep(1)
                
                try:
                    add_btn.click()
                except Exception as e:
                    self.driver.execute_script("arguments[0].click();", add_btn)
                
                time.sleep(3)
                
                # Check if we're still on the same page or properly redirected to add form
                current_url = self.driver.current_url
                if 'visitor/list' in current_url:
                    print(f"ERROR: After clicking add button, we were redirected to visitor list!")
                    return False
                
                print("Successfully clicked Add button")
            else:
                print("Could not find Add button")
                return False
            
            # Step 3: Fill in the credential form
            print("Step 3: Filling credential form...")
            
            # Reader Type
            if credential_data.reader_type:
                reader_type_field = wait_for_element(self.driver, By.NAME, 'readerType', timeout=10)
                if reader_type_field:
                    select = Select(reader_type_field)
                    select.select_by_value(credential_data.reader_type)
                    print(f"Selected Reader Type: {credential_data.reader_type}")
                else:
                    print("Could not find Reader Type field")
            
            # Card#/LPR/UID (REQUIRED FIELD)
            if credential_data.unique_identifier:
                unique_id_field = None
                unique_id_selectors = [
                    'uniqueIdentifier', 'cardNumber', 'card_number', 'lpr', 'uid', 'credentialId', 'credential_id'
                ]
                
                # Try ID selectors first
                for selector in unique_id_selectors:
                    try:
                        unique_id_field = wait_for_element(self.driver, By.ID, selector, timeout=3)
                        if unique_id_field:
                            break
                    except:
                        continue
                
                # If not found by ID, try by name attribute
                if not unique_id_field:
                    for selector in unique_id_selectors:
                        try:
                            unique_id_field = wait_for_element(self.driver, By.NAME, selector, timeout=3)
                            if unique_id_field:
                                break
                        except:
                            continue
                
                # If still not found, try CSS selectors for input fields with placeholder text
                if not unique_id_field:
                    css_selectors = [
                        'input[placeholder*="Card" i]',
                        'input[placeholder*="LPR" i]', 
                        'input[placeholder*="UID" i]',
                        'input[placeholder*="Unique" i]',
                        'input[placeholder*="Identifier" i]'
                    ]
                    
                    for selector in css_selectors:
                        try:
                            unique_id_field = wait_for_element(self.driver, By.CSS_SELECTOR, selector, timeout=3)
                            if unique_id_field:
                                break
                        except:
                            continue
                
                if unique_id_field:
                    unique_id_field.clear()
                    time.sleep(0.5)
                    unique_id_field.send_keys(credential_data.unique_identifier)
                    time.sleep(0.5)
                    
                    # Verify the value was entered
                    entered_value = unique_id_field.get_attribute('value')
                    
                    if entered_value == credential_data.unique_identifier:
                        print(f"✓ Successfully filled Card#/LPR/UID: {credential_data.unique_identifier}")
                    else:
                        print(f"⚠ WARNING: Value mismatch! Retrying...")
                        unique_id_field.click()
                        time.sleep(0.5)
                        unique_id_field.clear()
                        time.sleep(0.5)
                        unique_id_field.send_keys(credential_data.unique_identifier)
                        time.sleep(0.5)
                        
                        entered_value = unique_id_field.get_attribute('value')
                        if entered_value != credential_data.unique_identifier:
                            print(f"ERROR: Still unable to fill field correctly after retry!")
                            return False
                else:
                    print("ERROR: Could not find Card#/LPR/UID field")
                    return False
            else:
                print("ERROR: No unique_identifier provided! This is a required field.")
                return False
            
            # PIN
            if credential_data.pin:
                pin_field = wait_for_element(self.driver, By.NAME, 'pin', timeout=5)
                if pin_field:
                    pin_field.clear()
                    pin_field.send_keys(str(credential_data.pin))
                    print(f"Filled PIN: {credential_data.pin}")
            
            # Active Date and Time
            if credential_data.active_date:
                active_date_field = wait_for_element(self.driver, By.ID, 'activeDatePlaceholder', timeout=5)
                if active_date_field:
                    active_date_field.clear()
                    active_date_field.send_keys(credential_data.active_date)
                    print(f"Filled Active Date: {credential_data.active_date}")
            
            if credential_data.active_time:
                active_time_field = wait_for_element(self.driver, By.ID, 'activeTimePlaceholder', timeout=5)
                if active_time_field:
                    active_time_field.clear()
                    active_time_field.send_keys(credential_data.active_time)
                    print(f"Filled Active Time: {credential_data.active_time}")
            
            # Expiry Date and Time
            if credential_data.expiry_date:
                expiry_date_field = wait_for_element(self.driver, By.ID, 'expiryDatePlaceholder', timeout=5)
                if expiry_date_field:
                    expiry_date_field.clear()
                    expiry_date_field.send_keys(credential_data.expiry_date)
                    print(f"Filled Expiry Date: {credential_data.expiry_date}")
            
            if credential_data.expiry_time:
                expiry_time_field = wait_for_element(self.driver, By.ID, 'expiryTimePlaceholder', timeout=5)
                if expiry_time_field:
                    expiry_time_field.clear()
                    expiry_time_field.send_keys(credential_data.expiry_time)
                    print(f"Filled Expiry Time: {credential_data.expiry_time}")
            
            # Use Limit
            if credential_data.use_limit:
                use_limit_field = wait_for_element(self.driver, By.NAME, 'useLimit', timeout=5)
                if use_limit_field:
                    use_limit_field.clear()
                    use_limit_field.send_keys(str(credential_data.use_limit))
                    print(f"Filled Use Limit: {credential_data.use_limit}")
            
            # Comments
            if credential_data.comments:
                comments_field = wait_for_element(self.driver, By.NAME, 'comments', timeout=5)
                if comments_field:
                    comments_field.clear()
                    comments_field.send_keys(credential_data.comments)
                    print(f"Filled Comments: {credential_data.comments}")
            
            # Status
            if credential_data.status:
                status_field = wait_for_element(self.driver, By.NAME, 'status', timeout=5)
                if status_field:
                    select = Select(status_field)
                    select.select_by_value(credential_data.status)
                    print(f"Selected Status: {credential_data.status}")
            
            # Access Control List checkbox
            if hasattr(credential_data, 'access_control_lists') and credential_data.access_control_lists is not None:
                checkbox = wait_for_element(self.driver, By.ID, 'accessControlListsIntegerArray1', timeout=5)
                if checkbox:
                    if credential_data.access_control_lists and not checkbox.is_selected():
                        checkbox.click()
                        print("Checked Access Control List")
                    elif not credential_data.access_control_lists and checkbox.is_selected():
                        checkbox.click()
                        print("Unchecked Access Control List")
            
            # Step 4: Click Save button
            print("Step 4: Clicking Save button...")
            save_btn = wait_for_element(self.driver, By.CSS_SELECTOR, 'button[type="submit"][value="save"]', timeout=10)
            if not save_btn:
                save_btn = wait_for_element(self.driver, By.CSS_SELECTOR, 'button[name="action"][value="save"]', timeout=5)
                
            if save_btn:
                save_btn.click()
                time.sleep(4)
                print("Successfully clicked Save button")
                
                current_url = self.driver.current_url
                if 'visitor/edit' in current_url:
                    print("Successfully saved credential - redirected to visitor page")
                    return True
                else:
                    print(f"Form submitted, current URL: {current_url}")
                    return True
            else:
                print("Could not find Save button")
                return False
                
        except Exception as e:
            print(f"Error adding credential to visitor: {e}")
            return False

    def add_credential(self, search_term: str, credential_data: CredentialData):
        """Main method: Search for visitor and add credential"""
        try:
            # Check if search_term is a UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
            is_uuid = len(search_term) == 36 and search_term.count('-') == 4
            
            # If search_term is a UUID, navigate directly to that visitor
            if is_uuid:
                self.driver.get(f'https://app.evtrack.com/visitor/edit?uuid={search_term}')
                time.sleep(3)
                visitor_uuid = search_term
            else:
                # If search_term is a name, need to search
                visitor_uuid = self.search_and_navigate_to_visitor(search_term)
            
            if not visitor_uuid:
                print(f"Could not find visitor with search term: {search_term}")
                return False
            
            # Verify we're on the visitor edit page
            if 'visitor/edit' not in self.driver.current_url or visitor_uuid not in self.driver.current_url:
                print(f"ERROR: After navigation, we're not on the correct visitor edit page!")
                return False
            
            # Add credential to the visitor profile
            success = self.add_credential_to_visitor(credential_data)
            return success
            
        except Exception as e:
            print(f"Error in add_credential: {e}")
            return False

    # Keep original method for backward compatibility
    def add_credential_legacy(self, visitor_uuid: str, credential_data: CredentialData):
        """Legacy method: Add a credential to a visitor's profile using UUID"""
        try:
            # Navigate to visitor edit page with UUID
            self.driver.get(f'https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}')
            time.sleep(4)
            
            # Click on Credentials tab
            credentials_tab = wait_for_element(self.driver, By.CSS_SELECTOR, 'a[href="#credentials"]', timeout=10)
            if not credentials_tab:
                # Try alternative selectors for credentials tab
                tab_selectors = [
                    '.nav-tabs a[data-toggle="tab"][href="#credentials"]',
                    '//a[contains(@href, "#credentials") or contains(text(), "Credentials")]',
                    'li a[href="#credentials"]',
                    '.nav-link[href="#credentials"]'
                ]
                for selector in tab_selectors:
                    try:
                        if selector.startswith('//'):
                            credentials_tab = self.driver.find_element(By.XPATH, selector)
                        else:
                            credentials_tab = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if credentials_tab:
                            break
                    except:
                        continue
            
            if credentials_tab:
                credentials_tab.click()
                time.sleep(3)
                
                # Click "Add" button for credentials
                print("Looking for Add credential button...")
                add_btn = None
                
                # Wait a bit for the tab content to fully load
                time.sleep(2)
                
                # Try different approaches to find and click the Add button
                add_btn_selectors = [
                    'button.dt-button.btn.btn-primary',
                    'button[type="button"].btn.btn-primary',
                    '.dt-buttons button.btn-primary',
                    'button:contains("Add")',
                    '.btn-primary'
                ]
                
                for selector in add_btn_selectors:
                    try:
                        if ':contains(' in selector:
                            # Use XPath for text-based selection
                            xpath = f'//button[contains(text(), "Add") and contains(@class, "btn")]'
                            add_btn = self.driver.find_element(By.XPATH, xpath)
                        else:
                            add_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if add_btn and add_btn.is_displayed() and add_btn.is_enabled():
                            print(f"Found Add button with selector: {selector}")
                            # Scroll to button to ensure it's in view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", add_btn)
                            time.sleep(1)
                            
                            # Try clicking with JavaScript if regular click fails
                            try:
                                add_btn.click()
                                print("Clicked Add button successfully")
                                break
                            except:
                                print("Regular click failed, trying JavaScript click")
                                self.driver.execute_script("arguments[0].click();", add_btn)
                                print("JavaScript click successful")
                                break
                    except Exception as e:
                        print(f"Selector {selector} failed: {e}")
                        continue
                
                if add_btn:
                    time.sleep(3)
                    
                    # Fill credential form fields
                    def safe_fill_field(field_selector, field_value, field_name, field_type="input"):
                        """Safely fill a field with error handling"""
                        if not field_value:
                            return True
                            
                        try:
                            if field_type == "select":
                                element = self.driver.find_element(By.ID, field_selector)
                                select = Select(element)
                                select.select_by_value(field_value)
                                print(f"Successfully selected {field_name}: {field_value}")
                                return True
                            else:
                                element = self.driver.find_element(By.ID, field_selector)
                                if element and element.is_displayed():
                                    element.clear()
                                    element.send_keys(str(field_value))
                                    print(f"Successfully filled {field_name}: {field_value}")
                                    return True
                        except Exception as e:
                            print(f"Failed to fill {field_name}: {e}")
                            return False
                        
                        print(f"Could not fill field {field_name}")
                        return False
                    
                    # Reader Type (required selection)
                    if credential_data.reader_type:
                        safe_fill_field('readerType', credential_data.reader_type, 'Reader Type', 'select')
                    
                    # Card#/LPR/UID
                    if credential_data.unique_identifier:
                        # Try multiple approaches to fill the unique identifier field
                        success = False
                        unique_id_selectors = ['uniqueIdentifier', 'cardNumber', 'card_number', 'lpr', 'uid', 'credentialId', 'credential_id']
                        
                        for selector in unique_id_selectors:
                            success = safe_fill_field(selector, credential_data.unique_identifier, 'Card#/LPR/UID')
                            if success:
                                break
                        
                        # If still not successful, try by name attribute
                        if not success:
                            for selector in unique_id_selectors:
                                try:
                                    element = self.driver.find_element(By.NAME, selector)
                                    if element and element.is_displayed():
                                        element.clear()
                                        element.send_keys(str(credential_data.unique_identifier))
                                        print(f"Successfully filled Card#/LPR/UID (by name): {credential_data.unique_identifier}")
                                        success = True
                                        break
                                except:
                                    continue
                        
                        if not success:
                            print("ERROR: Could not find or fill Card#/LPR/UID field")
                    
                    # PIN
                    if credential_data.pin:
                        safe_fill_field('pin', credential_data.pin, 'PIN')
                    
                    # Active Date (if provided)
                    if credential_data.active_date:
                        # Split date and time if provided in format "YYYY-MM-DD HH:MM:SS"
                        if ' ' in credential_data.active_date:
                            date_part, time_part = credential_data.active_date.split(' ', 1)
                            time_part = time_part[:5]  # Get HH:MM only
                        else:
                            date_part = credential_data.active_date
                            time_part = "00:00"
                        
                        safe_fill_field('activeDatePlaceholder', date_part, 'Active Date')
                        safe_fill_field('activeTimePlaceholder', time_part, 'Active Time')
                    
                    # Expiry Date (if provided)
                    if credential_data.expiry_date:
                        # Split date and time if provided in format "YYYY-MM-DD HH:MM:SS"
                        if ' ' in credential_data.expiry_date:
                            date_part, time_part = credential_data.expiry_date.split(' ', 1)
                            time_part = time_part[:5]  # Get HH:MM only
                        else:
                            date_part = credential_data.expiry_date
                            time_part = "23:59"
                        
                        safe_fill_field('expiryDatePlaceholder', date_part, 'Expiry Date')
                        safe_fill_field('expiryTimePlaceholder', time_part, 'Expiry Time')
                    
                    # Use Limit
                    if credential_data.use_limit:
                        safe_fill_field('useLimit', str(credential_data.use_limit), 'Use Limit')
                    
                    # Comments
                    if credential_data.comments:
                        safe_fill_field('comments', credential_data.comments, 'Comments')
                    
                    # Status (default is ACTIVE)
                    if credential_data.status:
                        safe_fill_field('status', credential_data.status, 'Status', 'select')
                    
                    # Access Control List checkbox (default is checked)
                    if credential_data.access_control_lists is not None:
                        try:
                            checkbox = self.driver.find_element(By.ID, 'accessControlListsIntegerArray1')
                            if credential_data.access_control_lists and not checkbox.is_selected():
                                checkbox.click()
                                print("Checked Access Control List")
                            elif not credential_data.access_control_lists and checkbox.is_selected():
                                checkbox.click()
                                print("Unchecked Access Control List")
                        except Exception as e:
                            print(f"Error handling Access Control List checkbox: {e}")
                    
                    # Click Save button
                    print("Looking for save button...")
                    save_btn = None
                    save_selectors = [
                        'button[value="save"]',
                        'button#submitBtn',
                        'button[type="submit"]:contains("Save")',
                        'button.btn-primary[name="action"][value="save"]',
                        '.btn-primary:contains("Save")'
                    ]
                    
                    for selector in save_selectors:
                        try:
                            save_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if save_btn and save_btn.is_displayed():
                                print(f"Found save button with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if save_btn:
                        print("Clicking save button...")
                        save_btn.click()
                        time.sleep(5)
                        
                        # Check for success indicators
                        success_indicators = [
                            '.alert-success',
                            '.success-message',
                            '.notification-success',
                            '[class*="success"]'
                        ]
                        
                        # Also check if we're still on the same page (might indicate success)
                        current_url = self.driver.current_url
                        if 'visitor/edit' in current_url and visitor_uuid in current_url:
                            print("Credential likely added successfully (stayed on visitor page)")
                            return True
                        
                        for indicator in success_indicators:
                            try:
                                success_element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                                if success_element and success_element.is_displayed():
                                    print("Credential added successfully!")
                                    return True
                            except:
                                continue
                        
                        return True  # Assume success if no error found
                    else:
                        print("Save button not found")
                        return False
                else:
                    print("Add credential button not found")
                    return False
            else:
                print("Credentials tab not found")
                return False
                
        except Exception as e:
            print(f"Error adding credential: {e}")
            return False

    def update_credential(self, search_term: str, credential_search_detail: str, credential_data: CredentialData):
        """Update an existing credential for a visitor using search term and credential search detail"""
        try:
            # Check if search_term is a UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
            is_uuid = len(search_term) == 36 and search_term.count('-') == 4
            
            # If search_term is a UUID, navigate directly to that visitor
            if is_uuid:
                self.driver.get(f'https://app.evtrack.com/visitor/edit?uuid={search_term}')
                time.sleep(3)
                visitor_uuid = search_term
            else:
                # If search_term is a name, need to search
                visitor_uuid = self.search_and_navigate_to_visitor(search_term)
            
            if not visitor_uuid:
                print(f"Could not find visitor with search term: {search_term}")
                return False
            
            # Verify we're on the visitor edit page
            if 'visitor/edit' not in self.driver.current_url or visitor_uuid not in self.driver.current_url:
                print(f"ERROR: After navigation, we're not on the correct visitor edit page!")
                return False
            
            # Step 1: Click on Credentials tab
            print("Step 1: Clicking Credentials tab...")
            credentials_tab = wait_for_element(self.driver, By.CSS_SELECTOR, 'a[href="#credentials"][data-toggle="tab"]', timeout=10)
            if not credentials_tab:
                credentials_tab = wait_for_element(self.driver, By.CSS_SELECTOR, 'a[href="#credentials"]', timeout=5)
            
            if credentials_tab:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", credentials_tab)
                time.sleep(1)
                
                try:
                    credentials_tab.click()
                except Exception as e:
                    self.driver.execute_script("arguments[0].click();", credentials_tab)
                
                time.sleep(3)
                print("Successfully clicked Credentials tab")
            else:
                print("Could not find Credentials tab")
                return False
            
            # Step 2: Search for the specific credential
            print(f"Step 2: Searching for credential with detail: '{credential_search_detail}'")
            
            search_input = wait_for_element(self.driver, By.CSS_SELECTOR, 'input[type="search"][aria-controls="credentialsListTable"]', timeout=10)
            if not search_input:
                search_selectors = [
                    'input[type="search"]',
                    '.dataTables_filter input',
                    'input[placeholder*="search" i]',
                    'input[aria-controls*="credential" i]'
                ]
                
                for selector in search_selectors:
                    try:
                        search_input = wait_for_element(self.driver, By.CSS_SELECTOR, selector, timeout=3)
                        if search_input:
                            break
                    except:
                        continue
            
            if search_input:
                search_input.clear()
                search_input.send_keys(credential_search_detail)
                time.sleep(2)
                
                from selenium.webdriver.common.keys import Keys
                search_input.send_keys(Keys.ENTER)
                time.sleep(3)
                print("Performed credential search")
            else:
                print("Could not find credential search input")
                return False
            
            # Step 3: Click the checkbox to select the credential
            print("Step 3: Selecting credential with checkbox...")
            
            checkbox = wait_for_element(self.driver, By.CSS_SELECTOR, 'td.select-checkbox', timeout=10)
            if not checkbox:
                checkbox_selectors = [
                    'td.select-checkbox',
                    '.select-checkbox',
                    'input[type="checkbox"]',
                    'td:first-child'
                ]
                
                for selector in checkbox_selectors:
                    try:
                        checkbox = wait_for_element(self.driver, By.CSS_SELECTOR, selector, timeout=3)
                        if checkbox:
                            break
                    except:
                        continue
            
            if checkbox:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", checkbox)
                time.sleep(1)
                
                try:
                    checkbox.click()
                except Exception as e:
                    self.driver.execute_script("arguments[0].click();", checkbox)
                
                time.sleep(2)
                print("Successfully selected credential")
            else:
                print("Could not find credential checkbox to select")
                return False
            
            # Step 4: Click the "Edit" button
            print("Step 4: Clicking Edit button...")
            
            edit_btn = wait_for_element(self.driver, By.CSS_SELECTOR, 'button.dt-button.btn.btn-success', timeout=10)
            if not edit_btn:
                edit_selectors = [
                    'button.dt-button.btn.btn-success',
                    'button:contains("Edit")',
                    '.btn-success',
                    'button[tabindex="0"][aria-controls="credentialsListTable"]'
                ]
                
                for selector in edit_selectors:
                    try:
                        if ':contains(' in selector:
                            xpath = f'//button[contains(text(), "Edit") and contains(@class, "btn")]'
                            edit_btn = self.driver.find_element(By.XPATH, xpath)
                        else:
                            edit_btn = wait_for_element(self.driver, By.CSS_SELECTOR, selector, timeout=3)
                        
                        if edit_btn:
                            break
                    except:
                        continue
            
            if edit_btn:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", edit_btn)
                time.sleep(1)
                
                try:
                    edit_btn.click()
                except Exception as e:
                    self.driver.execute_script("arguments[0].click();", edit_btn)
                
                time.sleep(3)
                print("Successfully clicked Edit button")
            else:
                print("Could not find Edit button")
                return False
            
            # Step 5: Fill in the credential form with updated data
            print("Step 5: Updating credential form...")
            
            # Note: According to user requirements, these fields are read-only and cannot be edited:
            # - Holder (disabled)
            # - Credential Type (readonly)
            # - Reader Type (readonly)
            # - Card#/LPR/UID (readonly)
            # - PIN (disabled)
            # We will only update the editable fields
            
            # Active Date and Time
            if credential_data.active_date:
                active_date_field = wait_for_element(self.driver, By.ID, 'activeDatePlaceholder', timeout=5)
                if active_date_field:
                    active_date_field.clear()
                    active_date_field.send_keys(credential_data.active_date)
                    print(f"Updated Active Date: {credential_data.active_date}")
            
            if credential_data.active_time:
                active_time_field = wait_for_element(self.driver, By.ID, 'activeTimePlaceholder', timeout=5)
                if active_time_field:
                    active_time_field.clear()
                    active_time_field.send_keys(credential_data.active_time)
                    print(f"Updated Active Time: {credential_data.active_time}")
            
            # Expiry Date and Time
            if credential_data.expiry_date:
                expiry_date_field = wait_for_element(self.driver, By.ID, 'expiryDatePlaceholder', timeout=5)
                if expiry_date_field:
                    expiry_date_field.clear()
                    expiry_date_field.send_keys(credential_data.expiry_date)
                    print(f"Updated Expiry Date: {credential_data.expiry_date}")
            
            if credential_data.expiry_time:
                expiry_time_field = wait_for_element(self.driver, By.ID, 'expiryTimePlaceholder', timeout=5)
                if expiry_time_field:
                    expiry_time_field.clear()
                    expiry_time_field.send_keys(credential_data.expiry_time)
                    print(f"Updated Expiry Time: {credential_data.expiry_time}")
            
            # Use Limit
            if credential_data.use_limit:
                use_limit_field = wait_for_element(self.driver, By.ID, 'useLimit', timeout=5)
                if use_limit_field:
                    use_limit_field.clear()
                    use_limit_field.send_keys(str(credential_data.use_limit))
                    print(f"Updated Use Limit: {credential_data.use_limit}")
            
            # Comments
            if credential_data.comments:
                comments_field = wait_for_element(self.driver, By.ID, 'comments', timeout=5)
                if comments_field:
                    comments_field.clear()
                    comments_field.send_keys(credential_data.comments)
                    print(f"Updated Comments: {credential_data.comments}")
            
            # Status
            if credential_data.status:
                status_field = wait_for_element(self.driver, By.ID, 'status', timeout=5)
                if status_field:
                    select = Select(status_field)
                    select.select_by_value(credential_data.status)
                    print(f"Updated Status: {credential_data.status}")
            
            # Step 6: Click Save button
            print("Step 6: Clicking Save button...")
            save_btn = wait_for_element(self.driver, By.CSS_SELECTOR, 'button[type="submit"][value="save"]', timeout=10)
            if not save_btn:
                save_selectors = [
                    'button[type="submit"][value="save"]',
                    'button[name="action"][value="save"]',
                    'button:contains("Save")',
                    '.btn-primary[type="submit"]'
                ]
                
                for selector in save_selectors:
                    try:
                        if ':contains(' in selector:
                            xpath = f'//button[contains(text(), "Save") and @type="submit"]'
                            save_btn = self.driver.find_element(By.XPATH, xpath)
                        else:
                            save_btn = wait_for_element(self.driver, By.CSS_SELECTOR, selector, timeout=3)
                        
                        if save_btn:
                            break
                    except:
                        continue
            
            if save_btn:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", save_btn)
                time.sleep(1)
                
                try:
                    save_btn.click()
                except Exception as e:
                    self.driver.execute_script("arguments[0].click();", save_btn)
                
                time.sleep(4)
                print("Successfully clicked Save button")
                
                current_url = self.driver.current_url
                if 'visitor/edit' in current_url:
                    print("Successfully updated credential - redirected to visitor page")
                    return True
                else:
                    print(f"Form submitted, current URL: {current_url}")
                    return True
            else:
                print("Could not find Save button")
                return False
                
        except Exception as e:
            print(f"Error updating credential: {e}")
            return False
