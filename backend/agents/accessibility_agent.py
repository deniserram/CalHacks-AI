# backend/agents/branding_agent.py
from playwright.sync_api import sync_playwright
from colorthief import ColorThief # pip install colorthief
import io # To handle image data in memory
import os # For saving temporary screenshots (ColorThief can work from bytes, but file is often simpler)
# from webcolors import rgb_to_hex # pip install webcolors - useful for converting RGB tuples to hex strings


def extract_branding_palette(url: str) -> dict:
   """
   Extracts a branding palette from a website by taking a screenshot and
   using ColorThief to find dominant colors.
   """
   palette_data = {}
   issues_found = False
   temp_screenshot_path = None # Initialize to None


   try:
       with sync_playwright() as p:
           browser = p.chromium.launch()
           page = browser.new_page()
           page.goto(url, wait_until="load") # Wait for page to load


           # Define screenshot path
           sanitized_url_name = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_').replace(':', '')
           screenshot_dir = 'screenshots' # Assumed to be created by app.py already
           temp_screenshot_path = os.path.join(screenshot_dir, f"{sanitized_url_name}_temp_branding.png")


           # Take a screenshot
           page.screenshot(path=temp_screenshot_path, full_page=True)
           browser.close()


           # Use ColorThief to extract dominant colors from the screenshot
           color_thief = ColorThief(temp_screenshot_path)


           # Get a color palette (e.g., 6 dominant colors)
           # You can adjust the number of colors in get_palette()
           dominant_colors_rgb = color_thief.get_palette(color_count=6)


           # Convert RGB tuples to hex codes for easier use in frontend
           # Assign simple names for the hackathon
           color_names = ["primary", "secondary", "accent1", "accent2", "dark_text", "light_bg"]
           for i, rgb in enumerate(dominant_colors_rgb):
               hex_color = '#%02x%02x%02x' % rgb # Convert RGB tuple to hex string
               if i < len(color_names):
                   palette_data[color_names[i]] = hex_color
               else:
                   palette_data[f"color_{i+1}"] = hex_color # Fallback for extra colors


   except Exception as e:
       print(f"Error extracting branding palette: {e}")
       issues_found = True


   finally:
       # Clean up the temporary screenshot file
       if temp_screenshot_path and os.path.exists(temp_screenshot_path):
           os.remove(temp_screenshot_path)


   status = "completed with issues" if issues_found or not palette_data else "completed"
   return {"status": status, "palette": palette_data}


# Example of how you would call this:
# if __name__ == '__main__':
#     test_url = "https://www.nasa.gov/" # Or any URL
#     results = extract_branding_palette(test_url)
#     import json
#     print(json.dumps(results, indent=2))














