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

    // Function to display results
    const displayResults = (results) => {
        designChecklist.innerHTML = '';
        workflowSuggestions.innerHTML = '';
        brandingPaletteDiv.innerHTML = '';
        savePaletteButton.style.display = 'none';
        errorDiv.style.display = 'none';

        if (results.error) {
            errorDiv.textContent = `Analysis error: ${results.error}`;
            errorDiv.style.display = 'block';
            return;
        }

        // Design Check
        results.design_check_results.checklist.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            designChecklist.appendChild(li);
        });

        // Workflow Check
        results.user_workflow_results.suggestions.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            workflowSuggestions.appendChild(li);
        });

        // Branding Palette
        const palette = results.branding_palette_results.palette;
        currentAnalyzedPalette = palette; // Store for saving
        if (Object.keys(palette).length > 0) {
            for (const name in palette) {
                const entryDiv = document.createElement('div');
                entryDiv.classList.add('palette-entry');
                const swatch = document.createElement('span');
                swatch.classList.add('color-swatch');
                swatch.style.backgroundColor = palette[name];
                entryDiv.appendChild(swatch);
                const text = document.createTextNode(`${name}: ${palette[name]}`);
                entryDiv.appendChild(text);
                brandingPaletteDiv.appendChild(entryDiv);
            }
            savePaletteButton.style.display = 'block';
        } else {
            brandingPaletteDiv.textContent = 'No dominant colors extracted.';
        }

        resultsDiv.style.display = 'block';
    };

    // Function to fetch and display saved palettes
    const fetchAndDisplaySavedPalettes = async () => {
        paletteListDiv.innerHTML = 'Loading saved palettes...';
        try {
            // Send message to background.js to fetch palettes
            const response = await chrome.runtime.sendMessage({ action: "fetchPalettes" });
            const savedPalettes = response.data;

            paletteListDiv.innerHTML = ''; // Clear previous
            if (Object.keys(savedPalettes).length === 0) {
                paletteListDiv.textContent = 'No palettes saved yet.';
            } else {
                for (const name in savedPalettes) {
                    const palette = savedPalettes[name];
                    const paletteDiv = document.createElement('div');
                    paletteDiv.classList.add('palette-item');
                    let html = `<strong>${name}</strong>:<br>`;
                    for (const colorName in palette) {
                        const colorValue = palette[colorName];
                        html += `<div class="color-swatch" style="background-color: ${colorValue};"></div> ${colorName}: ${colorValue}<br>`;
                    }
                    paletteDiv.innerHTML = html;
                    paletteListDiv.appendChild(paletteDiv);
                }
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
        resultsDiv.style.display = 'none';
        errorDiv.style.display = 'none';

        try {
            // Send message to background.js to start analysis
            const response = await chrome.runtime.sendMessage({
                action: "analyzeWebsite",
                url: urlToAnalyze
            });
            if (response.success) {
                displayResults(response.data);
            } else {
                errorDiv.textContent = `Analysis failed: ${response.error}`;
                errorDiv.style.display = 'block';
            }
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
        if (currentAnalyzedPalette && Object.keys(currentAnalyzedPalette).length > 0) {
            const paletteName = prompt("Enter a name for this palette:", "My Custom Palette");
            if (paletteName) {
                try {
                    const response = await chrome.runtime.sendMessage({
                        action: "savePalette",
                        name: paletteName,
                        palette: currentAnalyzedPalette
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