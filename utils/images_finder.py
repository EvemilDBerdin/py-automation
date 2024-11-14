import os
import platform
import asyncio
import logging
from typing import Dict, Any
from pathlib import Path
import re
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class ImagesFinder:
    DEFAULT_ROOT_PATH = r"\\192.168.1.10\Properties"
    MAX_IMAGES = 200
    files_found = 0
    file_paths = []
    current_file_index = 0

    def __init__(self, page: Page):
        self.page = page

    @staticmethod
    def normalize_path(path):
        # Expand user directory if path starts with '~'
        path = os.path.expanduser(path)
        
        # Handle Windows UNC paths
        if path.startswith('//') or path.startswith(r'\\'):
            return path.replace('/', '\\')
        
        # Handle Windows drive paths
        if platform.system() == 'Windows' and len(path) > 1 and path[1] == ':':
            return os.path.normpath(path)
        
        # Handle Unix-style paths
        if path.startswith('/'):
            if platform.system() == 'Windows':
                # Convert to Windows path only if on Windows
                return '\\\\' + path[1:].replace('/', '\\')
            else:
                return os.path.normpath(path)
        
        # For all other cases, use os.path.normpath
        return os.path.normpath(path)

    async def upload_images(self, all_data: Dict[str, Any]) -> None:
        # Get property directory and images using existing methods
        property_dir, image_paths = self.find_images_for_property(
            id_input=all_data['property_id'],
            custom_path=all_data.get('folder_path', None)
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

        # Find file input element
        file_input = await self.page.query_selector("input[type='file']")
        if file_input and sorted_images:
            for image_path in sorted_images:
                try:
                    await file_input.set_input_files(image_path)
                    await asyncio.sleep(0.1)  # Small delay between uploads
                except Exception as e:
                    logging.error(f"Error uploading image {image_path}: {str(e)}")
                    continue

    @staticmethod
    def find_property_directory(id_input, custom_path=None):
        root_path = ImagesFinder.normalize_path(custom_path or ImagesFinder.DEFAULT_ROOT_PATH)
        print(f"Searching for property ID: {id_input}")
        print(f"Root path: {root_path}")
        
        if not os.path.exists(root_path):
            print(f"Warning: Specified path '{root_path}' does not exist. Using default path.")
            return None

        for root, dirs, files in os.walk(root_path):
            if id_input.lower() in root.lower():
                print(f"Found matching directory: {root}")
                return root

        print(f"No matching directory found for {id_input}")
        return None

    @staticmethod
    def get_image_paths(property_dir, id_input, imageSize=0, maxImageCustom=None):
        ImagesFinder.files_found = 0
        ImagesFinder.file_paths = []
        ImagesFinder.current_file_index = 0
        image_extensions = ('.jpg', '.jpeg', '.png')
        
        max_images = maxImageCustom if maxImageCustom is not None else ImagesFinder.MAX_IMAGES
        
        for f in os.listdir(property_dir):
            if ImagesFinder.files_found >= max_images:
                break
            if f.lower().endswith(image_extensions):
                full_path = os.path.join(property_dir, f)
                ImagesFinder.file_paths.append(full_path)
                ImagesFinder.files_found += 1

        if not ImagesFinder.file_paths:
            print(f"No images found for {id_input} in: {property_dir}")
        else:
            print(f"Found {ImagesFinder.files_found} images for {id_input}")

        return ImagesFinder.file_paths

    @staticmethod
    def find_images_for_property(id_input, custom_path=None, maxImageCustom=None):
        property_dir = ImagesFinder.find_property_directory(id_input, custom_path)
        if property_dir is None:
            return None, []
        return property_dir, ImagesFinder.get_image_paths(property_dir, id_input, maxImageCustom=maxImageCustom)

# Example usage in your main code:
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        image_finder = ImagesFinder(page)
        
        # Your data dictionary
        all_data = {
            'property_id': 'example_id',
            'folder_path': 'path/to/images'
        }
        
        # Upload images
        await image_finder.upload_images(all_data)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())