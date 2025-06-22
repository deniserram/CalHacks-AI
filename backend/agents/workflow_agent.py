import google.generativeai as genai
from playwright.sync_api import sync_playwright
import time
from utils import get_image_parts, parse_gemini_json_response


def run_gemini_workflow_analysis(url, screenshot_base64, key_elements):
    """
    Gemini-based analysis of user workflow and CTA clarity.
    """
    print(f"Running Gemini Workflow Agent for: {url}")
    
    image_parts = get_image_parts(screenshot_base64)

    workflow_elements_context = []
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
            }
          ]
        }
        ```"""
    ]

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_parts, generation_config={"response_mime_type": "application/json"})
        parsed_data = parse_gemini_json_response(response.text)
        return {"status": "success", "mode": "gemini", "data": parsed_data}
    except Exception as e:
        print(f"Error in Workflow Agent (Gemini): {e}")
        return {"status": "error", "mode": "gemini", "message": str(e), "data": {}}


def run_playwright_workflow_analysis(url):
    """
    Playwright-based simulation of user navigation.
    """
    print(f"Running Playwright Workflow Agent for: {url}")

    suggestions = []
    issues_found = False

    workflows = [
        {"name": "Find 'About Us' Page", "target_keywords": ["about", "our story", "company"], "success_url_part": "about"},
        {"name": "Find 'Contact' Page", "target_keywords": ["contact", "reach us", "support"], "success_url_part": "contact"},
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            for workflow in workflows:
                page.goto(url, wait_until="load")
                time.sleep(1)
                print(f"\n--- Workflow: {workflow['name']} for {url} ---")
                workflow_success = False
                target_found = False

                for keyword in workflow['target_keywords']:
                    locator = page.locator(f"a:has-text('{keyword}'), button:has-text('{keyword}')")
                    if locator.count() > 0:
                        try:
                            target_element = locator.first
                            if target_element.is_visible():
                                print(f"  Found '{keyword}' link/button: {target_element.text_content()}")
                                target_element.click()
                                page.wait_for_load_state('networkidle', timeout=5000)
                                workflow_success = True
                                target_found = True
                                break
                        except Exception as click_error:
                            print(f"  Failed to click '{keyword}': {click_error}")

                if workflow_success and workflow['success_url_part'].lower() in page.url.lower():
                    suggestions.append(f"Workflow '{workflow['name']}': Successfully navigated to expected page ({page.url}).")
                elif workflow_success:
                    suggestions.append(f"Workflow '{workflow['name']}': Navigated, but did not reach expected URL (Current: {page.url}).")
                    issues_found = True
                elif not target_found:
                    suggestions.append(f"Workflow '{workflow['name']}': Could not find a clear link/button for '{', '.join(workflow['target_keywords'])}'.")
                    issues_found = True
                else:
                    suggestions.append(f"Workflow '{workflow['name']}': Clicked but did not complete as expected.")
                    issues_found = True

            browser.close()

    except Exception as e:
        suggestions.append(f"Error during workflow analysis: {e}")
        issues_found = True

    status = "completed with issues" if issues_found else "completed successfully"
    return {"status": status, "mode": "playwright", "suggestions": suggestions}


def check_user_workflow(url, screenshot_base64=None, key_elements=None, mode="gemini"):
    """
    Unified entry point for workflow analysis.
    Use mode='gemini' or mode='playwright'.
    """
    if mode == "playwright":
        return run_playwright_workflow_analysis(url)
    else:
        return run_gemini_workflow_analysis(url, screenshot_base64, key_elements or [])
