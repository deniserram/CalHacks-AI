# backend/agents/branding_agent.py

from playwright.sync_api import sync_playwright
from colorthief import ColorThief
import io
import os
import base64
from PIL import Image

def extract_branding_palette(url=None, screenshot_base64=None, key_elements=None):
    """
    Extracts a branding palette from a website. If a screenshot is passed in base64,
    it uses that. Otherwise, it will take a screenshot using Playwright.
    """

    palette_data = {}
    issues_found = False
    temp_screenshot_path = None

    try:
        # If base64 screenshot provided, use it directly (your flow)
        if screenshot_base64:
            image_bytes = base64.b64decode(screenshot_base64)
            img_stream = io.BytesIO(image_bytes)
            color_thief = ColorThief(img_stream)

            dominant_colors_rgb = color_thief.get_palette(color_count=6)
        
        # If no base64 screenshot provided, fallback to your teammate's flow
        elif url:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url, wait_until="load")

                # Save screenshot to file
                sanitized_url_name = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_').replace(':', '')
                screenshot_dir = 'screenshots'
                os.makedirs(screenshot_dir, exist_ok=True)
                temp_screenshot_path = os.path.join(screenshot_dir, f"{sanitized_url_name}_temp_branding.png")

                page.screenshot(path=temp_screenshot_path, full_page=True)
                browser.close()

                color_thief = ColorThief(temp_screenshot_path)
                dominant_colors_rgb = color_thief.get_palette(color_count=6)
        else:
            raise Exception("No screenshot or URL provided.")

        # Map colors to simplified labels
        color_names = ["primary", "secondary", "accent1", "accent2", "dark_text", "light_bg"]
        for i, rgb in enumerate(dominant_colors_rgb):
            hex_color = '#%02x%02x%02x' % rgb
            if i < len(color_names):
                palette_data[color_names[i]] = hex_color
            else:
                palette_data[f"color_{i+1}"] = hex_color

    except Exception as e:
        print(f"Error extracting branding palette: {e}")
        issues_found = True

    finally:
        if temp_screenshot_path and os.path.exists(temp_screenshot_path):
            os.remove(temp_screenshot_path)

    status = "completed with issues" if issues_found or not palette_data else "completed"
    return {
        "status": status,
        "palette": palette_data
    }
