// extension/content.js

// This function will be called by background.js to collect data from the DOM
function collectPageData() {
    const data = {
        key_elements: []
    };

    // Select common, relevant elements for analysis. Expand this list as needed.
    // Ensure you select elements that will be useful for all three agents.
    const selectors = 'h1, h2, h3, h4, h5, h6, p, a, button, img, input, select, textarea, label, li, [role], [tabindex], div:not([id^="s_"])'; // Added role, tabindex, and general divs

    document.querySelectorAll(selectors).forEach(element => {
        try {
            const boundingBox = element.getBoundingClientRect();
            // Filter out elements that are not visible or have zero dimensions
            if (boundingBox.width === 0 || boundingBox.height === 0 || boundingBox.x + boundingBox.width <= 0 || boundingBox.y + boundingBox.height <= 0) {
                return; // Skip invisible or off-screen elements
            }

            const computedStyle = window.getComputedStyle(element);

            // Collect relevant computed styles
            const styles = {
                fontFamily: computedStyle.fontFamily,
                fontSize: computedStyle.fontSize,
                color: computedStyle.color,
                backgroundColor: computedStyle.backgroundColor,
                paddingTop: computedStyle.paddingTop,
                paddingBottom: computedStyle.paddingBottom,
                marginLeft: computedStyle.marginLeft,
                marginRight: computedStyle.marginRight,
                lineHeight: computedStyle.lineHeight,
                textAlign: computedStyle.textAlign,
                display: computedStyle.display,
                position: computedStyle.position, // Important for layout
                zIndex: computedStyle.zIndex,      // Important for layering
                opacity: computedStyle.opacity,    // Important for visibility
                border: computedStyle.border,
                boxSizing: computedStyle.boxSizing,
                fontWeight: computedStyle.fontWeight,
                textDecoration: computedStyle.textDecoration,
                cursor: computedStyle.cursor // Useful for interactive elements
                // Add more CSS properties as your agents might need them
            };

            data.key_elements.push({
                id: element.id || null,
                tag_name: element.tagName,
                text_content: element.textContent ? element.textContent.trim().substring(0, 500) : null, // Limit text length to avoid huge payloads
                bounding_box: {
                    x: boundingBox.x,
                    y: boundingBox.y,
                    width: boundingBox.width,
                    height: boundingBox.height,
                    top: boundingBox.top,
                    right: boundingBox.right,
                    bottom: boundingBox.bottom,
                    left: boundingBox.left
                },
                computed_styles: styles,
                src: element.tagName === 'IMG' ? element.src : null,
                alt: element.tagName === 'IMG' ? element.alt : null,
                href: element.tagName === 'A' || element.tagName === 'AREA' ? element.href : null,
                role: element.getAttribute('role') || null,
                tabIndex: element.getAttribute('tabindex') || null
            });
            
        } catch (e) {
            console.warn("Could not collect data for element:", element, e);
        }
    });

    return data;
}

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "collectPageData") {
        const pageData = collectPageData();
        sendResponse(pageData);
        return true; // Keep the message channel open for sendResponse
    }
});