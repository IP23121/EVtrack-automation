from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from .visitor_search import VisitorSearchAutomation
import logging
import time

logger = logging.getLogger(__name__)

class VehicleAddAutomation:
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

    async def add_vehicle(self, search_term, vehicle_data):
        """Add a vehicle to a visitor following the exact EVTrack workflow."""
        try:
            await self.update_progress(0, "Starting vehicle addition...")
            
            # Step 1: Search for the visitor using the same method as invite/badge
            await self.update_progress(5, f"Searching for visitor: {search_term}")
            
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
            
            await self.update_progress(20, f"Found visitor: {visitor_name}")
            
            # Step 2: Navigate to the visitor profile page
            await self.update_progress(25, "Navigating to visitor profile...")
            
            profile_url = f'https://app.evtrack.com/visitor/edit?uuid={visitor_uuid}'
            self.driver.get(profile_url)
            
            # Wait for the profile page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            await self.update_progress(35, "Profile page loaded, looking for vehicles tab...")
            
            # Step 3: Click on the Vehicles tab
            try:
                # Wait for and click the vehicles tab
                vehicles_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#vehicles"][data-toggle="tab"]'))
                )
                vehicles_tab.click()
                self.logger.info("Successfully clicked Vehicles tab")
                
                # Wait for vehicles tab content to load
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Could not find or click Vehicles tab: {str(e)}")
                raise Exception("Could not find or click Vehicles tab")
            
            await self.update_progress(45, "Vehicles tab opened, looking for Add Vehicle button...")
            
            # Step 4: Click the "Add Vehicle" button
            try:
                add_vehicle_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, 'vehicleListTableNew'))
                )
                add_vehicle_btn.click()
                self.logger.info("Successfully clicked Add Vehicle button")
                
                # Wait for the add vehicle form to appear
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Could not find or click Add Vehicle button: {str(e)}")
                raise Exception("Could not find or click Add Vehicle button")
            
            await self.update_progress(55, "Add Vehicle form opened, filling vehicle information...")
            
            # Step 5: Fill the vehicle form with the provided data
            await self._fill_vehicle_form(vehicle_data)
            
            await self.update_progress(85, "Vehicle information filled, submitting form...")
            
            # Step 6: Click the Save button
            try:
                save_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"][name="action"][value="save"]')
                save_button.click()
                self.logger.info("Successfully clicked Save button")
                
                # Wait for form submission to complete
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Could not find or click Save button: {str(e)}")
                raise Exception("Could not find or click Save button")
            
            await self.update_progress(95, "Processing vehicle addition...")
            
            # Check if we're back on the visitor profile page or if there are any errors
            current_url = self.driver.current_url
            if 'visitor/edit' in current_url and 'uuid=' in current_url:
                await self.update_progress(100, "Vehicle added successfully!")
                self.logger.info("Vehicle addition appears successful - still on visitor profile page")
                
                return {
                    'success': True,
                    'message': f"Vehicle added successfully to {visitor_name}",
                    'visitor_name': visitor_name,
                    'visitor_uuid': visitor_uuid,
                    'vehicle_data': vehicle_data
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
                
                await self.update_progress(100, "Vehicle addition status unclear")
                self.logger.warning("Not on expected page after form submission")
                return {
                    'success': False,
                    'message': 'Vehicle addition status unclear - form submitted but unexpected redirect',
                    'current_url': current_url
                }
                
        except Exception as e:
            await self.update_progress(100, f"Error: {str(e)}")
            self.logger.error(f"Error in add_vehicle: {str(e)}")
            raise

    async def _fill_vehicle_form(self, vehicle_data):
        """Fill the vehicle form fields with the provided data."""
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
            
            # Fill all the form fields
            for field_name, form_id in field_mappings.items():
                if field_name in vehicle_data and vehicle_data[field_name]:
                    try:
                        if form_id == 'licenseDateOfExpiry':
                            # Special handling for date field
                            element = self.driver.find_element(By.ID, form_id)
                            element.clear()
                            # Ensure date is in the correct format (yyyy-mm-dd)
                            date_value = vehicle_data[field_name]
                            if date_value:
                                element.send_keys(date_value)
                                self.logger.info(f"Filled date field {field_name}: {date_value}")
                        else:
                            # Regular text input
                            element = self.driver.find_element(By.ID, form_id)
                            element.clear()
                            element.send_keys(str(vehicle_data[field_name]))
                            self.logger.info(f"Filled {field_name}: {vehicle_data[field_name]}")
                            
                    except Exception as e:
                        self.logger.warning(f"Could not fill field {field_name} ({form_id}): {str(e)}")
            
            self.logger.info("Vehicle form filling completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error filling vehicle form: {str(e)}")
            raise
