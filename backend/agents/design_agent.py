# backend/agents/design_agent.py
from playwright.sync_api import sync_playwright
import os # For saving screenshots
# from bs4 import BeautifulSoup # Uncomment if you need advanced HTML parsing
# from webcolors import rgb_to_hex # pip install webcolors - if you do advanced color checks

def analyze_design(url: str) -> dict:
    """
    Analyzes a website for basic design checks, WCAG standards, padding, and responsive design.
    Generates a checklist of potential fixes.
    """
    checklist = []
    issues_found = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch() # You can choose 'firefox' or 'webkit' too
            page = browser.new_page()
            page.goto(url, wait_until="load") # 'load', 'domcontentloaded', 'networkidle'

            # --- 1. Basic WCAG & HTML Structure Checks ---

            # Check for missing alt text on images
            for img in page.locator('img').all():
                if not img.get_attribute('alt'):
                    checklist.append(f"Accessibility: Image missing alt text (src: {img.get_attribute('src')})")
                    issues_found = True

            # Check for basic heading structure (e.g., presence of h1)
            if page.locator('h1').count() == 0:
                checklist.append("Accessibility: No <h1> tag found on the page. Consider a main heading for structure.")
                issues_found = True

            # Check for viewport meta tag (crucial for responsive design)
            if not page.locator('meta[name="viewport"]').count():
                checklist.append("Responsive Design: Missing <meta name='viewport'> tag. This is essential for proper scaling on mobile devices.")
                issues_found = True

            # --- 2. Responsive Design (via screenshots at different viewports) ---
            # These are for manual review or further automated analysis (e.g., image diffing)

            # Define screenshot path
            sanitized_url_name = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_').replace(':', '')
            screenshot_dir = 'screenshots' # Assumed to be created by app.py already

            # Mobile Viewport Screenshot
            page.set_viewport_size({"width": 375, "height": 812}) # iPhone X dimensions
            mobile_screenshot_path = os.path.join(screenshot_dir, f"{sanitized_url_name}_mobile.png")
            page.screenshot(path=mobile_screenshot_path)
            checklist.append(f"Responsive Check: Mobile screenshot captured for visual review: {mobile_screenshot_path}")

            # Desktop Viewport Screenshot
            page.set_viewport_size({"width": 1280, "height": 800}) # Common desktop width
            desktop_screenshot_path = os.path.join(screenshot_dir, f"{sanitized_url_name}_desktop.png")
            page.screenshot(path=desktop_screenshot_path)
            checklist.append(f"Responsive Check: Desktop screenshot captured for visual review: {desktop_screenshot_path}")

            # --- 3. Placeholder for more advanced checks (e.g., contrast, padding consistency) ---
            # These are harder to implement accurately in a hackathon:
            # - Contrast: Requires extracting computed styles for text/background colors and applying WCAG formulas.
            # - Padding/Spacing: Difficult to automate consistency without complex image analysis or robust CSS parsing.

            # Example placeholder for a deeper check if you have time:
            # try:
            #     # This is a highly simplified way to get some CSS properties, not robust for all cases
            #     font_size_elements = page.evaluate('''() => {
            #         const elements = Array.from(document.querySelectorAll('p, li, span, a'));
            #         return elements.map(el => window.getComputedStyle(el).fontSize);
            #     }''')
            #     # You'd then analyze font_size_elements for very small sizes, etc.
            #     if any(int(s.replace('px', '').replace('rem', '').split('.')[0]) < 12 for s in font_size_elements if s.endswith('px')):
            #         checklist.append("Visual Design: Potentially small font sizes detected. Review for readability.")
            #         issues_found = True
            # except Exception as e:
            #     print(f"Could not perform advanced font size check: {e}")

            browser.close()

    except Exception as e:
        checklist.append(f"Error during design analysis: {e}")
        issues_found = True

    status = "completed with issues" if issues_found else "completed successfully"
    return {"status": status, "checklist": checklist}

# Example of how you would call this (for local testing of the agent script):
# if __name__ == '__main__':
#     test_url = "https://www.google.com" # Or any URL you want to test
#     results = analyze_design(test_url)
#     import json
#     print(json.dumps(results, indent=2))