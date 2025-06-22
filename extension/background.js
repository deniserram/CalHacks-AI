// extension/background.js
// It handles messages from popup.js (and content.js), and makes network requests.

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    // Must return true to indicate that sendResponse will be called asynchronously
    // This is crucial for async operations like fetch requests.
    (async () => {
        const API_BASE_URL = 'http://localhost:5000/api'; // Your Flask backend URL

        if (request.action === "analyzeWebsite") {
            try {
                // 1. Get current tab details (URL, title)
                const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
                const currentUrl = tab.url;
                const currentTitle = tab.title;

                // Basic validation: Don't analyze internal Chrome pages
                if (currentUrl.startsWith('chrome://') || currentUrl.startsWith('chrome-extension://') || currentUrl === 'about:blank') {
                    sendResponse({ success: false, error: "Cannot analyze internal Chrome pages, extension pages, or blank tabs. Please navigate to a website." });
                    return; // Exit early
                }

                // 2. Capture screenshot as Base64
                // chrome.tabs.captureVisibleTab returns a data URL (e.g., "data:image/png;base64,...")
                const screenshotDataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
                // Remove the "data:image/png;base64," prefix for the backend
                const cleanScreenshotBase64 = screenshotDataUrl.replace(/^data:image\/(png|jpeg|gif);base64,/, '');

                // 3. Inject content.js if it's not already running (this ensures the listener is set up)
                // You can add logic to only inject if not already injected, but for a one-off action, it's fine.
                await chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ['content.js'] // Inject the entire content.js file
                });

                // 4. Send a message to content.js to trigger its data collection function
                // The response from content.js will be received here directly.
                const pageDataFromContent = await chrome.tabs.sendMessage(tab.id, { action: "collectPageData" });

                // Check if content script returned an error or no data
                if (!pageDataFromContent || pageDataFromContent.error) {
                    console.error('Background script - Content script data collection failed:', pageDataFromContent ? pageDataFromContent.error : 'No data received from content script.');
                    sendResponse({ success: false, error: pageDataFromContent ? pageDataFromContent.error : "Failed to collect data from the webpage." });
                    return;
                }

                console.log('Background script: Received pageDataFromContent from content.js:', pageDataFromContent);
                console.log('data', pageDataFromContent.key_elements);

                // 5. Combine all data into a single comprehensive payload for the backend
                const comprehensivePayload = {
                    url: currentUrl,
                    title: currentTitle,
                    screenshot_base64: cleanScreenshotBase64,
                    key_elements: pageDataFromContent.key_elements // This is the detailed DOM data from content.js
                };
                
                console.log('Background script: Sending comprehensive payload to backend.'); 

                // 6. Send combined payload to your Flask backend
                const response = await fetch(`${API_BASE_URL}/analyze-website`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(comprehensivePayload),
                });
                
                if (!response.ok) {
                    const errorText = await response.text(); // Get raw error text
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }

                const data = await response.json();
                sendResponse({ success: true, data: data });

            } catch (error) {
                console.error('Background script - Error during analyzeWebsite:', error);
                // Send back a more detailed error message for the popup to display
                sendResponse({ success: false, error: error.message || "An unknown error occurred during website analysis." });
            }
        }
        // Keep your other request actions ('fetchPalettes', 'savePalette')
        else if (request.action === "fetchPalettes") {
            try {
                const response = await fetch(`${API_BASE_URL}/branding-palettes`);
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }
                const data = await response.json();
                sendResponse({ success: true, data: data });
            }
            catch (error) {
                console.error('Background script - Error fetching palettes:', error);
                sendResponse({ success: false, error: error.message || "Network error" });
            }
        } else if (request.action === "savePalette") {
            try {
                const response = await fetch(`${API_BASE_URL}/branding-palettes`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name: request.name, palette: request.palette }),
                });
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }
                const data = await response.json();
                sendResponse({ success: true, message: data.message });
            } catch (error) {
                console.error('Background script - Error saving palette:', error);
                sendResponse({ success: false, error: error.message || "Network error" });
            }
        }
    })();
    return true; // Crucial: Keep the message channel open for sendResponse
});