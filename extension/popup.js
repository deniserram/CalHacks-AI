// extension/popup.js
document.addEventListener('DOMContentLoaded', () => {
    const currentUrlSpan = document.getElementById('currentUrl');
    const analyzeButton = document.getElementById('analyzeButton');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const designChecklist = document.getElementById('designChecklist');
    const workflowSuggestions = document.getElementById('workflowSuggestions');
    const brandingPaletteDiv = document.getElementById('brandingPalette');
    const savePaletteButton = document.getElementById('savePaletteButton');
    const paletteListDiv = document.getElementById('paletteList');

    let currentAnalyzedPalette = null; // To hold the palette for saving

    // Get current tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const currentTab = tabs[0];
        currentUrlSpan.textContent = currentTab ? currentTab.url : 'N/A';
    });

    // Function to display results (takes the full response object from background.js)
    const displayResults = (response) => {
        designChecklist.innerHTML = '';
        workflowSuggestions.innerHTML = '';
        brandingPaletteDiv.innerHTML = '';
        savePaletteButton.style.display = 'none';
        errorDiv.style.display = 'none';
        resultsDiv.innerHTML = ''; // Clear the overall results section

        // --- Handle overall analysis failure ---
        // 'response' is the object { success: boolean, data: backend_data, error: string }
        if (response.success === false) {
            errorDiv.textContent = `Analysis failed: ${response.error || 'Unknown error'}`;
            errorDiv.style.display = 'block';
            return;
        }

        // Now, 'analysisData' contains the actual analysis results object from the backend
        const analysisData = response.data; // This is the object with design_check_results, etc.

        if (!analysisData) {
            errorDiv.textContent = `No analysis data received from backend.`;
            errorDiv.style.display = 'block';
            return;
        }

        // Display URL/Title if available
        resultsDiv.innerHTML += `<h3>Analysis for: ${analysisData.url || 'Current Page'}</h3>`;


        // --- Design Check ---
        resultsDiv.innerHTML += `<h4>Design Feedback</h4>`;
        const designFeedback = analysisData.design_check_results?.data?.design_feedback;
        if (designFeedback && designFeedback.length > 0) {
            const ul = document.createElement('ul');
            designFeedback.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${item.aspect || 'N/A'}:</strong> ${item.issue || 'N/A'}<br><em>Recommendation:</em> ${item.recommendation || 'N/A'}`;
                ul.appendChild(li);
            });
            designChecklist.appendChild(ul);
        } else {
            designChecklist.innerHTML = `<p>No specific design feedback.</p>`;
        }


        // --- Workflow Check ---
        resultsDiv.innerHTML += `<h4>Workflow Analysis</h4>`;
        const workflowAnalysis = analysisData.user_workflow_results?.data?.workflow_analysis;
        if (workflowAnalysis && workflowAnalysis.length > 0) {
            const ul = document.createElement('ul');
            workflowAnalysis.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>Path:</strong> ${item.workflow_path || 'N/A'}<br><strong>Issue:</strong> ${item.issue || 'N/A'}<br><em>Recommendation:</em> ${item.recommendation || 'N/A'}`;
                ul.appendChild(li);
            });
            workflowSuggestions.appendChild(ul);
        } else {
            workflowSuggestions.innerHTML = `<p>No specific workflow issues identified.</p>`;
        }

        // --- Branding Palette (which you use for Accessibility results) ---
        resultsDiv.innerHTML += `<h4>Branding Palette (Accessibility Analysis)</h4>`; // Clarified heading for your setup
        // Accessing branding data from 'accessibility_results' as per your backend setup
        const brandingData = analysisData.accessibility_results?.data; 
        currentAnalyzedPalette = brandingData?.palette || null; // Store for saving (make sure it's the array of hex codes)

        if (brandingData && brandingData.palette && brandingData.palette.length > 0) {
            // Dominant Color
            if (brandingData.dominant_color) {
                const dominantDiv = document.createElement('div');
                dominantDiv.innerHTML = `<strong>Dominant Color:</strong> 
                    <div class="color-swatch" style="background-color: ${brandingData.dominant_color};" title="${brandingData.dominant_color}"></div>
                    ${brandingData.dominant_color}`;
                brandingPaletteDiv.appendChild(dominantDiv);
            }

            // Palette colors (iterate array of hex codes)
            const paletteContainer = document.createElement('div');
            paletteContainer.innerHTML = '<strong>Extracted Palette:</strong> ';
            brandingData.palette.forEach(colorValue => {
                const swatch = document.createElement('span');
                swatch.classList.add('color-swatch');
                swatch.style.backgroundColor = colorValue;
                swatch.title = colorValue; // Show hex on hover
                paletteContainer.appendChild(swatch);
            });
            brandingPaletteDiv.appendChild(paletteContainer);

            savePaletteButton.style.display = 'block';
        } else {
            brandingPaletteDiv.innerHTML = `<p>No dominant colors or palette extracted.</p>`;
            savePaletteButton.style.display = 'none'; // Hide if no palette to save
        }

        // --- Accessibility Analysis (if you were to add a dedicated one later) ---
        // This section is currently structured to look for 'accessibility_issues'
        // If your 'extract_branding_palette' function returns a different structure
        // for accessibility analysis, you'll need to adjust this.
        // For now, if branding is the *only* thing you want for 'accessibility_results',
        // you might remove or rename this section, or adjust it to display
        // accessibility-relevant data from your branding analysis if it includes it.
        // Assuming there might be a separate structure for accessibility issues if they were added.
        resultsDiv.innerHTML += `<h4>Additional Accessibility Details (if provided by agent)</h4>`; // New Heading
        const accessibilityDetails = analysisData.accessibility_results?.data?.accessibility_issues; // Assuming 'accessibility_issues' nested
        if (accessibilityDetails && accessibilityDetails.length > 0) {
            const ul = document.createElement('ul');
            accessibilityDetails.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>Issue:</strong> ${item.issue || 'N/A'}<br><em>Recommendation:</em> ${item.recommendation || 'N/A'}`;
                if (item.element_info) {
                    li.innerHTML += `<br><strong>Element:</strong> <pre>${JSON.stringify(item.element_info, null, 2)}</pre>`;
                }
                if (item.colors) {
                    li.innerHTML += `<br><strong>Colors:</strong> Foreground: ${item.colors.foreground}, Background: ${item.colors.background}`;
                }
                ul.appendChild(li);
            });
            resultsDiv.appendChild(ul);
        } else {
            resultsDiv.innerHTML += `<p>No specific accessibility details found (beyond branding).</p>`;
        }

        resultsDiv.style.display = 'block'; // Make the main results container visible

        // Add CSS for color swatches if not already present
        if (!document.getElementById('color-swatch-style')) {
            const style = document.createElement('style');
            style.id = 'color-swatch-style';
            style.innerHTML = `
                .color-swatch {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 1px solid #ccc;
                    vertical-align: middle;
                    margin-left: 5px;
                    margin-right: 5px;
                    border-radius: 3px;
                }
                .palette-item { /* Changed from .palette-entry to .palette-item for clarity */
                    margin-bottom: 5px;
                    display: flex;
                    align-items: center;
                    flex-wrap: wrap; /* Allow wrapping for long lines of colors */
                }
                .result-item { /* Assuming you use this class in popup.html */
                    background-color: #f9f9f9;
                    border-left: 3px solid #007bff;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 4px;
                }
                .result-item h5 { /* Assuming you use h5 within result-item */
                    margin-top: 0;
                    color: #0056b3;
                }
            `;
            document.head.appendChild(style);
        }
    };

    // Function to fetch and display saved palettes
    const fetchAndDisplaySavedPalettes = async () => {
        paletteListDiv.innerHTML = 'Loading saved palettes...';
        try {
            const response = await chrome.runtime.sendMessage({ action: "fetchPalettes" });
            // The backend returns an ARRAY of objects: [{"name": "...", "palette": [...]}, ...]
            const savedPalettes = response.data; 

            paletteListDiv.innerHTML = ''; // Clear previous
            if (!savedPalettes || savedPalettes.length === 0) { // Check if it's an empty array
                paletteListDiv.textContent = 'No palettes saved yet.';
            } else {
                // Iterate over the array of saved palette objects
                savedPalettes.forEach(paletteEntry => {
                    const paletteDiv = document.createElement('div');
                    paletteDiv.classList.add('palette-item'); // Use the new class
                    let html = `<strong>${paletteEntry.name}</strong>: `; // Access 'name' property

                    // Iterate over the 'palette' array (which contains hex color strings)
                    paletteEntry.palette.forEach(colorValue => {
                        html += `<span class="color-swatch" style="background-color: ${colorValue};" title="${colorValue}"></span>`;
                    });
                    
                    paletteDiv.innerHTML = html;
                    paletteListDiv.appendChild(paletteDiv);
                });
            }
        } catch (error) {
            console.error('Error fetching saved palettes:', error);
            paletteListDiv.textContent = 'Error loading saved palettes.';
        }
    };

    // Event listener for Analyze button
    analyzeButton.addEventListener('click', async () => {
        const urlToAnalyze = currentUrlSpan.textContent; // Correctly defined here
        if (urlToAnalyze === 'N/A' || !urlToAnalyze) {
            errorDiv.textContent = 'Cannot get current tab URL.';
            errorDiv.style.display = 'block';
            return;
        }

        loadingDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        errorDiv.style.display = 'none';

        try {
            // Send message to background.js to start analysis
            const response = await chrome.runtime.sendMessage({
                action: "analyzeWebsite",
                url: urlToAnalyze
            });
            
            // Pass the entire response object to displayResults
            displayResults(response); // <--- CHANGED THIS LINE
            
        } catch (error) {
            console.error('Error during analysis:', error);
            errorDiv.textContent = `Analysis failed: ${error.message}`;
            errorDiv.style.display = 'block';
        } finally {
            loadingDiv.style.display = 'none';
        }
    });

    // Event listener for Save Palette button
    savePaletteButton.addEventListener('click', async () => {
        if (currentAnalyzedPalette && currentAnalyzedPalette.length > 0) { // Check length for array
            const paletteName = prompt("Enter a name for this palette:", "My Custom Palette");
            if (paletteName) {
                try {
                    const response = await chrome.runtime.sendMessage({
                        action: "savePalette",
                        name: paletteName,
                        palette: currentAnalyyzedPalette // This needs to be a list of colors (hex codes)
                    });
                    if (response.success) {
                        alert(response.message || "Palette saved!");
                        fetchAndDisplaySavedPalettes(); // Refresh saved palettes
                    } else {
                        alert(`Failed to save palette: ${response.error}`);
                    }
                } catch (error) {
                    console.error('Error saving palette:', error);
                    alert(`Failed to save palette: ${error.message}`);
                }
            }
        } else {
            alert("No palette to save.");
        }
    });

    // Fetch saved palettes on popup load
    fetchAndDisplaySavedPalettes();
});