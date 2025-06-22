// extension/popup.js

document.addEventListener('DOMContentLoaded', () => {
    const currentUrlSpan = document.getElementById('currentUrl');
    const analyzeButton = document.getElementById('analyzeButton');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    
    // Get references to your UI elements (ensure these IDs exist in popup.html)
    const vibeAnalysisOutput = document.getElementById('vibeAnalysisOutput'); // NEW element
    const designChecklist = document.getElementById('designChecklist'); 
    const workflowSuggestions = document.getElementById('workflowSuggestions');
    const brandingPaletteDiv = document.getElementById('brandingPalette');
    const savePaletteButton = document.getElementById('savePaletteButton');
    const paletteListDiv = document.getElementById('paletteList');

    let currentAnalyzedPalette = null; // To hold the palette for saving (array of hex codes)

    // Get current tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const currentTab = tabs[0];
        currentUrlSpan.textContent = currentTab ? currentTab.url : 'N/A';
    });

    // Function to display results (takes the full response object from background.js)
    const displayResults = (response) => {
        // Clear previous results sections
        resultsDiv.innerHTML = ''; // Clear overall results, then re-append sections
        errorDiv.style.display = 'none'; // Hide any previous errors
        
        // --- Handle overall analysis failure from background.js or backend ---
        if (response.success === false) {
            errorDiv.textContent = `Analysis failed: ${response.error || 'Unknown error'}`;
            errorDiv.style.display = 'block';
            return;
        }

        const analysisData = response.data; // This is the object with design_check_results, etc.

        if (!analysisData) {
            errorDiv.textContent = `No analysis data received from backend.`;
            errorDiv.style.display = 'block';
            return;
        }

        // Display URL/Title if available (append to main resultsDiv)
        resultsDiv.innerHTML += `<h3>Analysis for: ${analysisData.url || 'Current Page'}</h3>`;

        // --- Design Analysis (Vibe, Feedback, and Color Palette) ---
        resultsDiv.innerHTML += `<h4>Design Analysis</h4>`;
        const designResults = analysisData.design_check_results?.data; // Get the 'data' object from design_check_results

        if (designResults) {
            // Display Vibe Analysis
            if (vibeAnalysisOutput) { // Check if the element exists
                const vibe = designResults.vibe_analysis;
                if (vibe) {
                    vibeAnalysisOutput.innerHTML = `
                        <h5>Overall Vibe / Brand Personality:</h5>
                        <p>Keywords: <strong>${vibe.keywords.join(', ') || 'N/A'}</strong></p>
                        <p>${vibe.description || 'No description provided.'}</p>
                    `;
                } else {
                    vibeAnalysisOutput.innerHTML = `<p>No vibe analysis provided.</p>`;
                }
                resultsDiv.appendChild(vibeAnalysisOutput); // Append the vibe section to main results
            }

            // Display Design Feedback
            const designFeedback = designResults.design_feedback;
            if (designFeedback && designFeedback.length > 0) {
                designChecklist.innerHTML = `<h5>Design Feedback:</h5>`;
                const ul = document.createElement('ul');
                designFeedback.forEach(item => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${item.aspect || 'N/A'}:</strong> ${item.issue || 'N/A'}<br><em>Recommendation:</em> ${item.recommendation || 'N/A'}<br><em>Severity:</em> ${item.severity || 'N/A'}`;
                    ul.appendChild(li);
                });
                designChecklist.appendChild(ul);
            } else {
                designChecklist.innerHTML = `<p>No specific design feedback.</p>`;
            }
            resultsDiv.appendChild(designChecklist); // Append the feedback section to main results
            
            // --- Extracted Color Palette from Design Agent ---
            resultsDiv.innerHTML += `<h4>Extracted Color Palette:</h4>`; // NEW heading for design palette
            const extractedPalette = designResults.extracted_color_palette; // Get palette from design results
            
            if (extractedPalette && extractedPalette.length > 0) {
                const paletteContainer = document.createElement('div');
                paletteContainer.innerHTML = '<strong>Dominant Colors:</strong> ';
                
                // Convert extracted palette (with proportions) to simple hex array for display/saving
                const colorsForSwatches = [];
                extractedPalette.forEach(item => {
                    colorsForSwatches.push(item.color); // Collect just the hex code
                    const swatch = document.createElement('span');
                    swatch.classList.add('color-swatch');
                    swatch.style.backgroundColor = item.color;
                    swatch.title = `${item.color} (${(item.proportion * 100).toFixed(0)}%)`; // Show color and proportion on hover
                    paletteContainer.appendChild(swatch);
                });
                
                brandingPaletteDiv.innerHTML = ''; // Clear previous content if any
                brandingPaletteDiv.appendChild(paletteContainer);
                currentAnalyzedPalette = colorsForSwatches; // Store the simple array of hex codes for saving
                savePaletteButton.style.display = 'block'; // Show save button
            } else {
                brandingPaletteDiv.innerHTML = `<p>No dominant colors or palette extracted by design agent.</p>`;
                savePaletteButton.style.display = 'none';
            }
            resultsDiv.appendChild(brandingPaletteDiv); // Append the palette section to main results

        } else {
            // This block runs if 'design_check_results' key is not present or its data is null/undefined
            resultsDiv.innerHTML += `<h4>Design Analysis:</h4><p>Design analysis agent did not return data or encountered an error.</p>`;
        }


        // --- Workflow Check ---
        resultsDiv.innerHTML += `<h4>Workflow Analysis</h4>`;
        // Make sure workflowSuggestions is cleared first
        workflowSuggestions.innerHTML = ''; 
        const workflowAnalysis = analysisData.user_workflow_results?.data?.workflow_analysis;
        const workflowStatus = analysisData.user_workflow_results?.status;
        const workflowMessage = analysisData.user_workflow_results?.message;

        if (workflowStatus === "skipped") {
            workflowSuggestions.innerHTML = `<p>Status: <strong>${workflowStatus}</strong></p><p>${workflowMessage}</p>`;
        } else if (workflowAnalysis && workflowAnalysis.length > 0) {
            const ul = document.createElement('ul');
            workflowAnalysis.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>Path:</strong> ${item.workflow_path || 'N/A'}<br><strong>Issue:</strong> ${item.issue || 'N/A'}<br><em>Recommendation:</em> ${item.recommendation || 'N/A'}`;
                ul.appendChild(li);
            });
            workflowSuggestions.appendChild(ul);
        } else {
            workflowSuggestions.innerHTML = `<p>No specific workflow issues identified or agent not fully active.</p>`;
        }
        resultsDiv.appendChild(workflowSuggestions); // Append the workflow section to main results


        // // --- Accessibility & Responsiveness Details ---
        // resultsDiv.innerHTML += `<h4>Accessibility & Responsiveness Details</h4>`;
        // const accessibilityResults = analysisData.accessibility_results?.data;
        // const accessibilityStatus = analysisData.accessibility_results?.status;
        // const accessibilityMessage = analysisData.accessibility_results?.message;

        // // Create a temporary div for accessibility output to avoid overwriting resultsDiv.innerHTML
        // const accessibilityOutputDiv = document.createElement('div');
        // if (accessibilityStatus === "success" && accessibilityResults) {
        //     let accHtml = `<p>Status: <strong>${accessibilityStatus}</strong></p>`;
        //     accHtml += `<p>${accessibilityMessage}</p>`;
        //     if (accessibilityResults.accessibility_score !== undefined) {
        //          accHtml += `<p><strong>Accessibility Score:</strong> ${accessibilityResults.accessibility_score || 'N/A'}</p>`;
        //     }
        //     if (accessibilityResults.responsiveness_notes) {
        //         accHtml += `<p><strong>Responsiveness Notes:</strong> ${accessibilityResults.responsiveness_notes || 'N/A'}</p>`;
        //     }
            
        //     // If you have specific 'accessibility_issues' coming from this agent:
        //     if (accessibilityResults.accessibility_issues && accessibilityResults.accessibility_issues.length > 0) {
        //         accHtml += `<h5>Specific Accessibility Issues:</h5><ul>`;
        //         accessibilityResults.accessibility_issues.forEach(item => {
        //             accHtml += `<li><strong>Issue:</strong> ${item.issue || 'N/A'}<br><em>Recommendation:</em> ${item.recommendation || 'N/A'}`;
        //             if (item.element_info) accHtml += `<br><strong>Element:</strong> <pre>${JSON.stringify(item.element_info, null, 2)}</pre>`;
        //             if (item.colors) accHtml += `<br><strong>Colors:</strong> Foreground: ${item.colors.foreground}, Background: ${item.colors.background}`;
        //             accHtml += `</li>`;
        //         });
        //         accHtml += `</ul>`;
        //     } else {
        //         accHtml += `<p>No specific accessibility issues detailed.</p>`;
        //     }
        //     accessibilityOutputDiv.innerHTML = accHtml;
        // } else {
        //     accessibilityOutputDiv.innerHTML = `<p>Accessibility & Responsiveness analysis status: <strong>${accessibilityStatus || 'N/A'}</strong></p>`;
        //     if (accessibilityMessage) accessibilityOutputDiv.innerHTML += `<p>${accessibilityMessage}</p>`;
        //     accessibilityOutputDiv.innerHTML += `<p>No detailed accessibility data found.</p>`;
        // }
        // resultsDiv.appendChild(accessibilityOutputDiv); // Append the accessibility section to main results


        // Make the main results container visible
        resultsDiv.style.display = 'block'; 

        // Add CSS for color swatches if not already present (good practice to ensure styling)
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
                .palette-item {
                    margin-bottom: 5px;
                    display: flex;
                    align-items: center;
                    flex-wrap: wrap;
                }
            `;
            document.head.appendChild(style);
        }
    };

    // --- Event Listeners and Initial Load (remain mostly the same) ---
    // Function to fetch and display saved palettes (assumes backend saves/returns hex codes)
    const fetchAndDisplaySavedPalettes = async () => {
        paletteListDiv.innerHTML = 'Loading saved palettes...';
        try {
            const response = await chrome.runtime.sendMessage({ action: "fetchPalettes" });
            const savedPalettes = response.data; 

            paletteListDiv.innerHTML = '';
            if (!savedPalettes || savedPalettes.length === 0) {
                paletteListDiv.textContent = 'No palettes saved yet.';
            } else {
                savedPalettes.forEach(paletteEntry => {
                    const paletteDiv = document.createElement('div');
                    paletteDiv.classList.add('palette-item');
                    let html = `<strong>${paletteEntry.name}</strong>: `;
                    paletteEntry.palette.forEach(colorValue => { // This assumes paletteEntry.palette is an array of hex strings
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
        const urlToAnalyze = currentUrlSpan.textContent;
        if (urlToAnalyze === 'N/A' || !urlToAnalyze) {
            errorDiv.textContent = 'Cannot get current tab URL.';
            errorDiv.style.display = 'block';
            return;
        }

        loadingDiv.style.display = 'block';
        resultsDiv.style.display = 'none'; // Hide results until new ones are ready
        errorDiv.style.display = 'none';

        try {
            const response = await chrome.runtime.sendMessage({
                action: "analyzeWebsite",
                url: urlToAnalyze
            });
            
            displayResults(response);
            
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
        if (currentAnalyzedPalette && currentAnalyzedPalette.length > 0) {
            const paletteName = prompt("Enter a name for this palette:", "My Custom Palette");
            if (paletteName) {
                try {
                    const response = await chrome.runtime.sendMessage({
                        action: "savePalette",
                        name: paletteName,
                        palette: currentAnalyzedPalette // This should now be a list of hex codes
                    });
                    if (response.success) {
                        alert(response.message || "Palette saved!");
                        fetchAndDisplaySavedPalettes();
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