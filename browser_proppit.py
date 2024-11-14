from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Dict, List, Any, Union
from pathlib import Path
import asyncio
import logging
import os
import time
import re
import json
from datetime import datetime
from utils import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# PARENT_DIRECTORY_NAME = "/DESKTOP-GI2LH5U"

class PropertyAutomation:
    def __init__(self):
        self.page: Optional[Page] = None
        self.browser: Optional[BrowserContext] = None
        self.context: Optional[BrowserContext] = None
        self.user_data_dir = os.path.join(os.path.expanduser("~"), "playwright_chrome_data")
        self.playwright = None

    async def initialize(self) -> None:
        try:
            self.playwright = await async_playwright().start()
            os.makedirs(self.user_data_dir, exist_ok=True)
            
            # Launch browser with persistent context
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                args=['--start-maximized']
            )
            
            # Get or create page
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
            else:
                self.page = await self.browser.new_page()
                
            await self.setup_page_handlers()
            logging.info("Browser initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize browser: {str(e)}")
            raise

    async def setup_page_handlers(self) -> None:
        self.page.set_default_timeout(30000)
        self.page.on("dialog", lambda dialog: dialog.accept())
        
    async def navigate_to_proppit(self) -> None:
        try:
            await self.page.goto('https://proppit.com/properties/new-property', wait_until='networkidle')
        except PlaywrightTimeoutError:
            logging.error("Failed to load Proppit page")
            raise

    async def safe_click(self, selector: str) -> bool:
        try:
            element = await self.page.wait_for_selector(selector, timeout=2000)
            if element:
                await element.click()
                await asyncio.sleep(0.1)
                return True
        except:
            return False

    async def safe_fill(self, selector: str, value: str) -> bool:
        try:
            if not value:
                return False
            element = await self.page.wait_for_selector(selector, timeout=2000)
            if element:
                await element.fill(str(value))
                await asyncio.sleep(0.1)
                return True
        except:
            return False

    async def handle_property_type(self, all_data: Dict[str, Any]) -> None:
        if all_data['property_id'].startswith('SL'):
            await self.safe_click("//input[@name='propertyType' and @value='land']/following-sibling::div//span")
            return
        
        property_type = all_data['type'].lower()
        await self.safe_click(f"//input[@name='propertyType' and @value='{property_type}']/following-sibling::div//span")

    async def handle_status(self, all_data: Dict[str, Any]) -> None:
        status_mapping = {
            'sale': 'newprop_operation_sell',
            'rent': 'newprop_operation_rent'
        }
        
        status = all_data['status'].lower()
        if status in status_mapping:
            await self.safe_click(f"//span[@data-tag='{status_mapping[status]}']")

    async def fill_property_details(self, all_data: Dict[str, Any]) -> None:

        #Location
        await self.location(all_data)

        # Price
        await self.safe_fill("input[data-tag='operation_rentPrice']", str(all_data['price']))
        await self.safe_fill("input[data-tag='operation_sellPrice']", str(all_data['price']))
        
        # Areas
        await self.safe_fill("input[name='usableArea']", str(all_data['floor_area']))
        await self.safe_fill("input[name='plotAreaSqm']", str(all_data['lot_area']))
        
        # Rooms
        await self.safe_fill("input[name='bedrooms']", str(all_data['bedrooms']))
        await self.safe_fill("input[name='bathrooms']", str(all_data['bathrooms']))
        
        # Property Info
        await self.safe_fill("input[data-tag='property_referenceId']", all_data['property_id'])
        await self.safe_fill("input[data-tag='property_title']", all_data['listing_title'])
        
        # Description
        description = all_data['listing_description'].replace('•', '-').strip()
        await self.safe_fill("textarea[data-tag='property_description']", description)

    async def location(self, all_data: Dict[str, Any]) -> None:
         # Location
        get_location = CebuLocationBarangay.get_dynamic_location(all_data)

        if await self.safe_fill("input[data-tag='address_input']", f"{get_location['barangay']} {get_location['city']}"):
            await asyncio.sleep(1)
            await self.safe_click("div[data-tag='address_suggestions'] div[role='option']:first-child")
            await self.safe_click("//span[text()='Show area']/ancestor::label[1]")
        

    async def handle_furnishing(self, all_data: Dict[str, Any]) -> None:
        furnishing_map = {
            'furnished': 'Fully',
            'semi-furnished': 'Partly furnished',
            'unfurnished': 'Unfurnished',
            'bare': 'Unfurnished',
            'warm-shell': 'Partly furnished',
            'bare shell': 'Unfurnished',
            'pre-selling': 'Unfurnished'
        }
        
        furnishing = all_data['furnishing'].lower()
        if furnishing in furnishing_map:
            if await self.safe_click("//span[@data-tag='newprop_furnished_title']/following::div"):
                await self.safe_click(f"//span[text()='{furnishing_map[furnishing]}']/ancestor::div[2]")

    async def handle_facilities(self, all_data: Dict[str, Any]) -> None:
        facility_map = {
            'condo': [
                "Air conditioning", "Balcony", "Car park", "Equipped kitchen",
                "Built-in kitchen", "Utility room", "Concierge", "Garden", "Gym",
                "Elevator", "Security", "Swimming pool", "Near main road",
                "Nearby malls", "Nearby schools", "Children's area"
            ],
            'commercial': ["Air conditioning", "Car park", "Concierge", "Security"],
            'offices': ["Air conditioning", "Car park", "Concierge", "Security"],
            'house': [
                "Air conditioning", "Balcony", "Car park", "Equipped kitchen",
                "Built-in kitchen", "Utility room", "Garden", "Security"
            ],
            'lot': ["Security"]
        }
        
        property_type = all_data['type'].lower()
        if property_type in facility_map:
            for facility in facility_map[property_type]:
                await self.safe_click(f"//span[text()='{facility}']/ancestor::label[1]")

    async def upload_images(self, all_data: Dict[str, Any]) -> None:
        try:
            # Find and sort images using ImagesFinder
            property_dir, image_paths = ImagesFinder(self.page).find_images_for_property(
                id_input=all_data['property_id'],
                custom_path=f"{PARENT_DIRECTORY_NAME}{all_data['folder_path']}"
            )

            if not property_dir or not image_paths:
                logging.error(f"No images found for property ID: {all_data['property_id']}")
                return

            # Sort images based on the number in parentheses
            sorted_images = sorted(
                image_paths,
                key=lambda x: int(re.search(r'\((\d+)\)', os.path.basename(x)).group(1)) 
                if re.search(r'\((\d+)\)', os.path.basename(x)) 
                else float('inf')
            )

            # Upload all images at once
            file_input = await self.page.query_selector("input[type='file']")
            if file_input and sorted_images:
                try:
                    # Convert paths to strings and upload all at once
                    image_paths_str = [str(path) for path in sorted_images]
                    await file_input.set_input_files(image_paths_str)
                except Exception as e:
                    logging.error(f"Error uploading images: {str(e)}")

        except Exception as e:
            logging.error(f"Error in upload_images: {str(e)}")

    async def add_contact_info(self) -> None:
        cgr_messenger = "https://www.facebook.com/CebuGrandRealty"
        phone = await self.page.get_attribute("input[name='contactPhone']", "value")
        
        if phone:
            await self.safe_fill("input[name='contactFacebookMessenger']", cgr_messenger)
            await self.safe_fill("input[name='contactViber']", f"+63{phone}")

    async def run_automation(self, id_input: str) -> None:
        try:
            all_data = AirtableDataHelper.get_airtable_record(id_input)
            if not all_data:
                logging.error(f"No data found for property ID: {id_input}")
                return
                
            await self.initialize()
            await self.navigate_to_proppit()
            
            # Media
            await self.upload_images(all_data)
            
            # Property Setup
            await self.handle_status(all_data)
            await self.handle_property_type(all_data)
            
            # Details
            await self.fill_property_details(all_data)
            await self.handle_furnishing(all_data)
            await self.handle_facilities(all_data)
            
            # Contact
            await self.add_contact_info()
            
            logging.info(f"Successfully processed property: {id_input}")
            
        except Exception as e:
            logging.error(f"Error processing property {id_input}: {str(e)}")
        
        # Don't close the browser, just wait indefinitely
        try:
            # Keep the script running until manually interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logging.info("Script manually interrupted")
        finally:
            # Optional: Add cleanup code here if needed in the future
            pass

async def main(id_input: str):
    automation = PropertyAutomation()
    await automation.run_automation(id_input)

def get_valid_directory() -> str:
    while True:
        directory = input("Please enter the parent directory path (e.g., /DESKTOP-GI2LH5U): ").strip()
        if not directory:
            print("Error: Directory path cannot be empty")
            continue
        if not directory.startswith('/'):
            print("Error: Directory path must start with '/'")
            continue
        return directory

if __name__ == "__main__":
    print("Welcome to Lamudi Property Automation")
    
    # Get parent directory
    # PARENT_DIRECTORY_NAME = get_valid_directory()
    PARENT_DIRECTORY_NAME = 'C:/Users/merry/OneDrive - Cebu Grand Realty'
    print(f"Using directory: {PARENT_DIRECTORY_NAME}")
    
    # Get property ID
    property_id = input("Please enter the property ID: ").strip()
    if not property_id:
        print("Error: Property ID cannot be empty")
    else:
        asyncio.run(main(property_id.upper()))