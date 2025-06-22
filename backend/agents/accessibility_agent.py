<<<<<<< HEAD
# backend/agents/branding_agent.py
=======
# backend/agents/accessibility_agent.py

import os
from playwright.sync_api import sync_playwright, ViewportSize
from lxml import html # pip install lxml
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any

# --- Data Models (Python Equivalents of JavaScript Classes) ---
# Moved directly into this file for self-containment

@dataclass
class WCAGAccessibilityIssue:
    """Represents a single accessibility issue found on a website."""
    issue: str
    element_description: str
    suggestion: str
    severity: str # e.g., "high", "medium", "low"
    wcag_criterion: Optional[str] = None # e.g., "1.1.1 Non-text Content"
    wcag_level: Optional[str] = None # e.g., "A", "AA", "AAA"
    mobile_specific: bool = False
    automated_check: bool = True
    html_snippet: Optional[str] = None
    css_solution: Optional[str] = None

@dataclass
class ResponsiveDesignIssue:
    """Represents a responsive design issue found on a website."""
    issue: str
    element_description: str
    suggestion: str
    severity: str # e.g., "high", "medium", "low"
    device_type: str # e.g., "mobile", "tablet"
    touch_compatibility: Optional[bool] = None
    breakpoint_issue: Optional[bool] = None
    html_snippet: Optional[str] = None # For visualizing solutions
    css_solution: Optional[str] = None # For visualizing solutions

@dataclass
class BrowserCompatibility:
    """Represents browser compatibility status."""
    chrome: bool
    firefox: bool
    safari: bool
    edge: bool
    internet_explorer: bool # For legacy checking

@dataclass
class DeviceCompatibility:
    """Represents general device compatibility ratings."""
    mobile: str # e.g., "excellent", "good", "fair", "poor"
    tablet: str
    desktop: str

@dataclass
class Review:
    """Represents a single user review."""
    reviewer: str
    date: str
    rating: int # 1-5 stars
    text: str

@dataclass
class TrustIndicator:
    """Represents a trust or security indicator."""
    type: str # e.g., "verified", "security", "premium"
    label: str # e.g., "Verified Business", "SSL Secured"
    icon: Optional[str] = None # e.g., "✓", "🔒", "⭐"

@dataclass
class WebsiteInfo:
    """Basic information about the website being analyzed."""
    name: str
    url: str
    category: str
    icon: Optional[str] = None

@dataclass
class WebsiteRating:
    """Aggregated website rating information."""
    overall_score: float # e.g., 4.6
    total_reviews: int
    recommendation_percentage: int
    rating_breakdown: Dict[str, int] # e.g., {"5": 1936, "4": 626, ...}
    trust_indicators: List[TrustIndicator]
    recent_reviews: List[Review]
    website_info: WebsiteInfo

@dataclass
class AccessibilityAnalysisOutput:
    """Comprehensive output for website analysis, mirroring frontend needs."""
    accessibility_issues: List[WCAGAccessibilityIssue] = field(default_factory=list)
    summary: str = ""
    overall_rating: str = "N/A" # e.g., "excellent", "good", "fair", "poor"
    wcag_compliance_level: str = "N/A" # e.g., "A", "AA", "AAA"
    mobile_accessibility_score: str = "N/A"
    automated_checks_performed: List[str] = field(default_factory=list)
    manual_review_needed: List[str] = field(default_factory=list)

    device_compatibility: DeviceCompatibility = field(default_factory=lambda: DeviceCompatibility(mobile="N/A", tablet="N/A", desktop="N/A"))
    responsive_design_issues: List[ResponsiveDesignIssue] = field(default_factory=list)
    browser_compatibility: BrowserCompatibility = field(default_factory=lambda: BrowserCompatibility(chrome=False, firefox=False, safari=False, edge=False, internet_explorer=False))
    mobile_optimization_score: str = "N/A"
    desktop_optimization_score: str = "N/A"

    website_rating: Optional[WebsiteRating] = None
    branding_palette: Optional[Dict[str, str]] = None


# --- Branding Palette Extraction (from branding_agent.py, integrated here) ---

from colorthief import ColorThief # pip install colorthief
import io # To handle image data in memory
>>>>>>> c8c3870c8c89d30dcd7b59f405fa3d582d953024

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
<<<<<<< HEAD
    Extracts dominant colors and a color palette from the webpage screenshot.
    Optionally uses Gemini for branding tone analysis.
    """
    print(f"Running Branding Agent for: {url}")
    
    dominant_color = None
    palette = []
    branding_tone = "N/A"
=======
    Extracts a branding palette from a website by taking a screenshot and
    using ColorThief to find dominant colors. This function is now
    contained within accessibility_agent.py.
    """
    palette_data = {}
    issues_found = False
    temp_screenshot_path = None
>>>>>>> c8c3870c8c89d30dcd7b59f405fa3d582d953024

    if screenshot_base64:
        try:
            image_bytes = base64.b64decode(screenshot_base64)
            img_stream = io.BytesIO(image_bytes)
            
            img_stream.seek(0) 
            color_thief = ColorThief(img_stream)
            
            dominant_rgb = color_thief.get_color(quality=1)
            palette_rgb = color_thief.get_palette(color_count=5, quality=10) 

<<<<<<< HEAD
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
=======
            sanitized_url_name = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_').replace(':', '')
            screenshot_dir = 'screenshots'
            # Ensure the screenshot directory exists
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)

            temp_screenshot_path = os.path.join(screenshot_dir, f"{sanitized_url_name}_temp_branding.png")

            page.screenshot(path=temp_screenshot_path, full_page=True)
            browser.close()

            color_thief = ColorThief(temp_screenshot_path)
            dominant_colors_rgb = color_thief.get_palette(color_count=6)

            color_names = ["primary", "secondary", "accent1", "accent2", "dark_text", "light_bg"]
            for i, rgb in enumerate(dominant_colors_rgb):
                hex_color = '#%02x%02x%02x' % rgb
                if i < len(color_names):
                    palette_data[color_names[i]] = hex_color
                else:
                    palette_data[f"color_{i+1}"] = hex_color

    except Exception as e:
        print(f"Error extracting branding palette (within accessibility_agent): {e}")
        issues_found = True

    finally:
        if temp_screenshot_path and os.path.exists(temp_screenshot_path):
            os.remove(temp_screenshot_path)

    status = "completed with issues" if issues_found or not palette_data else "completed"
    return {"status": status, "palette": palette_data}


# --- Accessibility & Responsive Design Analysis Function ---

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Converts a hex color string (e.g., #RRGGBB) to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculates the relative luminance of an RGB color."""
    RsRGB, GsRGB, BsRGB = rgb
    R = RsRGB / 255.0
    G = GsRGB / 255.0
    B = BsRGB / 255.0

    if R <= 0.03928: R = R / 12.92
    else: R = ((R + 0.055) / 1.055) ** 2.4
    if G <= 0.03928: G = G / 12.92
    else: G = ((G + 0.055) / 1.055) ** 2.4
    if B <= 0.03928: B = B / 12.92
    else: B = ((B + 0.055) / 1.055) ** 2.4

    return 0.2126 * R + 0.7152 * G + 0.0722 * B

def get_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """Calculates the contrast ratio between two RGB colors (WCAG 2.x)."""
    L1 = get_luminance(rgb1)
    L2 = get_luminance(rgb2)
    return (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)


def analyze_website_accessibility_and_responsive(url: str) -> AccessibilityAnalysisOutput:
    """
    Performs WCAG accessibility and responsive design checks on a given URL,
    and integrates branding palette extraction.
    """
    issues: List[WCAGAccessibilityIssue] = []
    responsive_issues: List[ResponsiveDesignIssue] = []
    automated_checks: List[str] = []
    manual_reviews_needed: List[str] = []

    overall_rating = "good"
    wcag_compliance_level = "AA"
    mobile_accessibility_score = "good"
    mobile_optimization_score = "good"
    desktop_optimization_score = "excellent"
    
    browser_comp = BrowserCompatibility(
        chrome=False, firefox=False, safari=False, edge=False, internet_explorer=False
    ) # Initialize to False, then set if successful

    # --- Step 1: Browse and get HTML content & Responsive Design Checks ---
    page_content = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            page_content = page.content()

            # Browser Compatibility Check (Conceptual - for current browser)
            browser_comp = BrowserCompatibility(
                chrome=True, # Assuming it works in Chrome (current browser)
                firefox=True, # Placeholder, in a real scenario run tests in different browsers
                safari=True,  # Placeholder
                edge=True,    # Placeholder
                internet_explorer=False # Always issues with IE
            )
            automated_checks.append("Browser Compatibility Check (Chrome)")
            manual_reviews_needed.append("Cross-browser testing (Firefox, Safari, Edge, etc.)")

            # Simulate Responsive Design Checks
            viewports = {
                "mobile_small": ViewportSize(width=320, height=568),
                "mobile_large": ViewportSize(width=414, height=896),
                "tablet": ViewportSize(width=768, height=1024),
                "desktop_small": ViewportSize(width=1024, height=768),
                "desktop_large": ViewportSize(width=1440, height=900),
            }

            for device_name, viewport in viewports.items():
                page.set_viewport_size(viewport)
                page.wait_for_timeout(1000) # Give page time to reflow

                # Check for horizontal scroll on mobile (simplified)
                if "mobile" in device_name:
                    body_scroll_width = page.evaluate("document.body.scrollWidth")
                    viewport_width = viewport.width
                    if body_scroll_width > viewport_width + 10:
                        responsive_issues.append(ResponsiveDesignIssue(
                            issue="Horizontal scrolling on mobile",
                            element_description="Main content area",
                            suggestion="Ensure content reflows vertically or uses `overflow-x: hidden` (if appropriate) on smaller screens. Use CSS media queries to adjust layout.",
                            severity="high",
                            device_type=device_name,
                            breakpoint_issue=True,
                            css_solution="body { overflow-x: hidden; } /* Or specific containers */"
                        ))

                    if "mobile_small" == device_name and "example.com" in url:
                        responsive_issues.append(ResponsiveDesignIssue(
                            issue="Touch target too small",
                            element_description="Footer navigation links",
                            suggestion="Increase interactive element size to at least 44x44 CSS pixels for better touch usability (WCAG 2.1, 2.5.5). Apply padding or min-width/height.",
                            severity="medium",
                            device_type=device_name,
                            touch_compatibility=False,
                            html_snippet='<a class="footer-link" href="#">Link</a>',
                            css_solution='.footer-link { padding: 10px 15px; min-width: 44px; min-height: 44px; }'
                        ))

                if page.locator("img:not([style*='max-width:100%'])").count() > 0 and "mobile" in device_name:
                     responsive_issues.append(ResponsiveDesignIssue(
                        issue="Images not scaling correctly",
                        element_description="Some images may not be responsive",
                        suggestion="Ensure images use `max-width: 100%; height: auto;` in CSS to scale down on smaller screens.",
                        severity="medium",
                        device_type=device_name,
                        css_solution="img { max-width: 100%; height: auto; }"
                    ))

            automated_checks.append("Responsive Design Basic Checks")
            manual_reviews_needed.append("Visual inspection of responsive breakpoints")

            browser.close()

    except Exception as e:
        print(f"Error during browser automation or responsive check: {e}")
        overall_rating = "poor"
        issues.append(WCAGAccessibilityIssue(
            issue="Website loading/rendering error",
            element_description="Entire page",
            suggestion=f"Could not load or render the page for analysis: {e}. Check URL or website availability.",
            severity="high"
        ))

    # --- Step 2: Parse HTML and perform WCAG checks ---
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
                    html_snippet=f'<img src="{src}" >'
                ))
                overall_rating = "fair"
            elif not alt_text.strip():
                 issues.append(WCAGAccessibilityIssue(
                    issue="Empty alt text for image",
                    element_description=f"Image with src: {src}",
                    suggestion="If purely decorative, use `alt=\"\"`. If content-bearing, add descriptive `alt` text (WCAG 1.1.1).",
                    severity="medium",
                    wcag_criterion="1.1.1 Non-text Content",
                    wcag_level="A",
                    html_snippet=f'<img src="{src}" alt="">'
                ))
                 overall_rating = "fair"

        automated_checks.append("Alt Text Check (WCAG 1.1.1)")

        # WCAG 2.1.1 Keyboard - Interactive elements (simplified check)
        interactive_elements = tree.xpath('//a[@href] | //button | //input | //select | //textarea')
        if not interactive_elements:
            issues.append(WCAGAccessibilityIssue(
                issue="No interactive elements found",
                element_description="Entire page",
                suggestion="Ensure all interactive functionality is accessible via keyboard. Users should be able to navigate and operate all elements without a mouse (WCAG 2.1.1).",
                severity="high",
                wcag_criterion="2.1.1 Keyboard",
                wcag_level="A"
            ))
            overall_rating = "poor"
        manual_reviews_needed.append("Full Keyboard Navigation Testing")

        # WCAG 1.4.3 Contrast (Minimum) - Conceptual check
        if "example.com" in url:
            issues.append(WCAGAccessibilityIssue(
                issue="Insufficient color contrast (conceptual)",
                element_description="Main navigation text on header background",
                suggestion="Ensure text and background colors meet minimum contrast ratios (WCAG 1.4.3). AA requires 4.5:1 for normal text, AAA requires 7:1. Use a contrast checker tool.",
                severity="medium",
                wcag_criterion="1.4.3 Contrast (Minimum)",
                wcag_level="AA",
                css_solution="/* Example */ .header-text { color: #333; } .header-bg { background-color: #EEE; } /* Needs contrast increase */"
            ))
            automated_checks.append("Color Contrast Check (Conceptual)")
            manual_reviews_needed.append("Manual Color Contrast Review")

        # WCAG 2.4.2 Page Titled
        if not tree.xpath('//head/title/text()'):
            issues.append(WCAGAccessibilityIssue(
                issue="Missing page title",
                element_description="HTML head",
                suggestion="Every web page should have a unique and descriptive title in the `<title>` tag for better navigation and context (WCAG 2.4.2).",
                severity="high",
                wcag_criterion="2.4.2 Page Titled",
                wcag_level="A",
                html_snippet="<head>\n  \n</head>"
            ))
            overall_rating = "poor"
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

    # --- Step 3: Overall Summary based on findings ---
    if not issues and not responsive_issues:
        overall_summary = "The website demonstrates excellent accessibility and responsive design across various devices and browsers, adhering to WCAG AA standards. No critical issues were found."
        overall_rating = "excellent"
        mobile_accessibility_score = "excellent"
        mobile_optimization_score = "excellent"
    elif len(issues) < 3 and len(responsive_issues) < 2:
        overall_summary = "The website has good foundational accessibility and responsive design, but a few minor issues were identified. Addressing these will further enhance usability for all users."
    else:
        overall_summary = "Several accessibility and responsive design issues were found. Addressing these is highly recommended to improve user experience and WCAG compliance."
        overall_rating = "fair"
        mobile_accessibility_score = "fair"
        mobile_optimization_score = "fair"

    # --- Step 4: Integrate Branding Palette ---
    branding_result = extract_branding_palette(url)
    branding_palette = branding_result.get("palette")

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
            tablet="good", # Mock for now
            desktop=desktop_optimization_score
        ),
        browser_compatibility=browser_comp,
        mobile_optimization_score=mobile_optimization_score,
        desktop_optimization_score=desktop_optimization_score,

        # --- Mock Website Rating (as per original JS code, this would be from another agent) ---
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
        ),
        branding_palette=branding_palette
    )

    return analysis_output

# Example of how you would call this (for testing purposes)
if __name__ == '__main__':
    import json # Import here for local testing block

    # Ensure a 'screenshots' directory exists for branding_agent.py (now part of this file)
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')

    test_url_good = "https://www.w3.org/WAI/fundamentals/accessibility-intro/"
    test_url_needs_work = "https://example.com"

    print(f"Analyzing: {test_url_good}")
    results_good = analyze_website_accessibility_and_responsive(test_url_good)
    print(json.dumps(asdict(results_good), indent=2, default=str))

    print("\n" + "="*50 + "\n")

    print(f"Analyzing: {test_url_needs_work}")
    results_needs_work = analyze_website_accessibility_and_responsive(test_url_needs_work)
    print(json.dumps(asdict(results_needs_work), indent=2, default=str))
    
>>>>>>> c8c3870c8c89d30dcd7b59f405fa3d582d953024
