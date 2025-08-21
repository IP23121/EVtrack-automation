from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
import logging
import time

logger = logging.getLogger(__name__)

class VehicleUpdateAutomation:
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

    async def update_vehicle(self, search_term, vehicle_data):
        """Update a vehicle following the exact EVTrack workflow."""
        try:
            await self.update_progress(0, "Starting vehicle update...")
            
            # Step 1: Navigate directly to the vehicle list page
            await self.update_progress(5, "Navigating to vehicle list...")
            self.driver.get('https://app.evtrack.com/vehicle/list')
            
            # Quick login check
            if '/login' in self.driver.current_url:
                raise Exception("Not logged in to EVTrack")
            
            # Wait for the vehicle list page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            await self.update_progress(15, f"Searching for vehicle: {search_term}")
            
            # Step 2: Enter search term in the search input
            try:
                search_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"].form-control.input-sm[aria-controls="listTable"]'))
                )
                search_input.clear()
                search_input.send_keys(search_term)
                search_input.send_keys(Keys.RETURN)
                self.logger.info(f"Entered search term: {search_term}")
                
                # Wait for search results to load
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Could not find or use search input: {str(e)}")
                raise Exception("Could not find or use vehicle search input")
            
            await self.update_progress(30, "Selecting vehicle from search results...")
            
            # Step 3: Click the checkbox of the first result
            try:
                # Wait for the table to update with search results
                time.sleep(2)
                
                # Find and click the first checkbox in the results
                checkbox = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'td.select-checkbox'))
                )
                checkbox.click()
                self.logger.info("Successfully clicked vehicle checkbox")
                
                # Wait a moment for selection to register
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Could not find or click vehicle checkbox: {str(e)}")
                raise Exception("Could not find or select vehicle from search results")
            
            await self.update_progress(45, "Opening vehicle for editing...")
            
            # Step 4: Click the Edit button
            try:
                edit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.dt-button.btn.btn-success[aria-controls="listTable"]'))
                )
                edit_button.click()
                self.logger.info("Successfully clicked Edit button")
                
                # Wait for the edit page to load
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Could not find or click Edit button: {str(e)}")
                raise Exception("Could not find or click Edit button")
            
            await self.update_progress(60, "Navigating to Detail tab...")
            
            # Step 5: Click on the Detail tab
            try:
                detail_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#detail"][data-toggle="tab"]'))
                )
                detail_tab.click()
                self.logger.info("Successfully clicked Detail tab")
                
                # Wait for the detail tab content to load
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Could not find or click Detail tab: {str(e)}")
                raise Exception("Could not find or click Detail tab")
            
            await self.update_progress(70, "Updating vehicle information...")
            
            # Step 6: Update the vehicle form with the provided data
            await self._update_vehicle_form(vehicle_data)
            
            await self.update_progress(90, "Saving vehicle updates...")
            
            # Step 7: Click the Save button
            try:
                save_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"][name="action"][value="save"]')
                save_button.click()
                self.logger.info("Successfully clicked Save button")
                
                # Wait for form submission to complete
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Could not find or click Save button: {str(e)}")
                raise Exception("Could not find or click Save button")
            
            await self.update_progress(95, "Processing vehicle update...")
            
            # Check if we're back on the vehicle list or if there are any errors
            current_url = self.driver.current_url
            if 'vehicle/list' in current_url or 'vehicle/edit' in current_url:
                await self.update_progress(100, "Vehicle updated successfully!")
                self.logger.info("Vehicle update appears successful")
                
                return {
                    'success': True,
                    'message': f"Vehicle updated successfully (searched by: {search_term})",
                    'search_term': search_term,
                    'vehicle_data': vehicle_data,
                    'updated_fields': [field for field in vehicle_data.keys() if vehicle_data[field]]
                }
            else:
                # Check for any error messages on the form
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, '.alert-danger, .error, .has-error')
                    if error_elements:
                        error_message = error_elements[0].text
                        self.logger.error(f"Form validation error: {error_message}")
                        raise Exception(f"Form validation failed: {error_message}")
                except:
                    pass
                
                await self.update_progress(100, "Vehicle update status unclear")
                self.logger.warning("Not on expected page after form submission")
                return {
                    'success': False,
                    'message': 'Vehicle update status unclear - form submitted but unexpected redirect',
                    'current_url': current_url
                }
                
        except Exception as e:
            await self.update_progress(100, f"Error: {str(e)}")
            self.logger.error(f"Error in update_vehicle: {str(e)}")
            raise

    async def _update_vehicle_form(self, vehicle_data):
        """Update the vehicle form fields with the provided data."""
        try:
            # Map frontend field names to EVTrack form field IDs based on the HTML you provided
            field_mappings = {
                'number_plate': 'vehicleRegistrationNumber',
                'vehicle_type': 'vehicleType', 
                'make': 'vehicleMake',
                'model': 'vehicleModel',
                'year': 'vehicleYear',
                'colour': 'vehicleColour',
                'vin': 'vehicleVin',
                'engine_number': 'engineNumber',
                'licence_disc_number': 'licenseNumber',
                'licence_expiry_date': 'licenseDateOfExpiry',
                'document_number': 'documentNumber',
                'comments': 'comments'
            }
            
            # Update only the fields that have values (don't clear existing data)
            updated_fields = []
            for field_name, form_id in field_mappings.items():
                if field_name in vehicle_data and vehicle_data[field_name]:
                    try:
                        element = self.driver.find_element(By.ID, form_id)
                        
                        if form_id == 'licenseDateOfExpiry':
                            # Special handling for date field
                            element.clear()
                            # Ensure date is in the correct format (yyyy-mm-dd)
                            date_value = vehicle_data[field_name]
                            if date_value:
                                element.send_keys(date_value)
                                updated_fields.append(field_name)
                                self.logger.info(f"Updated date field {field_name}: {date_value}")
                        else:
                            # Regular text/number input - clear and set new value
                            element.clear()
                            element.send_keys(str(vehicle_data[field_name]))
                            updated_fields.append(field_name)
                            self.logger.info(f"Updated {field_name}: {vehicle_data[field_name]}")
                            
                    except Exception as e:
                        self.logger.warning(f"Could not update field {field_name} ({form_id}): {str(e)}")
            
            if updated_fields:
                self.logger.info(f"Vehicle form update completed successfully. Updated fields: {updated_fields}")
            else:
                self.logger.info("No fields were updated (no valid data provided)")
            
        except Exception as e:
            self.logger.error(f"Error updating vehicle form: {str(e)}")
            raise
