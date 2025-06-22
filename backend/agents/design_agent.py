import google.generativeai as genai
# Change this import line:
from utils import get_image_parts, parse_gemini_json_response # Import helpers

# ... rest of the design_agent.py code
def analyze_design(url, screenshot_base64, key_elements):
    """
    Analyzes the design of a webpage using Gemini Pro Vision and DOM data.
    """
    print(f"Running Design Agent for: {url}")
    
    image_parts = get_image_parts(screenshot_base64)

    design_elements_context = []
    # Filter and format key_elements relevant for design analysis
    for e in key_elements:
        if e['tag_name'] in ['H1', 'H2', 'P', 'BUTTON', 'A', 'IMG', 'DIV', 'SPAN'] and e['bounding_box']['width'] > 0 and e['bounding_box']['height'] > 0:
            styles = e['computed_styles']
            design_elements_context.append(
                f"- Tag: {e['tag_name']}, Text: '{e['text_content'] or ''}', "
                f"BBox: ({e['bounding_box']['x']},{e['bounding_box']['y']},{e['bounding_box']['width']}x{e['bounding_box']['height']}), "
                f"Styles: {{font: {styles.get('fontSize')}/{styles.get('lineHeight')} {styles.get('fontFamily')}, color: {styles.get('color')}, bg: {styles.get('backgroundColor')}}}"
            )
    
    prompt_parts = [
        "You are an expert UI/UX designer. Analyze the provided webpage screenshot and key elements for its design quality, focusing on visual hierarchy, consistency, spacing, typography, and color harmony. Identify specific areas for improvement and provide actionable recommendations. Be concise and actionable.",
        f"Webpage URL: {url}\n",
        "Here is the visual context:",
        *image_parts,
        "Here are details of key elements from the page's DOM structure:\n",
        "\n".join(design_elements_context) if design_elements_context else "No specific elements provided or elements filtered.",
        "\nProvide your analysis in a structured JSON format. Example structure:",
        """
        ```json
        {
          "design_feedback": [
            {
              "aspect": "Visual Hierarchy",
              "issue": "Headings are not clearly differentiated from body text.",
              "recommendation": "Increase font size or weight of H1/H2 elements."
            },
            {
              "aspect": "Spacing Consistency",
              "issue": "Inconsistent vertical spacing between sections.",
              "recommendation": "Establish a consistent vertical rhythm using a base unit for spacing (e.g., 20px, 40px)."
            },
            {
              "aspect": "Typography",
              "issue": "Too many font styles are used, leading to visual clutter.",
              "recommendation": "Limit to 2-3 complementary font families and consistent sizes."
            },
            {
              "aspect": "Color Harmony",
              "issue": "Colors feel disjointed and don't form a cohesive palette.",
              "recommendation": "Utilize a primary, secondary, and accent color scheme consistently."
            }
          ]
        }
        ```
        """
    ]

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')        # Ensure the generation_config is set for JSON output if supported by your model version
        response = model.generate_content(prompt_parts, generation_config={"response_mime_type": "application/json"})
        parsed_data = parse_gemini_json_response(response.text)
        return {"status": "success", "data": parsed_data}
    except Exception as e:
        print(f"Error in Design Agent: {e}")
        return {"status": "error", "message": f"Design analysis failed: {e}", "data": {}}