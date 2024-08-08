# from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import os
import json
from tqdm import tqdm
from PIL import Image

# def take_screenshot(url, output_file="screenshot.png", do_it_again=False):
async def take_screenshot(url, output_file="screenshot.png", do_it_again=False):
    # Convert local path to file:// URL if it's a file
    if os.path.exists(url):
        url = "file://" + os.path.abspath(url)

    # whether to overwrite existing screenshots
    if os.path.exists(output_file) and not do_it_again:
        print(f"{output_file} exists!")
        return

    try:
        # with sync_playwright() as p:
        async with async_playwright() as p:
            # Choose a browser, e.g., Chromium, Firefox, or WebKit
            # browser = p.chromium.launch()
            # page = browser.new_page()
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to the URL
            # page.goto(url, timeout=60000)
            await page.goto(url, timeout=60000)

            # Take the screenshot
            # page.screenshot(path=output_file, full_page=True, animations="disabled", timeout=60000)
            await page.screenshot(path=output_file, full_page=True, animations="disabled", timeout=60000)

            # browser.close()
            await browser.close()
    except Exception as e: 
        print(f"Failed to take screenshot due to: {e}. Generating a blank image.")
        # Generate a blank image 
        img = Image.new('RGB', (1280, 960), color = 'white')
        img.save(output_file)