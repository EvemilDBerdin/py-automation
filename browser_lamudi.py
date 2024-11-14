from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Dict, List, Any, Union
from pathlib import Path
import asyncio
import logging
import os
import time
import re
import random
from utils import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# PARENT_DIRECTORY_NAME = "/DESKTOP-GI2LH5U"

class LamudiAutomation:
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
            
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                args=['--start-maximized']
            )
            
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

    async def navigate_to_lamudi(self) -> None:
        try:
            await self.page.goto('https://portal.lamudi.com.ph/property', wait_until='networkidle')
        except PlaywrightTimeoutError:
            logging.error("Failed to load Lamudi page")
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
            await self.safe_click("//div[text()='Land']")
            await self.safe_click("//div[text()='Commercial Lot']")
            return

        property_type = all_data['type'].lower()
        match property_type:
            case 'house':
                await self.safe_click("//div[text()='House']")
                await self.safe_click("//div[text()='Single-family House']")
            case 'condo':
                await self.safe_click("//div[text()='Condominium']")
                if all_data['street_unit_no'].lower() == 'penthouse':
                    await self.safe_click("//div[text()='Penthouse']")
                if 1 <= all_data['bedrooms'] <= 3:
                    await self.safe_click("//div[text()='Other']")
                if 20 <= all_data['floor_area'] <= 25:
                    await self.safe_click("//div[text()='Studio']")
            case 'townhouse':
                await self.safe_click("//div[text()='House']")
                await self.safe_click("//div[text()='Townhouse']")
            case 'commercial':
                await self.safe_click("//div[text()='Commercial']")
                await self.safe_click("//div[text()='Offices']")
            case 'lot':
                await self.safe_click("//div[text()='Land']")
                await self.safe_click("//div[text()='Commercial Lot']")

    async def handle_status(self, all_data: Dict[str, Any]) -> None:
        status = all_data['status'].lower()
        match status:
            case 'sale':
                await self.safe_click("//span[text()='Sell']/ancestor::div[2]")
            case 'rent':
                await self.safe_click("//span[text()='Rent']/ancestor::div[2]")

    async def handle_furnishing(self, all_data: Dict[str, Any]) -> None:
        furnishing_map = {
            'furnished': 'Yes',
            'semi-furnished': 'Semi',
            'unfurnished': 'No',
            'bare': 'No',
            'warm-shell': 'Semi',
            'bare shell': 'No',
            'fitted-out': 'No',
            'pre-selling': 'No'
        }
        
        furnishing = all_data['furnishing'].lower()
        if furnishing in furnishing_map:
            await self.safe_click(f"//button[text()='{furnishing_map[furnishing]}']")
        else:
            await self.safe_click("//button[text()='No']")

    async def handle_features(self, all_data: Dict[str, Any]) -> None:
        feature_map = {
            'condo': [
                'Utility room', 'Air conditioning', 'Balcony', 'Elevators',
                'Function Room', 'Lobby', 'Lounge', 'Powder room', 'Reception Area',
                'Wi-Fi', 'Landscaped Garden', 'Playground', 'Jogging path', 'Parking lot',
                'Secure parking', '24-hour security', 'Gym', 'Entertainment room',
                'Daycare Center'
            ],
            'commercial': [
                "Air conditioning", "Elevators", "Lobby", "Reception area", "24-hour security"
            ],
            'house': [
                "Balcony", "Ensuite", "Air conditioning", "Entertainment room",
                "Lounge", "Maid's room", "Powder room", "Storage Room",
                "Carport", "Courtyard", "Fully fenced", "Garage", "Jogging path", 
                "Tennis court", "24-hour security", "Garden", "Landscaped Garden"
            ],
            'townhouse': [
                "Balcony", "Ensuite", "Air conditioning", "Entertainment room",
                "Lounge", "Maid's room", "Powder room", "Storage Room",
                "Carport", "Courtyard", "Fully fenced", "Garage", "Jogging path", 
                "Tennis court", "24-hour security", "Garden", "Landscaped Garden"
            ]
        }

        property_type = all_data['type'].lower()
        if property_type in feature_map:
            features = feature_map[property_type]
            if 'swimming pool' in all_data['listing_description'].lower():
                features.append('Swimming pool')

            for feature in features:
                xpath = f"//div[contains(@class, 'floating-container')]//div[contains(@class, 'button-small')][normalize-space()='{feature}']"
                await self.safe_click(xpath)
                await asyncio.sleep(0.025)

    async def fill_property_details(self, all_data: Dict[str, Any]) -> None:
        # Basic Details
        await self.safe_fill("//input[@name='title_en']", all_data['listing_title'])
        await self.safe_fill("//div[@contenteditable='true']", all_data['listing_description'].replace('•', '-'))
        await self.safe_fill("//input[@name='attribute[bedrooms]']", str(all_data['bedrooms']))
        await self.safe_fill("//input[@name='attribute[bathrooms]']", str(all_data['bathrooms']))
        await self.safe_fill("//input[@name='attribute[land_size]']", str(all_data['lot_area']))
        
        # More Key Information
        await self.safe_click("//div[1]//span[@id='property-toggleMoreKeyInfo']")
        await self.safe_fill("//input[@name='attribute[building_size]']", str(all_data['floor_area']))
        await self.safe_fill("//input[@name='attribute[car_spaces]']", str(all_data['parking']))
        
        # Classification for new properties
        if any(all_data['property_id'].startswith(prefix) for prefix in ['SRD', 'SRB', 'SC']):
            if ((all_data['property_id'].startswith('SRD') and all_data['status'].lower() == 'sale') or 
                ('brand new' in all_data['listing_description'].lower()) or 
                (all_data['property_id'].startswith('SRB') and all_data['furnishing'].lower() == 'unfurnished') or 
                (all_data['property_id'].startswith('SC') and all_data['type'].lower() == 'commercial')):
                await self.safe_click("//button[text()='Brand New']")
            elif all_data['property_id'].startswith('SRB'):
                await self.safe_click("//button[text()='Resale']")

        # Price and SKU
        await self.safe_fill("//input[@name='price_PHP']", str(all_data['price']))
        await self.safe_click("//span[text()='Per Year'][1]")
        await self.safe_click("//div[@class='slu_datePicker']//input[@type='text']")
        await self.safe_click("//div[contains(@class, 'slu_datePicker')]//div[contains(@class, 'react-datepicker__day--today')]")
        await self.safe_fill("//input[@name='skuOwner']", f"{all_data['property_id']}-{random.randint(100, 999999)}")

    async def handle_location(self, all_data: Dict[str, Any]) -> None:
        get_location = CebuLocationBarangay.get_dynamic_location(all_data)
        
        location_fields = [
            ("location_region", "Cebu"),
            ("location_city", get_location['city']),
            ("location_area", get_location['barangay'])
        ]

        for field, value in location_fields:
            await self.safe_fill(f"//input[@name='{field}']", value)
            try:
                await self.safe_click("//div[contains(@class, 'typeahead-scrollview-wrapper')]//li")
            except:
                continue

        await self.safe_click("//input[@id='location-hide-checkbox']")

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

    async def run_automation(self, id_input: str) -> None:
        try:
            all_data = AirtableDataHelper.get_airtable_record(id_input)
            if not all_data:
                logging.error(f"No data found for property ID: {id_input}")
                return
                
            await self.initialize()
            await self.navigate_to_lamudi()
            
            # Media
            await self.upload_images(all_data)
            
            # Property Setup
            await self.handle_status(all_data)
            await self.handle_property_type(all_data)
            
            # Details
            await self.fill_property_details(all_data)
            await self.handle_furnishing(all_data)
            await self.handle_features(all_data)
            
            # Location
            await self.handle_location(all_data)
            
            logging.info(f"Successfully processed property: {id_input}")
            
        except Exception as e:
            logging.error(f"Error processing property {id_input}: {str(e)}")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logging.info("Script manually interrupted")
        finally:
            pass

async def main(id_input: str):
    automation = LamudiAutomation()
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