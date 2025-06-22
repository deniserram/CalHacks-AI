# backend/agents/workflow_agent.py
from playwright.sync_api import sync_playwright
import time # For slight delays to observe navigation

# If you integrate an LLM, you'd import it here, e.g.:
# from openai import OpenAI
# openai_client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

def check_user_workflow(url: str) -> dict:
    """
    Checks basic user workflows by simulating navigation based on common goals.
    Provides suggestions if navigation paths are unclear or break.
    This agent heavily relies on Playwright to simulate browser interactions.
    The 'AI' part can be rule-based or an LLM if integrated.
    """
    suggestions = []
    issues_found = False

    # Define simple workflow goals and expected keywords/selectors
    workflows = [
        {"name": "Find 'About Us' Page", "target_keywords": ["about", "our story", "company"], "success_url_part": "about"},
        {"name": "Find 'Contact' Page", "target_keywords": ["contact", "reach us", "support"], "success_url_part": "contact"},
        # Add more simplified workflows here
        # {"name": "Navigate to Login/Sign Up", "target_keywords": ["login", "sign up", "register"], "success_url_part": "login"}
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            for workflow in workflows:
                page.goto(url, wait_until="load") # Start fresh for each workflow
                time.sleep(1) # Give page a moment to load

                print(f"\n--- Workflow: {workflow['name']} for {url} ---")
                workflow_success = False

                # --- AI Agent Logic (Simplified / Placeholder) ---
                # For a hackathon, this "AI" part could be very basic:
                # 1. Look for text matches in link/button elements.
                # 2. Use LLM to pick the best link if you have an API set up.

                target_found = False
                for keyword in workflow['target_keywords']:
                    # Look for links or buttons containing the keyword (case-insensitive)
                    locator = page.locator(f"a:has-text('{keyword}', true), button:has-text('{keyword}', true)")
                    if locator.count() > 0:
                        try:
                            # Prioritize visible links
                            target_element = locator.first
                            if target_element.is_visible():
                                print(f"  Found '{keyword}' link/button: {target_element.text_content()}")
                                target_element.click()
                                page.wait_for_load_state('networkidle', timeout=5000) # Wait for navigation
                                workflow_success = True
                                target_found = True
                                break # Move to next workflow if clicked
                        except Exception as click_error:
                            print(f"  Failed to click '{keyword}': {click_error}")
                            pass # Try next keyword

                if workflow_success and workflow['success_url_part'].lower() in page.url.lower():
                    suggestions.append(f"Workflow '{workflow['name']}': Successfully navigated to expected page ({page.url}).")
                elif workflow_success and workflow['success_url_part'].lower() not in page.url.lower():
                     suggestions.append(f"Workflow '{workflow['name']}': Navigated after click, but did not reach expected URL (Current: {page.url}). Check navigation clarity.")
                     issues_found = True
                elif not target_found:
                    suggestions.append(f"Workflow '{workflow['name']}': Could not find a clear link/button related to '{', '.join(workflow['target_keywords'])}'. Navigation may be unclear.")
                    issues_found = True
                else:
                    suggestions.append(f"Workflow '{workflow['name']}': Failed to complete. Check page for unexpected redirects or dynamic content issues.")
                    issues_found = True


                # --- LLM Integration Idea (Advanced, if you have time/API access) ---
                # This would involve sending page HTML/text to an LLM and asking it
                # to identify the best element to click for a given goal.
                # html_content = page.content()
                # prompt = f"Given this HTML, identify the CSS selector of the most relevant link or button to '{workflow['name']}'. Respond only with the CSS selector."
                #
                # try:
                #     llm_response = openai_client.chat.completions.create(
                #         model="gpt-3.5-turbo",
                #         messages=[
                #             {"role": "system", "content": "You are a helpful assistant that identifies HTML elements."},
                #             {"role": "user", "content": f"{prompt}\n\nHTML:\n{html_content[:2000]}"} # Send part of HTML
                #         ],
                #         max_tokens=50
                #     )
                #     selector_from_llm = llm_response.choices[0].message.content.strip()
                #     print(f"LLM suggested selector: {selector_from_llm}")
                #     # Then try to click that selector using Playwright
                #     # ... (logic to click and check result) ...
                # except Exception as llm_error:
                #     print(f"LLM interaction failed: {llm_error}")
                #     suggestions.append(f"Workflow '{workflow['name']}': LLM could not assist. Navigation might be too complex or unclear for AI analysis.")
                #     issues_found = True

            browser.close()

    except Exception as e:
        suggestions.append(f"Error during workflow analysis: {e}")
        issues_found = True

    status = "completed with issues" if issues_found else "completed successfully"
    return {"status": status, "suggestions": suggestions}

# Example of how you would call this:
# if __name__ == '__main__':
#     test_url = "https://www.berkeley.edu/" # Test a site with clear navigation
#     # Make sure to install 'openai' if you uncomment LLM part: pip install openai
#     results = check_user_workflow(test_url)
#     import json
#     print(json.dumps(results, indent=2))