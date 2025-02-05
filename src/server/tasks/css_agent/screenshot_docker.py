from playwright.sync_api import sync_playwright
import os
import sys
from PIL import Image

def take_screenshot(url, output_file="screenshot.png", do_it_again=False):
    # Convert local path to file:// URL if it's a file
    if os.path.exists(url):
        url = "file://" + os.path.abspath(url)

    # whether to overwrite existing screenshots
    if os.path.exists(output_file) and not do_it_again:
        print(f"{output_file} exists!")
        return

    try:
        with sync_playwright() as p:
            # Choose a browser, e.g., Chromium, Firefox, or WebKit
            browser = p.chromium.launch()
            page = browser.new_page()

            # Navigate to the URL
            page.goto(url, timeout=60000)

            print(page.evaluate("() => document.documentElement.scrollWidth"))
            print(page.evaluate("() => document.documentElement.scrollHeight"))

            # Take the screenshot
            page.screenshot(path=output_file, full_page=True, animations="disabled", timeout=60000)

            browser.close()
    except Exception as e: 
        print(f"Failed to take screenshot due to: {e}. Generating a blank image.")
        # Generate a blank image 
        img = Image.new('RGB', (1280, 960), color = 'white')
        img.save(output_file)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python screenshot.py <url> <output_file> [do_it_again]")
    else:
        url = sys.argv[1]
        output_file = sys.argv[2]
        do_it_again = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
        take_screenshot(url, output_file, do_it_again)
