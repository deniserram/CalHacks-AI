# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from agents.design_agent import analyze_design
from agents.workflow_agent import check_user_workflow
from agents.accessibility_agent import extract_branding_palette

# --- Ensure 'screenshots' directory exists for Playwright if you use it directly in backend agents ---
if not os.path.exists('screenshots'):
    os.makedirs('screenshots')

app = Flask(__name__)
# IMPORTANT: Allow CORS from your Chrome Extension origin.
# For local development, this usually means allowing '*' or specific origins like chrome-extension://<EXTENSION_ID>
# '*' is easiest for hackathon, but less secure for production.
CORS(app) # Allows all origins for simplicity in hackathon

# In-memory storage for branding palettes (resets on server restart)
branding_palettes = {}

# --- Agent Stubs (Your team will replace these with actual logic) ---
# You'll import your actual agent functions here later.
# For now, we'll use simple mocks.

def mock_design_analysis(url):
    print(f"Mocking design analysis for {url}")
    return {
        "status": "completed with issues",
        "checklist": [
            "Missing alt text on some images",
            "Low contrast detected in header (e.g., #FFFFFF on #EEEEEE)",
            "Viewport meta tag missing or misconfigured for responsive design"
        ]
    }

def mock_workflow_analysis(url):
    print(f"Mocking workflow analysis for {url}")
    return {
        "status": "completed with issues",
        "suggestions": [
            "AI agent got confused finding 'Contact Us' link. Consider clearer labeling.",
            "Primary call-to-action (CTA) not easily discoverable from homepage.",
            "Navigation path to 'Product Details' page took too many clicks."
        ]
    }

def mock_branding_extraction(url):
    print(f"Mocking branding palette extraction for {url}")
    # In real agent, ColorThief would extract from a screenshot
    return {
        "status": "completed",
        "palette": {
            "primary_brand": "#336699",
            "secondary_accent": "#FFCC00",
            "text_color": "#333333",
            "background_color": "#F0F0F0"
        }
    }
# -------------------------------------------------------------------


@app.route('/')
def hello():
    return "Backend is running! Visit /api/analyze-website or /api/branding-palettes."

@app.route('/api/analyze-website', methods=['POST'])
def analyze_website():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    results = {
        "url": url,
        "design_check_results": {},
        "user_workflow_results": {},
        "branding_palette_results": {}
    }

    try:
        # Call your actual agent functions here later
        results["design_check_results"] = analyze_design(url)
        results["user_workflow_results"] = check_user_workflow(url)
        results["branding_palette_results"] = extract_branding_palette(url)

    except Exception as e:
        app.logger.error(f"Error during analysis for {url}: {e}")
        results["error"] = f"An error occurred during analysis: {str(e)}"
        results["design_check_results"]["status"] = "failed"
        results["user_workflow_results"]["status"] = "failed"
        results["branding_palette_results"]["status"] = "failed"

    return jsonify(results)

@app.route('/api/branding-palettes', methods=['GET', 'POST'])
def handle_branding_palettes():
    if request.method == 'POST':
        palette_data = request.json
        palette_name = palette_data.get('name')
        if palette_name:
            branding_palettes[palette_name] = palette_data.get('palette', {})
            return jsonify({"message": f"Palette '{palette_name}' saved successfully"}), 201
        return jsonify({"error": "Palette name is required"}), 400
    else: # GET
        return jsonify(branding_palettes)

if __name__ == '__main__':
    # Ensure debug is True for development, but False for production!
    app.run(debug=True, port=5000)