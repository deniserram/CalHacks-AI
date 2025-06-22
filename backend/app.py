import sys
import os

import base64
from PIL import Image
import io
import json # Ensure json is imported
from concurrent.futures import ThreadPoolExecutor

# Make sure google.generativeai is imported
import google.generativeai as genai

# Ensure these imports are correct
from agents.design_agent import analyze_design
from agents.workflow_agent import check_user_workflow
from agents.accessibility_agent import analyze_website_accessibility_and_responsive, AccessibilityAnalysisOutput

from dataclasses import asdict

print(f"DEBUG: sys.path at app.py before accessibility_agent import: {sys.path}")
print(f"DEBUG: Attempting to import from backend.agents.accessibility_agent...")


from flask import Flask, request, jsonify
from flask_cors import CORS

# --- ADD THESE LINES TO CONFIGURE YOUR GEMINI API KEY ---
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual API key
# For a hackathon, hardcoding is quick. For production, use environment variables.
genai.configure(api_key="AIzaSyD6QQMmyJpxMbtk4Ha4_prLkrQodciOBaI") # <--- REPLACE THIS WITH YOUR KEY
# --------------------------------------------------------

# Playwright imports (if you are using Playwright)
from playwright.sync_api import sync_playwright

# Add the 'backend' directory to sys.path (already there)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

app = Flask(__name__)
CORS(app)

# Helper function to get page data using Playwright
def get_page_data_with_playwright(url):
    print(f"Playwright: Navigating to {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False for debugging UI: headless=False
        page = browser.new_page()
        
        try:
            # 1. Increase Timeout and change wait_until strategy
            # 'domcontentloaded' is less strict than 'networkidle'. It waits until the initial HTML is parsed.
            # Then, we add a short fixed wait to allow more content/JS to render.
            page.goto(url, wait_until="domcontentloaded", timeout=60000) # Increased to 60 seconds (60000ms)

            # Add a small fixed delay (e.g., 2-5 seconds) to allow more JavaScript to execute
            # and dynamic content to load after the basic DOM is ready.
            # This is a bit of a hack but often works well for hackathons.
            page.wait_for_timeout(3000) # Wait for 3 seconds

        except Exception as e:
            print(f"Playwright navigation warning for {url}: {e}")
            # If navigation itself timed out but the page might still be usable,
            # we can choose to continue or re-raise. For analysis, often continuing is fine.
            # For this error, it's often better to just proceed with what loaded.
            # You can decide if a failed navigation should halt the analysis.
            # For now, let's just log and continue.

        # 2. Capture Full Page Screenshot
        # This will capture the full scrollable page, which is a key advantage of Playwright.
        screenshot_bytes = page.screenshot(full_page=True)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        print(f"Playwright: Captured screenshot for {url}")

        # 3. Get Key Elements (execute client-side JS within Playwright)
        key_elements_data = page.evaluate('''
            () => {
                const data = { key_elements: [] };
                // Keep this comprehensive list for the agents to analyze
                const selectors = 'h1, h2, h3, h4, h5, h6, p, a, button, img, input, select, textarea, label, li, [role], [tabindex], div, span';

                document.querySelectorAll(selectors).forEach(element => {
                    try {
                        const boundingBox = element.getBoundingClientRect();
                        // Filter out elements that are not visible or have zero dimensions
                        if (boundingBox.width === 0 || boundingBox.height === 0 || boundingBox.x + boundingBox.width <= 0 || boundingBox.y + boundingBox.height <= 0) {
                            return; // Skip invisible or off-screen elements
                        }

                        const computedStyle = window.getComputedStyle(element);
                        const styles = {};
                        // Be selective to avoid too much data; include properties useful for your agents
                        const relevantCssProps = [
                            'fontFamily', 'fontSize', 'color', 'backgroundColor', 'paddingTop', 'paddingBottom',
                            'marginLeft', 'marginRight', 'lineHeight', 'textAlign', 'display', 'position',
                            'zIndex', 'opacity', 'border', 'boxSizing', 'fontWeight', 'textDecoration', 'cursor',
                            'width', 'height', 'top', 'left', 'right', 'bottom' // Add dimensional properties for computed styles
                        ];
                        for (let i = 0; i < computedStyle.length; i++) {
                            const prop = computedStyle[i];
                            if (relevantCssProps.includes(prop)) {
                                styles[prop] = computedStyle.getPropertyValue(prop);
                            }
                        }

                        data.key_elements.push({
                            id: element.id || null,
                            tag_name: element.tagName,
                            // Limit text length to avoid huge payloads, or prune irrelevant text
                            text_content: element.textContent ? element.textContent.trim().substring(0, 500) : null, 
                            bounding_box: {
                                x: boundingBox.x, y: boundingBox.y, width: boundingBox.width, height: boundingBox.height,
                                top: boundingBox.top, right: boundingBox.right, bottom: boundingBox.bottom, left: boundingBox.left
                            },
                            computed_styles: styles,
                            src: element.tagName === 'IMG' ? element.src : null,
                            alt: element.tagName === 'IMG' ? element.alt : null,
                            href: (element.tagName === 'A' || element.tagName === 'AREA') ? element.href : null,
                            role: element.getAttribute('role') || null,
                            tabIndex: element.getAttribute('tabindex') || null
                        });
                    } catch (e) {
                        // console.warn("Playwright evaluate: Could not collect data for element:", element, e);
                    }
                });
                return data;
            }
        ''')
        print(f"Playwright: Collected {len(key_elements_data['key_elements'])} key elements.")

        browser.close()
        return screenshot_base64, key_elements_data['key_elements']

# backend/app.py (REVERTED TO EXTENSION-SIDE DATA COLLECTION)
@app.route('/api/analyze-website', methods=['POST'])
def analyze_website():
    data = request.json
    url = data.get('url')
    
    # Data collection part (choose one: from request if extension-side, or call Playwright)
    # OPTION 1: Data from Chrome Extension (RECOMMENDED FOR SPEED)
    screenshot_base64 = data.get('screenshot_base64')
    key_elements = data.get('key_elements')

    # OPTION 2: If you MUST use Playwright on backend (less recommended for speed)
    # try:
    #     screenshot_base64, key_elements = get_page_data_with_playwright(url)
    # except Exception as e:
    #     return jsonify({"success": False, "error": f"Playwright data collection failed: {e}"}), 500


    if not url:
        return jsonify({"error": "URL is required"}), 400

    print(f"\n--- Received Analysis Request for {url} ---")
    print(f"Screenshot Base64 length: {len(screenshot_base64) if screenshot_base64 else 0} bytes")
    print(f"Number of Key Elements: {len(key_elements) if key_elements else 0}")

    results = {"url": url}

    # Define a list of functions to run in parallel
    agent_tasks = {
        "design_check_results": analyze_design,
        "user_workflow_results": check_user_workflow,
        "accessibility_results": analyze_website_accessibility_and_responsive(url),
    }

    # Use a ThreadPoolExecutor to run agent analyses concurrently
    # Max workers should be chosen carefully; too many can hurt performance
    # 4 is a good starting point for 4 agents.
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Create a list of future objects for each agent call
        futures = {
            key: executor.submit(func, url, screenshot_base64, key_elements)
            for key, func in agent_tasks.items()
        }

        # Collect results as they complete
        for key, future in futures.items():
            try:
                results[key] = future.result() # This will block until the result is ready for this future
            except Exception as e:
                print(f"Error running agent {key}: {e}")
                results[key] = {"status": "error", "message": f"Agent failed: {e}", "data": {}}

    print(f"--- Analysis Complete for {url} ---")
    return jsonify(results)

# ... rest of your Flask app (branding-palettes route etc.)
@app.route('/api/branding-palettes', methods=['GET'])
def get_branding_palettes():
    # Return the current list of saved palettes as JSON
    return jsonify(saved_branding_palettes)


saved_branding_palettes = []

# Your existing route to save palettes
@app.route('/api/branding-palettes', methods=['POST'])
def save_branding_palette():
    data = request.json
    name = data.get('name')
    palette = data.get('palette')

    if not name or not palette:
        return jsonify({"error": "Name and palette are required"}), 400

    # Ensure palette is a list for consistency
    if not isinstance(palette, list):
        return jsonify({"error": "Palette must be a list of colors"}), 400

    # Append the new palette to your in-memory list
    saved_branding_palettes.append({"name": name, "palette": palette})
    
    # You might want to save this to a file for persistence in a real app
    # For now, it's in-memory and will reset on server restart.

    return jsonify({"message": "Palette saved successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)