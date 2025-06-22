import google.generativeai as genai
from utils import get_image_parts, parse_gemini_json_response # Import helpers

def check_user_workflow(url, screenshot_base64, key_elements):
    """
    Analyzes user workflow and call-to-action clarity on a webpage.
    """
    print(f"Running Workflow Agent for: {url}")
    
    image_parts = get_image_parts(screenshot_base64)

    workflow_elements_context = []
    # Focus on interactive elements, headings, and key text blocks
    for e in key_elements:
        if e['tag_name'] in ['A', 'BUTTON', 'INPUT', 'FORM', 'H1', 'H2', 'P'] or (e.get('role') in ['button', 'link', 'navigation'] and e['bounding_box']['width'] > 0 and e['bounding_box']['height'] > 0):
            workflow_elements_context.append(
                f"- Tag: {e['tag_name']}, Text: '{e['text_content'] or ''}', "
                f"Type: {e.get('type', 'N/A')}, BBox: ({e['bounding_box']['x']},{e['bounding_box']['y']},{e['bounding_box']['width']}x{e['bounding_box']['height']}), "
                f"Href: {e['href'] or 'N/A'}"
            )

    prompt_parts = [
        "You are an expert in user experience (UX) and conversion rate optimization (CRO). Analyze the provided webpage screenshot and key elements to assess the clarity and effectiveness of its primary user workflows (e.g., 'Sign Up', 'Contact Us', 'Buy Now'). Identify any roadblocks, confusing elements, or missed opportunities for guiding the user. Focus on navigational clarity, call-to-action prominence, and overall ease of task completion.",
        f"Webpage URL: {url}\n",
        "Here is the visual context:",
        *image_parts,
        "Here are details of key interactive and content elements from the page's DOM structure:\n",
        "\n".join(workflow_elements_context) if workflow_elements_context else "No specific elements provided or elements filtered.",
        "\nProvide your analysis in a structured JSON format. For each issue, provide a specific recommendation. Example structure:",
        """
        ```json
        {
          "workflow_analysis": [
            {
              "workflow_path": "Primary Call to Action (e.g., 'Sign Up')",
              "issue": "The main 'Sign Up' button is not prominent enough or is below the fold.",
              "recommendation": "Move the primary CTA above the fold and use a contrasting color."
            },
            {
              "workflow_path": "Information Gathering (e.g., 'Contact Us' form)",
              "issue": "The contact form has too many required fields, leading to abandonment.",
              "recommendation": "Reduce form fields to essential information only; use progressive disclosure for optional fields."
            },
            {
              "workflow_path": "Navigation Clarity",
              "issue": "Navigation menu items are ambiguous or too numerous.",
              "recommendation": "Simplify navigation labels and group related items under clear categories."
            }
          ]
        }
        ```
        """
    ]

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_parts, generation_config={"response_mime_type": "application/json"})
        parsed_data = parse_gemini_json_response(response.text)
        return {"status": "success", "data": parsed_data}
    except Exception as e:
        print(f"Error in Workflow Agent: {e}")
        return {"status": "error", "message": f"Workflow analysis failed: {e}", "data": {}}