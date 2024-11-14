from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Dict, List, Any, Union
from pathlib import Path
import asyncio
import logging
import os
import time
import re
from utils import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

PARENT_DIRECTORY_NAME = "/DESKTOP-GI2LH5U"

class CarousellAutomation:
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

    async def navigate_to_carousell(self) -> None:
        try:
            await self.page.goto('https://www.carousell.ph/sell?source=nav_bar', wait_until='networkidle')
        except PlaywrightTimeoutError:
            logging.error("Failed to load Carousell page")
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
        # Initial category selection
        await self.safe_click("#main > div > div > div > div:nth-child(2) > div > div")
        await self.safe_click("//span[text()='Property']/ancestor::div[2]")
        await asyncio.sleep(0.5)

        # Handle status
        status = all_data['status'].lower()
        if status == 'sale':
            await self.safe_click("//span[text()='For Sale']/ancestor::div[2]")
        else:
            await self.safe_click("//span[text()='Rentals']/ancestor::div[2]")

        # Handle property types
        if all_data['property_id'].startswith('SL'):
            await self.safe_click("//span[text()='Lot']/ancestor::div[2]")
            return

        property_type = all_data['type'].lower()
        match property_type:
            case 'house':
                await self.safe_click("//span[text()='House & Lot']/ancestor::div[2]")
                await self.safe_click("//input[@name='field_pet_friendly' and @value='pet_friendly']/ancestor::label[1]")
                await self.safe_click("//input[@name='field_garden' and @value='garden']/ancestor::label[1]")
            case 'condo':
                await self.safe_click("//span[text()='Apartments & Condos']/ancestor::div[2]")
            case 'townhouse':
                await self.safe_click("//span[text()='Townhouse']/ancestor::div[2]")
            case 'commercial':
                await self.safe_click("//span[text()='Commercial']/ancestor::div[2]")
            case 'lot':
                await self.safe_click("//span[text()='Lot']/ancestor::div[2]")

    async def handle_condition(self, all_data: Dict[str, Any]) -> None:
        condition = ''
        if ((all_data['property_id'].startswith('SRB') and 'pre-selling' in all_data['url'].lower()) or 
            (all_data['property_id'].startswith('SRD') and all_data['listing_description'].lower().find('pre-selling')) or 
            (all_data['property_id'].startswith('SC') and all_data['type'].lower() == 'commercial')):
            condition = 'Pre-Selling'
        elif ((all_data['status'].lower() == 'sale' and all_data['property_id'].startswith('SRD')) or 
              (all_data['property_id'].startswith('SRB'))):
            condition = 'Pre-Owned'
        elif ((all_data['property_id'].startswith('SRB') and all_data['furnishing'].lower() == 'unfurnished') or 
              (all_data['property_id'].startswith('SRB') and 'brand new' in all_data['listing_title'].lower())):
            condition = 'New'
        elif (all_data['property_id'].startswith('SRB') and '/foreclosed/' in all_data['url'].lower()):
            condition = 'Foreclosed'

        if condition:
            await self.safe_click(f"//span[text()='{condition}']/ancestor::button[1]")

    async def handle_location(self, all_data: Dict[str, Any]) -> None:
        get_location = CebuLocationBarangay.get_dynamic_location(all_data)
        await self.safe_click("//input[@name='field_address_autocomplete']/ancestor::label[1]/ancestor::div[1]")
        
        search_input = f"{get_location['barangay']} {get_location['city']}"
        await self.safe_fill("//div[@role='dialog']//input[@placeholder='Search']", search_input)
        await self.page.wait_for_timeout(2000)

        # Base selector that works for the container + first row selection
        base_selector = "//div[@role='dialog']//input[@placeholder='Search']/ancestor::div[3]/following::div[1]//div[1]"
        await self.page.wait_for_selector(base_selector, state='visible', timeout=5000)
        await self.safe_click(base_selector)
        
        await asyncio.sleep(1)
        await self.safe_click("//input[@name='field_is_location_masked']/ancestor::label[1]")

    async def handle_bedrooms(self, bedrooms: int) -> None:
        if not bedrooms and bedrooms != 0:
            return

        text = None
        if bedrooms == 0:
            text = "0 Bedrooms"
        elif bedrooms == 1:
            text = "1 Bedroom"
        elif 2 <= bedrooms <= 5:
            text = f"{bedrooms} Bedrooms"
        elif bedrooms >= 6:
            text = "5+ Bedrooms"

        if text:
            await asyncio.sleep(0.5)
            await self.safe_click("//span[text()='Bedrooms (Optional)']/ancestor::div[2]")
            await self.safe_click(f"//p[text()='{text}']/ancestor::div[3]")

    async def handle_bathrooms(self, bathrooms: int) -> None:
        if not bathrooms and bathrooms != 0:
            return

        text = None
        if bathrooms == 0:
            text = "No Bathrooms"
        elif bathrooms == 1:
            text = "1 Bathroom"
        elif 2 <= bathrooms <= 5:
            text = f"{bathrooms} Bathrooms"
        elif bathrooms >= 6:
            text = "5+ Bathrooms"

        if text:
            await asyncio.sleep(0.5)
            await self.safe_click("//span[text()='Bathrooms (Optional)']/ancestor::div[2]")
            await self.safe_click(f"//p[text()='{text}']/ancestor::div[3]")

    async def handle_furnishing(self, all_data: Dict[str, Any]) -> None:
        furnishing_map = {
            'house': {
                'furnished': 'Fully Furnished',
                'semi-furnished': 'Semi Furnished',
                'unfurnished': 'Unfurnished',
                'pre-selling': 'Pre-Selling',
                'bare': 'Bare',
                'warm-shell': 'warm-shell',
                'bare shell': 'bare shell',
                'fitted-out': 'fitted-out'
            },
            'condo': {
                'furnished': 'Fully Furnished',
                'semi-furnished': 'Semi Furnished',
                'unfurnished': 'Unfurnished',
                'pre-selling': 'Unfurnished'
            },
            'townhouse': {
                'furnished': 'Fully Furnished',
                'semi-furnished': 'Semi Furnished',
                'unfurnished': 'Unfurnished',
                'pre-selling': 'Pre-Selling'
            },
            'commercial': {
                'furnished': 'Fully Fitted',
                'semi-furnished': 'Partially Fitted',
                'unfurnished': 'Bare',
                'bare': 'Bare',
                'warm-shell': 'Partially Fitted',
                'bare shell': 'Bare',
                'fitted-out': '',
                'pre-selling': ''
            },
            'lot': {
                'furnished': 'Fully Furnished',
                'semi-furnished': 'Semi Furnished',
                'unfurnished': 'Unfurnished',
                'pre-selling': 'Pre-Selling'
            }
        }

        property_type = all_data['type'].lower()
        furnishing = all_data['furnishing'].lower()

        if property_type in furnishing_map:
            text = furnishing_map[property_type].get(furnishing, 'Bare')
            if text:
                await self.safe_click(f"//span[text()='{text}']/ancestor::button[1]")

    async def handle_parking(self, parking_spaces: int) -> None:
        if not parking_spaces and parking_spaces != 0:
            return

        text = None
        if 0 <= parking_spaces <= 2:
            text = str(parking_spaces)
        elif parking_spaces >= 3:
            text = "2+"

        if text:
            await self.safe_click(f"//span[text()='{text}']/ancestor::button[1]")

    async def fill_property_details(self, all_data: Dict[str, Any]) -> None:
        # Title and description
        await self.safe_fill("//input[@name='field_title']", all_data['listing_title'])
        await self.safe_fill("//textarea[@name='field_description']", all_data['listing_description'])
        
        # Price
        await self.safe_fill("//input[@name='field_price']", str(all_data['price']))
        
        # Areas
        await self.safe_fill("//input[@name='field_property_floor_area_metric']", str(all_data['floor_area']))
        if all_data['lot_area']:
            await self.safe_fill("//input[@name='field_property_lot_area_metric']", str(all_data['lot_area']))

        # Auto renew
        await self.safe_click("//span[text()='Every 30 days']/ancestor::button[1]")

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
            await self.navigate_to_carousell()
            
            # Media
            await self.upload_images(all_data)
            
            # Property Type and Status
            await self.handle_property_type(all_data)
            
            # Details
            await self.fill_property_details(all_data)
            await self.handle_condition(all_data)
            await self.handle_location(all_data)
            await self.handle_bedrooms(all_data['bedrooms'])
            await self.handle_bathrooms(all_data['bathrooms'])
            await self.handle_furnishing(all_data)
            await self.handle_parking(all_data['parking'])
            
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
    automation = CarousellAutomation()
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