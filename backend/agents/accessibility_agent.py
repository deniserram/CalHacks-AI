# backend/agents/branding_agent.py

import base64
from PIL import Image
import io
from colorthief import ColorThief
from utils import get_image_parts, parse_gemini_json_response
import google.generativeai as genai

# --- FIX THIS LINE ---
def extract_branding_palette(url, screenshot_base64, key_elements):
# --- END FIX ---
    """
    Extracts dominant colors and a color palette from the webpage screenshot.
    Optionally uses Gemini for branding tone analysis.
    """
    print(f"Running Branding Agent for: {url}")
    
    dominant_color = None
    palette = []
    branding_tone = "N/A"

    if screenshot_base64:
        try:
            image_bytes = base64.b64decode(screenshot_base64)
            img_stream = io.BytesIO(image_bytes)
            
            img_stream.seek(0) 
            color_thief = ColorThief(img_stream)
            
            dominant_rgb = color_thief.get_color(quality=1)
            palette_rgb = color_thief.get_palette(color_count=5, quality=10) 

            dominant_color = f"#{dominant_rgb[0]:02x}{dominant_rgb[1]:02x}{dominant_rgb[2]:02x}"
            palette = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette_rgb]

        except Exception as e:
            print(f"Error extracting colors with ColorThief: {e}")
            return {"status": "error", "message": f"Color extraction failed: {e}", "data": {"dominant_color": None, "palette": [], "branding_tone": branding_tone}}
    else:
        return {"status": "error", "message": "No screenshot provided for branding palette extraction.", "data": {"dominant_color": None, "palette": [], "branding_tone": branding_tone}}

    return {
        "status": "success",
        "data": {
            "dominant_color": dominant_color,
            "palette": palette,
            "branding_tone": branding_tone
        }
    }