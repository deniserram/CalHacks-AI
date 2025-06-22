# backend/agents/accessibility_agent.py


# This agent focuses on WCAG (Web Content Accessibility Guidelines)
# and Responsive Design checks.


print(f"DEBUG: I am accessibility_agent.py, loaded from: {__file__}")


import os
from playwright.sync_api import sync_playwright
from lxml import html # Make sure lxml is installed: pip install lxml
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any


# --- Data Models ---
# These dataclasses define the structure of the analysis output.
# They are consistent with what your frontend expects to receive.


@dataclass
class WCAGAccessibilityIssue:
   """Represents a single WCAG accessibility issue found on a website."""
   issue: str
   element_description: str
   suggestion: str
   severity: str # e.g., 'critical', 'high', 'medium', 'low'
   wcag_criterion: Optional[str] = None # e.g., "1.1.1 Non-text Content"
   wcag_level: Optional[str] = None # e.g., "A", "AA", "AAA"
   html_snippet: Optional[str] = None # Relevant HTML snippet for context
   css_solution: Optional[str] = None # Example CSS fix


@dataclass
class ResponsiveDesignIssue:
   """Represents a responsive design issue found on a website."""
   issue: str
   element_description: str # Element causing the issue (e.g., "Main content area")
   suggestion: str
   severity: str # e.g., 'critical', 'high', 'medium', 'low'
   device_type: str # e.g., "mobile_small", "tablet"
   breakpoint_issue: Optional[bool] = None # True if issue appears at a specific breakpoint
   css_solution: Optional[str] = None # Example CSS fix
  
@dataclass
class BrowserCompatibility:
   """Represents browser compatibility status (conceptual)."""
   chrome: bool
   firefox: bool
   safari: bool
   edge: bool
   internet_explorer: bool = False # Always issues with IE, good to mark




@dataclass
class DeviceCompatibility:
   """Represents general device compatibility ratings."""
   mobile: str # e.g., "excellent", "good", "fair", "poor"
   tablet: str
   desktop: str


# Mock data models for other agents' output (kept for consistent output structure)
@dataclass
class TrustIndicator:
   type: str
   label: str
   icon: Optional[str] = None


@dataclass
class Review:
   reviewer: str
   date: str
   rating: int
   text: str


@dataclass
class WebsiteInfo:
   name: str
   url: str
   category: Optional[str] = None
   icon: Optional[str] = None


@dataclass
class WebsiteRating:
   overall_score: float
   total_reviews: int
   recommendation_percentage: int
   rating_breakdown: Dict[str, int]
   trust_indicators: List[TrustIndicator]
   recent_reviews: List[Review]
   website_info: WebsiteInfo


@dataclass
class AccessibilityAnalysisOutput:
   """Comprehensive output for website analysis by this agent."""
   accessibility_issues: List[WCAGAccessibilityIssue] = field(default_factory=list)
   responsive_design_issues: List[ResponsiveDesignIssue] = field(default_factory=list)
   summary: str = "Analysis complete."
   overall_rating: str = "good" # "excellent", "good", "fair", "poor"
   wcag_compliance_level: str = "AA" # "A", "AA", "AAA"
   mobile_accessibility_score: str = "good"
   automated_checks_performed: List[str] = field(default_factory=list)
   manual_review_needed: List[str] = field(default_factory=list)
   device_compatibility: DeviceCompatibility = field(default_factory=lambda: DeviceCompatibility(mobile="N/A", tablet="N/A", desktop="N/A"))
   browser_compatibility: BrowserCompatibility = field(default_factory=lambda: BrowserCompatibility(chrome=False, firefox=False, safari=False, edge=False))
   mobile_optimization_score: str = "N/A"
   desktop_optimization_score: str = "N/A"
  
   # WebsiteRating is typically from another agent, but included for complete output
   website_rating: WebsiteRating = field(default_factory=lambda: WebsiteRating(
       overall_score=0.0, total_reviews=0, recommendation_percentage=0, rating_breakdown={},
       trust_indicators=[], recent_reviews=[], website_info=WebsiteInfo(name="N/A", url="N/A")
   ))
   # Branding palette is NOT part of this agent's output
   # branding_palette: Dict[str, str] = field(default_factory=dict) # REMOVED


# --- Helper functions for Color Contrast Calculation (WCAG 2.x method) ---
# These functions are used for the contrast checker.
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
   """Converts a hex color string (e.g., #RRGGBB) to an RGB tuple."""
   hex_color = hex_color.lstrip('#')
   return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_linear(value: int) -> float:
   """Converts an sRGB component (0-255) to a linear-light component."""
   val_float = value / 255.0
   return val_float / 12.92 if val_float <= 0.03928 else ((val_float + 0.055) / 1.055) ** 2.4


def get_luminance(rgb: Tuple[int, int, int]) -> float:
   """Calculates the relative luminance of an RGB color (WCAG 2.x)."""
   R = rgb_to_linear(rgb[0])
   G = rgb_to_linear(rgb[1])
   B = rgb_to_linear(rgb[2])
   return 0.2126 * R + 0.7152 * G + 0.0722 * B


def get_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
   """Calculates the contrast ratio between two RGB colors (WCAG 2.x)."""
   L1 = get_luminance(rgb1)
   L2 = get_luminance(rgb2)
   # Add a small epsilon to avoid division by zero if L1+0.05 == L2+0.05
   return (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05) if min(L1,L2) + 0.05 > 0 else float('inf')




# --- Primary Analysis Function ---
def analyze_website_accessibility_and_responsive(url: str, screenshot_base64: Optional[str] = None, key_elements: Optional[List[Dict]] = None) -> AccessibilityAnalysisOutput:
   """
   Performs WCAG accessibility and responsive design checks on a given URL.
   screenshot_base64 and key_elements are accepted for consistent API with app.py's calls,
   but this agent primarily uses Playwright for its own scraping and live browser analysis.
   """
   print(f"DEBUG: accessibility_agent: Starting analysis for {url}")
   print(f"DEBUG: accessibility_agent: received screenshot_present={screenshot_base64 is not None}, elements_present={key_elements is not None}")


   issues: List[WCAGAccessibilityIssue] = []
   responsive_issues: List[ResponsiveDesignIssue] = []
   automated_checks: List[str] = []
   manual_reviews_needed: List[str] = []


   # Initialize output values
   overall_rating = "good"
   wcag_compliance_level = "AA"
   mobile_accessibility_score = "good"
   mobile_optimization_score = "good"
   desktop_optimization_score = "excellent"
   browser_comp = BrowserCompatibility(chrome=False, firefox=False, safari=False, edge=False, internet_explorer=False)


   page_content = ""
  
   # --- STEP 1: Use Playwright for live browser checks and HTML content ---
   try:
       with sync_playwright() as p:
           # Launch browser in headless mode (no visible UI)
           browser = p.chromium.launch(headless=True)
           page = browser.new_page()


           print(f"DEBUG: accessibility_agent: Navigating Playwright to {url}")
           page.goto(url, wait_until="networkidle", timeout=60000) # Wait for network idle, increased timeout
           page_content = page.content() # Get the full HTML content
           print(f"DEBUG: accessibility_agent: Playwright navigation successful for {url}.")


           # --- Browser Compatibility Check (Conceptual) ---
           browser_comp = BrowserCompatibility(chrome=True, firefox=True, safari=True, edge=True, internet_explorer=False)
           automated_checks.append("Browser Compatibility Check (Conceptual for modern browsers)")
           manual_reviews_needed.append("Cross-browser testing (Firefox, Safari, Edge, etc.) for full verification.")


           # --- Responsive Design Checks ---
           # Define common device viewports
           viewports = {
               "mobile_small": {"width": 320, "height": 568},  # iPhone 5/SE
   "mobile_large": {"width": 414, "height": 896},  # iPhone Plus / modern large phone
   "tablet": {"width": 768, "height": 1024},      # iPad portrait
   "desktop_small": {"width": 1024, "height": 768}, # Small desktop/laptop
}


           for device_name, viewport in viewports.items():
               page.set_viewport_size(viewport)
               page.wait_for_timeout(500) # Give page time to reflow


               # Check for horizontal scrollbars
               body_scroll_width = page.evaluate("document.body.scrollWidth")
               viewport_width = viewport['width'] # Use dictionary access for width
               if body_scroll_width > viewport_width + 10: # Allow a small margin
                   responsive_issues.append(ResponsiveDesignIssue(
                       issue="Horizontal scrolling detected",
                       element_description=f"Page body at {device_name} ({viewport.width}px)", # Use viewport['width'] here too
                       suggestion="Ensure content reflows vertically and doesn't overflow horizontally. Use `max-width: 100%; overflow-x: hidden;` on containers, and responsive units (%, vw) for widths.",
                       severity="high",
                       device_type=device_name,
                       breakpoint_issue=True,
                       css_solution="body { overflow-x: hidden; } /* Or specific containers with max-width: 100% */"
                   ))
              
               # Check for images not scaling (basic check)
               # Looks for images that don't have max-width:100% or similar responsive properties
               if "mobile" in device_name and page.locator("img:not([style*='max-width:100%']):not([width=''])").count() > 0:
                   responsive_issues.append(ResponsiveDesignIssue(
                       issue="Images may not be responsive",
                       element_description="Some images might not scale correctly",
                       suggestion="Ensure images use `max-width: 100%; height: auto;` in CSS to scale down on smaller screens.",
                       severity="medium",
                       device_type=device_name,
                       css_solution="img { max-width: 100%; height: auto; }"
                   ))
              
               # Example: Check for very small font sizes on mobile
               if "mobile" in device_name and page.evaluate('() => parseFloat(window.getComputedStyle(document.body).fontSize)') < 14:
                   responsive_issues.append(ResponsiveDesignIssue(
                       issue="Small font size on mobile",
                       element_description="Body text",
                       suggestion="Increase base font size on mobile for better readability (e.g., at least 16px).",
                       severity="low",
                       device_type=device_name,
                       css_solution="body { font-size: 16px; } @media (max-width: 768px) { body { font-size: 1rem; } }"
                   ))


           automated_checks.append("Responsive Design Checks (multiple viewports)")
           manual_reviews_needed.append("Thorough visual review of all breakpoints and interactive elements on real devices.")
          
           print(f"DEBUG: accessibility_agent: Playwright browser closed.")


   except Exception as e:
       print(f"ERROR: accessibility_agent: Playwright operation failed for {url}: {e}")
       # Print full traceback to stdout for debugging in the terminal
       import sys, traceback
       traceback.print_exc(file=sys.stdout)
       overall_rating = "poor"
       issues.append(WCAGAccessibilityIssue(
           issue="Website loading/rendering error",
           element_description="Entire page",
           suggestion=f"Could not load or render the page for analysis: {e}. Check URL or website availability.",
           severity="critical" # Changed to critical as it blocks all checks
       ))


   # --- STEP 2: Parse HTML (if available) and perform WCAG checks ---
   if page_content:
       tree = html.fromstring(page_content)


       # WCAG 1.1.1 Non-text Content - Alt text for images
       for img in tree.xpath('//img'):
           alt_text = img.get('alt')
           src = img.get('src', 'N/A')
           if not alt_text:
               issues.append(WCAGAccessibilityIssue(
                   issue="Missing alt text for image",
                   element_description=f"Image with src: {src}",
                   suggestion="Add descriptive `alt` text to images to convey their purpose to screen reader users (WCAG 1.1.1). If purely decorative, use `alt=\"\"`.",
                   severity="high",
                   wcag_criterion="1.1.1 Non-text Content",
                   wcag_level="A",
                   html_snippet=f'<img src="{src}">'
               ))
           elif not alt_text.strip(): # Empty alt text
                issues.append(WCAGAccessibilityIssue(
                   issue="Empty alt text for image",
                   element_description=f"Image with src: {src}",
                   suggestion="If decorative, use `alt=\"\"`. If content-bearing, add descriptive `alt` text (WCAG 1.1.1).",
                   severity="medium",
                   wcag_criterion="1.1.1 Non-text Content",
                   wcag_level="A",
                   html_snippet=f'<img src="{src}" alt="">'
               ))
       automated_checks.append("Alt Text Check (WCAG 1.1.1)")


       # WCAG 2.1.1 Keyboard Accessibility (conceptual check)
       # Check for interactive elements without tabindex or role when they should have them
       # This is a very basic check; full keyboard accessibility requires manual testing.
       interactive_elements_no_tabindex = tree.xpath('//a[not(@tabindex) and not(@href)] | //button[not(@tabindex)] | //input[not(@tabindex)]')
       if interactive_elements_no_tabindex:
           issues.append(WCAGAccessibilityIssue(
               issue="Potentially inaccessible interactive elements",
               element_description="Some links, buttons, or form controls may not be keyboard accessible.",
               suggestion="Ensure all interactive elements are reachable and operable via keyboard. Use semantic HTML elements or add `tabindex='0'` and appropriate ARIA roles (WCAG 2.1.1).",
               severity="high",
               wcag_criterion="2.1.1 Keyboard",
               wcag_level="A",
               html_snippet=html.tostring(interactive_elements_no_tabindex[0], encoding='unicode') if interactive_elements_no_tabindex else None
           ))
       manual_reviews_needed.append("Full Keyboard Navigation Testing (tab order, focus visibility, all controls operable).")
       automated_checks.append("Basic Interactive Element Check (WCAG 2.1.1)")


       # WCAG 1.4.3 Contrast (Minimum) - Automated check (simplified)
       # This is an improved automated check, but still simplified.
       # A comprehensive check needs to analyze *all* text against its *actual* background pixel.
       try:
           # Evaluate JavaScript to get computed styles for text/background of main elements
           contrast_data = page.evaluate('''
               () => {
                   const results = [];
                   const selectors = 'h1, h2, h3, h4, h5, h6, p, a, span, li, button, input[type="submit"], input[type="button"]';
                   document.querySelectorAll(selectors).forEach(el => {
                       const style = window.getComputedStyle(el);
                       const tagName = el.tagName;
                       const textContent = el.textContent ? el.textContent.trim().substring(0, 100) : '';
                      
                       // Skip if element has no text or is invisible
                       if (!textContent || style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) < 0.05) {
                           return;
                       }


                       // Get text color and computed background color
                       const textColor = style.color;
                       let bgColor = style.backgroundColor;
                      
                       // Traverse up the DOM to find a non-transparent background
                       let currentEl = el;
                       while (currentEl && (bgColor === 'rgba(0, 0, 0, 0)' || bgColor === 'transparent')) {
                           currentEl = currentEl.parentElement;
                           if (currentEl) {
                               bgColor = window.getComputedStyle(currentEl).backgroundColor;
                           }
                       }


                       results.push({
                           tagName: tagName,
                           textContent: textContent,
                           textColor: textColor,
                           bgColor: bgColor
                       });
                   });
                   return results;
               }
           ''')


           for item in contrast_data:
               try:
                   # Convert 'rgb(r, g, b)' or 'rgba(r, g, b, a)' to (r, g, b) tuple
                   def parse_rgb_string(rgb_str):
                       if rgb_str.startswith('rgb'):
                           parts = rgb_str.replace('rgb(', '').replace('rgba(', '').replace(')', '').split(',')
                           return (int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip()))
                       return (0,0,0) # Default if parsing fails or invalid color


                   fg_rgb = parse_rgb_string(item['textColor'])
                   bg_rgb = parse_rgb_string(item['bgColor'])
                  
                   contrast = get_contrast_ratio(fg_rgb, bg_rgb)
                  
                   # WCAG 1.4.3 minimum contrast: 4.5:1 for normal text, 3:1 for large text.
                   # This check simplifies to 4.5:1 for all, as font size is harder to determine accurately here.
                   if contrast < 4.5:
                       issues.append(WCAGAccessibilityIssue(
                           issue="Insufficient color contrast",
                           element_description=f"Text: '{item['textContent']}' (Tag: {item['tagName']})",
                           suggestion=f"Ensure text and background colors meet minimum contrast ratios. WCAG 1.4.3 requires 4.5:1 for normal text. Current contrast: {contrast:.2f}:1. Adjust colors to improve readability.",
                           severity="medium",
                           wcag_criterion="1.4.3 Contrast (Minimum)",
                           wcag_level="AA",
                           css_solution=f"/* Example: increase contrast */ color: {item['textColor']}; background-color: {item['bgColor']};"
                       ))
               except Exception as ce:
                   print(f"WARNING: Could not process contrast for item {item}: {ce}")
           automated_checks.append("Color Contrast Check (WCAG 1.4.3 - Automated Simplified)")
           manual_reviews_needed.append("Manual verification of color contrast, especially for complex backgrounds or small text.")
       except Exception as e:
           print(f"ERROR: Failed to perform JavaScript evaluation for contrast check: {e}")
           issues.append(WCAGAccessibilityIssue(
               issue="Automated contrast check failed",
               element_description="Entire page",
               suggestion=f"Could not perform automated contrast checks due to script error: {e}",
               severity="low"
           ))




       # WCAG 2.4.2 Page Titled
       if not tree.xpath('//head/title/text()'):
           issues.append(WCAGAccessibilityIssue(
               issue="Missing page title",
               element_description="HTML head",
               suggestion="Every web page should have a unique and descriptive title in the `<title>` tag for better navigation and context (WCAG 2.4.2).",
               severity="high",
               wcag_criterion="2.4.2 Page Titled",
               wcag_level="A",
               html_snippet="<head>\n  <title>Your Page Title</title>\n</head>"
           ))
       automated_checks.append("Page Title Check (WCAG 2.4.2)")


       # WCAG 3.1.1 Language of Page
       html_element = tree.xpath('//html')[0] if tree.xpath('//html') else None
       if not (html_element and html_element.get('lang')):
           issues.append(WCAGAccessibilityIssue(
               issue="Missing page language declaration",
               element_description="HTML tag",
               suggestion="Declare the primary human language of the web page using the `lang` attribute on the `<html>` element (WCAG 3.1.1) for screen reader pronunciation.",
               severity="medium",
               wcag_criterion="3.1.1 Language of Page",
               wcag_level="A",
               html_snippet="<html lang=\"en\">"
           ))
       automated_checks.append("Language Declaration Check (WCAG 3.1.1)")
   else:
       print("WARNING: No HTML content available for detailed WCAG checks.")
       manual_reviews_needed.append("No automated WCAG checks performed due to lack of HTML content.")




   # --- STEP 3: Overall Summary based on findings ---
   if not issues and not responsive_issues:
       overall_summary = "The website demonstrates excellent accessibility and responsive design across various devices and browsers, adhering to WCAG AA standards. No critical issues were found."
       overall_rating = "excellent"
       mobile_accessibility_score = "excellent"
       mobile_optimization_score = "excellent"
   elif len(issues) < 3 and len(responsive_issues) < 2:
       overall_summary = "The website has good foundational accessibility and responsive design, but a few minor issues were identified. Addressing these will further enhance usability for all users."
       overall_rating = "good"
   else:
       overall_summary = f"Several accessibility and responsive design issues were found ({len(issues)} accessibility, {len(responsive_issues)} responsive). Addressing these is highly recommended to improve user experience and WCAG compliance."
       overall_rating = "fair" if (len(issues) + len(responsive_issues)) > 5 else "poor"
       mobile_accessibility_score = "fair"
       mobile_optimization_score = "fair"


   # --- Construct and return the result object ---
   analysis_output = AccessibilityAnalysisOutput(
       accessibility_issues=issues,
       responsive_design_issues=responsive_issues,
       summary=overall_summary,
       overall_rating=overall_rating,
       wcag_compliance_level=wcag_compliance_level,
       mobile_accessibility_score=mobile_accessibility_score,
       automated_checks_performed=automated_checks,
       manual_review_needed=manual_reviews_needed,
       device_compatibility=DeviceCompatibility(
           mobile=mobile_optimization_score,
           tablet="good", # Mock or refine if you add tablet specific checks
           desktop=desktop_optimization_score
       ),
       browser_compatibility=browser_comp,
       mobile_optimization_score=mobile_optimization_score,
       desktop_optimization_score=desktop_optimization_score,


       # Mock Website Rating (as per original JS code, this would be from another agent)
       website_rating=WebsiteRating(
           overall_score=4.6,
           total_reviews=2847,
           recommendation_percentage=94,
           rating_breakdown={"5": 1936, "4": 626, "3": 199, "2": 57, "1": 29},
           trust_indicators=[
               TrustIndicator(type="verified", label="Verified Business", icon="✓"),
               TrustIndicator(type="security", label="SSL Secured", icon="🔒"),
               TrustIndicator(type="premium", label="Premium Member", icon="⭐")
           ],
           recent_reviews=[
               Review(reviewer="Sarah M.", date="3 days ago", rating=5, text="Excellent customer service and fast shipping!"),
               Review(reviewer="Mike R.", date="1 week ago", rating=4, text="Good selection of products and reasonable prices."),
               Review(reviewer="Jennifer L.", date="2 weeks ago", rating=5, text="Outstanding experience! Accessibility features work perfectly.")
           ],
           website_info=WebsiteInfo(name="Mock Website", url=url, category="General", icon="🌐")
       )
   )
   print(f"DEBUG: accessibility_agent: Analysis complete for {url}. Issues found: {len(issues) + len(responsive_issues)}")
   browser.close()
   return analysis_output


# Example of how you would call this (for local testing purposes)
if __name__ == '__main__':
   import json # Import here for local testing block


   # Ensure a 'screenshots' directory exists for Playwright if needed (e.g., for error screenshots)
   if not os.path.exists('screenshots'):
       os.makedirs('screenshots')


   test_url_good = "https://www.w3.org/WAI/fundamentals/accessibility-intro/"
   test_url_needs_work = "https://example.com" # This one is good for showing alt text issues, etc.


   print(f"Analyzing: {test_url_good}")
   # Call without screenshot_base64/key_elements, as this agent will scrape itself
   results_good = analyze_website_accessibility_and_responsive(test_url_good, None, None)
   print(json.dumps(asdict(results_good), indent=2, default=str))


   print("\n" + "="*50 + "\n")


   print(f"Analyzing: {test_url_needs_work}")
   results_needs_work = analyze_website_accessibility_and_responsive(test_url_needs_work, None, None)
   print(json.dumps(asdict(results_needs_work), indent=2, default=str))





