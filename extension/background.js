// extension/background.js is a Service Worker in Manifest V3
// It handles messages from popup.js (and content.js if you add it), and makes network requests.

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    // Must return true to indicate that sendResponse will be called asynchronously
    // This is crucial for async operations like fetch requests.
    (async () => {
        const API_BASE_URL = 'http://127.0.0.1:5000/api'; // Your Flask backend URL

        if (request.action === "analyzeWebsite") {
            try {
                const response = await fetch(`${API_BASE_URL}/analyze-website`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: request.url }),
                });
                const data = await response.json();
                sendResponse({ success: true, data: data });
            } catch (error) {
                console.error('Background script - Error analyzing website:', error);
                // Send back an error message for the popup to display
                sendResponse({ success: false, error: error.message || "Network error" });
            }
        } else if (request.action === "fetchPalettes") {
            try {
                const response = await fetch(`${API_BASE_URL}/branding-palettes`);
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
                const data = await response.json();
                sendResponse({ success: true, message: data.message });
            } catch (error) {
                console.error('Background script - Error saving palette:', error);
                sendResponse({ success: false, error: error.message || "Network error" });
            }
        }
    })();
    return true; // Keep the message channel open for sendResponse
});