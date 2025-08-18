from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from utils.selenium_utils import wait_for_element, click_element, fill_text_field
from models.visitor import VehicleData
from .vehicle_add import VehicleAddAutomation
from .vehicle_update import VehicleUpdateAutomation
import time
import logging

class VehicleAutomation:
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
        """Add a vehicle to a visitor using the new EVTrack workflow."""
        try:
            # Use the new VehicleAddAutomation class
            vehicle_add_automation = VehicleAddAutomation(self.driver)
            vehicle_add_automation.set_websocket(self.websocket)
            
            result = await vehicle_add_automation.add_vehicle(search_term, vehicle_data)
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding vehicle: {str(e)}")
            await self.update_progress(100, f"Failed to add vehicle: {str(e)}")
            raise

    async def update_vehicle(self, search_term, vehicle_data):
        """Update an existing vehicle using the new EVTrack workflow."""
        try:
            # Use the new VehicleUpdateAutomation class
            vehicle_update_automation = VehicleUpdateAutomation(self.driver)
            vehicle_update_automation.set_websocket(self.websocket)
            
            result = await vehicle_update_automation.update_vehicle(search_term, vehicle_data)
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating vehicle: {str(e)}")
            await self.update_progress(100, f"Failed to update vehicle: {str(e)}")
            raise
    # Legacy methods for backward compatibility (these use the old workflow)
    def _search_visitor(self, search_term):
        """Legacy search method - not used by new automation"""
        self.logger.warning("Legacy search method called - use VehicleAddAutomation instead")
        return None
        
    def search_visitor_for_vehicle(self, search_term: str):
        """Legacy method - searches and returns UUID and URL"""
        uuid = self._search_visitor(search_term)
        if uuid:
            return uuid, self.driver.current_url
        return None, None
