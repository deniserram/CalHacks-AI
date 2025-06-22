import os
import google.generativeai as genai
import base64
from PIL import Image
import io
import json

# Configure Gemini API (make sure GEMINI_API_KEY is set as an environment variable)
# It's best practice to load this from an environment variable or a secure configuration system.
# For quick hackathon setup, you might temporarily hardcode it here, but remove before production.
# Example: os.environ.get("GEMINI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("WARNING: GEMINI_API_KEY environment variable not set. Gemini functions may fail.")
    # You might want to raise an error or exit in a production app.

genai.configure(api_key=gemini_api_key)

# Helper Function: Prepare image for Gemini Vision API
def get_image_parts(screenshot_base64):
    if not screenshot_base64:
        return []
    try:
        image_bytes = base64.b64decode(screenshot_base64)
        return [{"mime_type": "image/png", "data": image_bytes}]
    except Exception as e:
        print(f"Error decoding screenshot for Gemini: {e}")
        return []

# Helper Function: Safely parse Gemini's JSON output
def parse_gemini_json_response(response_text):
    try:
        # Gemini often wraps JSON in ```json\n...\n```, so we need to clean it
        clean_text = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from Gemini: {e}")
        print(f"Gemini raw response: {response_text}")
        return {"error": f"Failed to parse AI response: {e}", "raw_response": response_text}
    except Exception as e:
        print(f"An unexpected error occurred while parsing Gemini response: {e}")
        return {"error": f"An unexpected error occurred: {e}", "raw_response": response_text}

# You can add other utility functions here if needed by multiple agents