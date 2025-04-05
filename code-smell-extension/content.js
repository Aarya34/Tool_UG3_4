(async () => {
    // 1. Get repository information
    const repoPath = window.location.pathname.split('/').slice(1, 3).join('/');
    const repoUrl = `https://github.com/${repoPath}`;
    console.log("[EXTENSION] Analyzing repository:", repoUrl);

    try {
        // 2. Fetch analysis results from backend
        const response = await fetch('http://localhost:5000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_url: repoUrl })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || "Analysis failed");
        }

        const data = await response.json();
        console.log("[EXTENSION] Analysis results:", data);

        // 3. Process and normalize smell data
        const smellsByFile = {};
        
        // Process Python results
        Object.entries(data.python || {}).forEach(([file, issues]) => {
            const fileName = file.split('/').pop(); // Get just the filename
            if (Object.keys(issues).length > 0) {
                smellsByFile[fileName] = Object.entries(issues).map(
                    ([type, detail]) => `${type}: ${JSON.stringify(detail)}`
                );
            }
        });

        // Process JavaScript results
        Object.entries(data.javascript || {}).forEach(([file, content]) => {
            const fileName = file.split('/').pop();
            if (content?.smells?.length > 0) {
                smellsByFile[fileName] = content.smells;
            }
        });

        console.log("[EXTENSION] Processed smells:", smellsByFile);

        // 4. Function to add indicators to files
        const addSmellIndicators = () => {
            // Target GitHub's file listing container
            const fileContainer = document.querySelector('[aria-labelledby="files"]') || 
                                document.querySelector('.react-directory-filename-column');
            
            if (!fileContainer) {
                console.log("[EXTENSION] File container not found, retrying...");
                setTimeout(addSmellIndicators, 500);
                return;
            }

            // Find all file links in the container
            const fileLinks = fileContainer.querySelectorAll('a.js-navigation-open, .react-directory-filename-column a');
            
            fileLinks.forEach(link => {
                const fileName = link.textContent.trim();
                const fileSmells = smellsByFile[fileName];
                
                if (fileSmells && !link.parentElement.querySelector('.smell-indicator')) {
                    const icon = document.createElement('span');
                    icon.className = 'smell-indicator';
                    icon.innerHTML = ' 👁️';
                    icon.style.cssText = `
                        margin-left: 8px;
                        cursor: pointer;
                        color: #f06;
                        position: relative;
                    `;

                    // Create tooltip
                    const tooltip = document.createElement('div');
                    tooltip.className = 'smell-tooltip';
                    tooltip.style.cssText = `
                        display: none;
                        position: absolute;
                        background: white;
                        border: 1px solid #d1d5da;
                        border-radius: 3px;
                        padding: 8px;
                        z-index: 100;
                        width: 300px;
                        left: 20px;
                        top: 0;
                        box-shadow: 0 1px 5px rgba(0,0,0,0.2);
                    `;

                    tooltip.innerHTML = `
                        <strong>Code smells in ${fileName}:</strong>
                        <ul style="margin-top: 5px; padding-left: 20px;">
                            ${fileSmells.map(smell => `<li>${smell}</li>`).join('')}
                        </ul>
                    `;

                    icon.appendChild(tooltip);
                    
                    icon.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        tooltip.style.display = tooltip.style.display === 'block' ? 'none' : 'block';
                    });

                    // Add to DOM - positioning depends on GitHub's layout
                    if (link.parentElement.querySelector('.Link--primary')) {
                        link.parentElement.querySelector('.Link--primary').after(icon);
                    } else {
                        link.parentElement.appendChild(icon);
                    }
                }
            });
        };

        // 5. Initial attempt to add indicators
        addSmellIndicators();

        // 6. Set up MutationObserver for dynamic content
        const observer = new MutationObserver(addSmellIndicators);
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

    } catch (err) {
        console.error("[EXTENSION] Error:", err);
        alert(`Error: ${err.message}`);
    }
})();