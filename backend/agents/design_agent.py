import google.generativeai as genai
from utils import get_image_parts, parse_gemini_json_response
import json # Import json for better error handling during LLM response parsing

# --- Helper function for refined color palette extraction with proportions (no change) ---
def extract_colors_from_key_elements_refined(key_elements, num_colors=5): 
    color_counts = {}
    total_colors_considered = 0
    
    for e in key_elements:
        styles = e.get('computed_styles', {})
        bg_color = styles.get('backgroundColor')
        text_color = styles.get('color')

        current_element_colors = []
        if bg_color:
            current_element_colors.append(bg_color)
        if text_color:
            current_element_colors.append(text_color)
            
        for color in current_element_colors:
            if color in ['transparent', 'initial', 'rgba(0, 0, 0, 0)', 'rgb(255, 255, 255)', 'rgb(0, 0, 0)']:
                continue
            
            color_counts[color] = color_counts.get(color, 0) + 1
            total_colors_considered += 1
            
    sorted_colors = sorted(color_counts.items(), key=lambda item: item[1], reverse=True)
    
    dominant_palette_with_proportions = []
    sum_of_selected_counts = sum(count for color, count in sorted_colors[:num_colors])
    if sum_of_selected_counts == 0:
        return []

    for color, count in sorted_colors[:num_colors]:
        proportion = round(count / sum_of_selected_counts, 2)
        dominant_palette_with_proportions.append({"color": color, "proportion": proportion})
    
    return dominant_palette_with_proportions


def analyze_design(url, screenshot_base64, key_elements):
    """
    Analyzes the design of a webpage using DOM data and Gemini Vision Pro,
    extracting font guidelines, a refined color palette, the website's overall vibe,
    and design principle insights (Hierarchy, Repetition & Consistency).
    """
    print(f"Running Design Agent for: {url}")
    
    # --- Existing Data Extraction ---
    unique_font_families = set()
    raw_typography_guidelines = {
        'H1': [], 'H2': [], 'P': []
    }
    extracted_color_palette_with_proportions = extract_colors_from_key_elements_refined(key_elements, num_colors=5)

    SYSTEM_FONTS = [
        'sans-serif', 'serif', 'monospace', 'cursive', 'fantasy', 
        '-apple-system', 'BlinkMacSystemFont', 'system-ui', 
        'Segoe UI Symbol', 'Segoe UI Emoji', 'Twemoji Mozilla', 
        'Roboto', 'Noto Sans', 
        'Arial', 'Helvetica', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Georgia', 'Times New Roman', 'Courier New',
        'Meiryo', 'Yu Gothic', 'Microsoft YaHei', 'Apple Color Emoji' 
    ]

    # --- Metrics Collection for Hierarchy & Consistency ---
    h1_font_sizes = []
    h2_font_sizes = []
    p_font_sizes = []
    cta_elements_for_llm = [] # For LLM to assess prominence & consistency
    
    # NEW: For consistency checks
    h1_styles_found = {} # {font_size_font_weight_font_family: count}
    h2_styles_found = {}
    p_styles_found = {}
    button_styles_found = {} # {bg_color_text_color_font_size_font_weight: count}
    link_styles_found = {} # For A tags acting as links

    for e in key_elements:
        if e.get('text_content') and e.get('computed_styles'):
            styles = e['computed_styles']
            
            # Existing: Collect unique font families and raw guidelines
            font_family_raw = styles.get('fontFamily')
            if font_family_raw:
                individual_fonts = [f.strip().strip("'\"") for f in font_family_raw.split(',') if f.strip().strip("'\"")]
                found_primary_font = False
                for font in individual_fonts:
                    font_lower = font.lower()
                    if font in SYSTEM_FONTS: continue
                    if "segoe ui" in font_lower:
                        if "segoe ui emoji" in font_lower or "segoe ui symbol" in font_lower:
                            if "segoe ui" in [f.lower() for f in individual_fonts if f not in SYSTEM_FONTS]: continue
                            else: unique_font_families.add("Segoe UI"); found_primary_font = True; break
                        else: unique_font_families.add("Segoe UI"); found_primary_font = True; break
                    if not found_primary_font: unique_font_families.add(font); found_primary_font = True 

            tag_name = e['tag_name']
            
            # --- Hierarchy & Consistency: Heading Styles ---
            if tag_name in ['H1', 'H2', 'P']:
                guideline_entry = {
                    'text_content_sample': e['text_content'][:50] + '...' if e['text_content'] and len(e['text_content']) > 50 else e['text_content'] or 'N/A',
                    'font_family': font_family_raw, 
                    'font_size': styles.get('fontSize'),
                    'font_weight': styles.get('fontWeight'),
                    'color': styles.get('color'),
                    'line_height': styles.get('lineHeight')
                }
                if guideline_entry not in raw_typography_guidelines[tag_name]:
                    raw_typography_guidelines[tag_name].append(guideline_entry)

                # Collect font sizes for hierarchy check
                try:
                    font_size_px = float(styles.get('fontSize', '0px').replace('px', ''))
                    if tag_name == 'H1' and font_size_px > 0: h1_font_sizes.append(font_size_px)
                    elif tag_name == 'H2' and font_size_px > 0: h2_font_sizes.append(font_size_px)
                    elif tag_name == 'P' and font_size_px > 0: p_font_sizes.append(font_size_px)
                except ValueError: pass

                # For Consistency: store a unique key for the style
                style_key = f"{styles.get('fontSize')}_{styles.get('fontWeight')}_{font_family_raw}"
                if tag_name == 'H1': h1_styles_found[style_key] = h1_styles_found.get(style_key, 0) + 1
                elif tag_name == 'H2': h2_styles_found[style_key] = h2_styles_found.get(style_key, 0) + 1
                elif tag_name == 'P': p_styles_found[style_key] = p_styles_found.get(style_key, 0) + 1

            # --- Hierarchy & Consistency: CTA Styles ---
            if tag_name in ['BUTTON', 'A'] and e.get('text_content') and e['bounding_box']['width'] > 0 and e['bounding_box']['height'] > 0:
                # Heuristic for a CTA: significant size, bold text, or distinct color
                is_prominent_size = (e['bounding_box']['width'] > 80 and e['bounding_box']['height'] > 25) # Slightly adjusted thresholds
                is_bold = (styles.get('fontWeight') in ['bold', '700', '600'])
                # Rough check for distinct color (not just grey/white/black text on white/grey bg)
                bg_color = styles.get('backgroundColor', '').lower()
                text_color = styles.get('color', '').lower()
                is_distinct_bg_color = bg_color not in ['transparent', 'rgba(0, 0, 0, 0)', 'rgb(255, 255, 255)', 'rgb(240, 240, 240)', 'initial'] and len(bg_color) > 0
                is_distinct_text_color = text_color not in ['rgb(0, 0, 0)', 'rgb(51, 51, 51)', 'rgb(102, 102, 102)'] and len(text_color) > 0
                
                is_above_fold = e['bounding_box']['y'] < 800

                if is_prominent_size or is_bold or is_distinct_bg_color or is_distinct_text_color or is_above_fold:
                    cta_elements_for_llm.append({
                        "tag": tag_name,
                        "text": e['text_content'][:50], # Truncate for prompt
                        "bbox": {'x': e['bounding_box']['x'], 'y': e['bounding_box']['y']}, # Simplify bbox for prompt
                        "styles": {k: styles.get(k) for k in ['fontSize', 'fontWeight', 'color', 'backgroundColor']},
                        "above_fold": is_above_fold 
                    })
                
                # For Consistency: store a unique key for button/link style
                cta_style_key = f"{bg_color}_{text_color}_{styles.get('fontSize')}_{styles.get('fontWeight')}"
                if tag_name == 'BUTTON': button_styles_found[cta_style_key] = button_styles_found.get(cta_style_key, 0) + 1
                elif tag_name == 'A': link_styles_found[cta_style_key] = link_styles_found.get(cta_style_key, 0) + 1 # For general links


    unique_font_families_list = sorted(list(unique_font_families))

    # Calculate average font sizes for hierarchy
    avg_h1_size = sum(h1_font_sizes) / len(h1_font_sizes) if h1_font_sizes else 0
    avg_h2_size = sum(h2_font_sizes) / len(h2_font_sizes) if h2_font_sizes else 0
    avg_p_size = sum(p_font_sizes) / len(p_font_sizes) if p_font_sizes else 0

    # Summarize Typography for Hierarchy (no change)
    brand_typography_summary = {}
    if raw_typography_guidelines['H1']:
        h1_font = raw_typography_guidelines['H1'][0]
        brand_typography_summary['heading1_font'] = {
            'font_family': h1_font.get('font_family'), 'font_size': h1_font.get('fontSize'), 'font_weight': h1_font.get('fontWeight')
        }
    if raw_typography_guidelines['H2']:
        h2_font = raw_typography_guidelines['H2'][0]
        brand_typography_summary['heading2_font'] = {
            'font_family': h2_font.get('font_family'), 'font_size': h2_font.get('fontSize'), 'font_weight': h2_font.get('fontWeight')
        }
    if raw_typography_guidelines['P']:
        p_font = raw_typography_guidelines['P'][0]
        brand_typography_summary['body_font'] = {
            'font_family': p_font.get('font_family'), 'font_size': p_font.get('fontSize'), 'font_weight': p_font.get('fontWeight')
        }

    # --- Compile Hierarchy & Consistency Insights for LLM ---
    hierarchy_consistency_insights_text = (
        f"Heading Font Sizes: H1 avg:{avg_h1_size:.1f}px, H2 avg:{avg_h2_size:.1f}px, P avg:{avg_p_size:.1f}px. "
    )
    if avg_h1_size > 0 and avg_h2_size > 0 and avg_h1_size <= avg_h2_size:
        hierarchy_consistency_insights_text += " WARNING: H1 is not clearly larger than H2."
    if avg_h2_size > 0 and avg_p_size > 0 and avg_h2_size <= avg_p_size:
        hierarchy_consistency_insights_text += " WARNING: H2 is not clearly larger than P."
    
    hierarchy_consistency_insights_text += f"\nFound {len(cta_elements_for_llm)} potentially prominent CTAs. Examples: {json.dumps(cta_elements_for_llm[:3])}. " # Dump as JSON for LLM

    # NEW: Consistency metrics
    hierarchy_consistency_insights_text += f"\nTypography Consistency: H1 styles found: {len(h1_styles_found)} unique styles. H2 styles found: {len(h2_styles_found)} unique styles. P styles found: {len(p_styles_found)} unique styles."
    if len(h1_styles_found) > 1 and sum(h1_styles_found.values()) > 1:
        hierarchy_consistency_insights_text += " WARNING: Multiple H1 styles detected."
    if len(h2_styles_found) > 1 and sum(h2_styles_found.values()) > 1:
        hierarchy_consistency_insights_text += " WARNING: Multiple H2 styles detected."
    if len(p_styles_found) > 1 and sum(p_styles_found.values()) > 1:
        hierarchy_consistency_insights_text += " WARNING: Multiple P styles detected."

    hierarchy_consistency_insights_text += f"\nCTA Button Consistency: {len(button_styles_found)} unique button styles. Link Consistency: {len(link_styles_found)} unique link styles."
    if len(button_styles_found) > 1 and sum(button_styles_found.values()) > 1:
        hierarchy_consistency_insights_text += " WARNING: Multiple button styles detected."
    if len(link_styles_found) > 1 and sum(link_styles_found.values()) > 1:
        hierarchy_consistency_insights_text += " WARNING: Multiple link styles detected."


    # --- LLM Vibe Analysis & Design Principles Assessment ---
    llm_output_data = {} 

    typography_summary_text = f"Detected Fonts: {', '.join(unique_font_families_list)}. Main H1/H2/P guidelines are available." if unique_font_families_list else "No distinct font families identified."
    color_summary_text = "Dominant Color Palette: " + ", ".join([f"{c['color']} ({c['proportion']*100:.0f}%)" for c in extracted_color_palette_with_proportions]) + "." if extracted_color_palette_with_proportions else "No dominant color palette identified."
    
    design_elements_context_for_llm = []
    for i, e in enumerate(key_elements):
        if i >= 50: break # Process max 50 elements for LLM context
        if e['tag_name'] in ['H1', 'H2', 'P', 'BUTTON', 'A', 'IMG'] and e['bounding_box']['width'] > 0 and e['bounding_box']['height'] > 0:
            styles = e['computed_styles']
            element_detail = (
                f"- Tag: {e['tag_name']}, Text: '{e['text_content'] or ''}', "
                f"BBox: ({e['bounding_box']['x']},{e['bounding_box']['y']},{e['bounding_box']['width']}x{e['bounding_box']['height']}), "
                f"Styles: {{font: {styles.get('fontSize')}/{styles.get('lineHeight')} {styles.get('fontFamily')}, color: {styles.get('color')}, bg: {styles.get('backgroundColor')}}}"
            )
            if e['tag_name'] == 'IMG' and e.get('src'):
                element_detail += f", ImgSrc: {e['src'][:50]}..."
            design_elements_context_for_llm.append(element_detail)


    prompt_parts = [
        """
        You are an expert brand and UI/UX analyst. Analyze the provided webpage screenshot and its DOM details.
        
        **For 'vibe_analysis':**
        Provide 2-3 **keywords** that capture the overall 'vibe', 'brand personality', or 'emotional tone'.
        Then, give a **single, concise sentence** (max 25 words) describing this vibe.
        
        **For 'design_feedback':**
        Focus on **Visual Hierarchy** and **Repetition & Consistency**.
        For each finding, provide:
        - **aspect**: The design principle (e.g., "Visual Hierarchy", "CTA Consistency").
        - **issue**: A **brief, specific statement** (max 15 words) of the problem.
        - **recommendation**: A **short, actionable suggestion** (max 20 words).
        - **severity**: "Minor", "Moderate", or "Major".
        Limit yourself to the **top 3-5 most impactful findings** across both principles.
        """, # This first part is crucial for setting the tone and conciseness
        f"Webpage URL: {url}\n",
        "Here is the visual context:",
        *get_image_parts(screenshot_base64), 
        "\nHere are details of key elements from the page's DOM structure (max 50 elements for brevity):\n",
        "\n".join(design_elements_context_for_llm) if design_elements_context_for_llm else "No specific elements provided or elements filtered for detailed analysis.",
        f"\nBased on extracted data, we found: {typography_summary_text}. {color_summary_text}.",
        f"\nSpecific Hierarchy and Consistency Metrics: {hierarchy_consistency_insights_text}",
        """
        Provide your analysis in a structured JSON format. Ensure all strings are correctly escaped.
        Example structure:
        ```json
        {
          "vibe_analysis": {
            "keywords": ["Modern", "Professional", "Minimalist"],
            "description": "Clean layout and concise typography convey a modern and professional feel."
          },
          "design_feedback": [
            {
              "aspect": "Visual Hierarchy",
              "issue": "H1/H2 differentiation unclear.",
              "recommendation": "Increase H1/H2 font size/weight for clarity.",
              "severity": "Major"
            },
            {
              "aspect": "CTA Prominence",
              "issue": "Primary CTAs blend with content.",
              "recommendation": "Use higher contrast color for main buttons.",
              "severity": "Major"
            },
            {
              "aspect": "Repetition & Consistency",
              "issue": "Inconsistent button styles.",
              "recommendation": "Establish a consistent style guide for all buttons.",
              "severity": "Minor"
            }
          ]
        }
        ```
        """
    ]

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt_parts, generation_config={"response_mime_type": "application/json"}, request_options={"timeout": 120})
        
        parsed_llm_data = {} 
        if response and response.text:
            try:
                parsed_llm_data = parse_gemini_json_response(response.text)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error from LLM response: {e}")
                print(f"Raw LLM response: {response.text}")
                parsed_llm_data = {} 

            if parsed_llm_data and 'vibe_analysis' in parsed_llm_data:
                llm_vibe_analysis = parsed_llm_data['vibe_analysis']
            else:
                print(f"LLM did not return 'vibe_analysis' in the expected format: {response.text}")
                llm_vibe_analysis = {"keywords": [], "description": "LLM response format error or missing 'vibe_analysis'."}
            
            llm_design_feedback = parsed_llm_data.get('design_feedback', [])
        else:
            print("LLM returned an empty or invalid response text.")
            llm_vibe_analysis = {"keywords": [], "description": "LLM returned an empty response."}
            llm_design_feedback = []

    except Exception as e:
        print(f"Error in LLM Analysis: {e}")
        llm_vibe_analysis = {"keywords": [], "description": f"Failed to generate analysis due to error: {str(e)}"}
        llm_design_feedback = []


    # --- Final Output Structure ---
    design_analysis_output = {
        "unique_font_families": unique_font_families_list,
        "typography_guidelines_raw": raw_typography_guidelines, 
        "brand_typography_summary": brand_typography_summary, 
        "extracted_color_palette": extracted_color_palette_with_proportions,
        "vibe_analysis": llm_vibe_analysis,
        "design_feedback": llm_design_feedback 
    }
    print('design vibe', llm_design_feedback)
    return {"status": "success", "data": design_analysis_output}