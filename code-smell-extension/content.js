(async () => {

    const pathParts = window.location.pathname.split('/');

    if (pathParts.length < 3 || !pathParts[1] || !pathParts[2]) {
        console.log("[EXTENSION] Not a repository page. Skipping analysis.");
        return;
    }
    const repoPath = window.location.pathname.split('/').slice(1, 3).join('/');
    const repoUrl = `https://github.com/${repoPath}`;
    console.log("[EXTENSION] Analyzing repository:", repoUrl);

    try {
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

        const smellsByFile = {};

        // Process Python files
        Object.entries(data.python || {}).forEach(([file, issues]) => {
            if (Object.keys(issues).length > 0) {
                smellsByFile[file] = {
                    type: 'python',
                    smells: issues
                };
            }
        });

        // Process JavaScript files
        Object.entries(data.javascript || {}).forEach(([file, issues]) => {
            if (Object.keys(issues).length > 0) {
                smellsByFile[file] = {
                    type: 'javascript',
                    smells: issues
                };
            }
        });

        console.log("[EXTENSION] Processed smells:", smellsByFile);

        function formatCode(code) {
            return code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }

        function addSmellIconsReliable(smellsByFile) {
            const fileLinks = document.querySelectorAll('a.js-navigation-open, a.Link--primary');
        
            fileLinks.forEach(link => {
                const text = link.textContent.trim();
                const href = link.getAttribute('href');
        
                const fileName = text || (href && href.split('/').pop());
                const matchedKey = Object.keys(smellsByFile).find(key => {
                    return key.endsWith('/' + fileName) || key === fileName;
                });
        
                const fileData = matchedKey ? smellsByFile[matchedKey] : null;
        
                if (fileData && !link.parentElement.querySelector('.smell-indicator')) {
                    const icon = document.createElement('span');
                    icon.className = 'smell-indicator';
                    icon.innerHTML = ' ℹ';
                    icon.style.cssText = `
                        font-size: 16px;
                        color: #f06;
                        cursor: pointer;
                        margin-left: 8px;
                        position: relative;
                    `;
    
                    icon.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();

                        document.querySelectorAll('.smell-modal').forEach(m => m.remove());
                    
                        const modal = document.createElement('div');
                        modal.className = 'smell-modal';
                        modal.style.cssText = `
                            position: fixed;
                            color: black;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            width: 90%;
                            max-width: 1200px;
                            max-height: 90vh;
                            overflow-y: auto;
                            background: white;
                            border: 1px solid #ccc;
                            border-radius: 8px;
                            padding: 20px;
                            z-index: 9999;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                        `;

                        let content = `
                            <h2 style="margin-bottom: 20px;">Code Smells in ${fileName}</h2>
                            <div class="smell-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        `;
                        
                        if (fileData.type === 'python' || fileData.type === 'javascript') {
                            Object.entries(fileData.smells).forEach(([smellType, data]) => {
                                const refactoringExample = data.refactoring_example || { before: "No example available", after: "No example available" };
                                content += `
                                    <div class="smell-card" style="border: 1px solid #eee; border-radius: 8px; padding: 15px; background: white;">
                                        <h3 style="color: #f06; margin: 0 0 10px 0;">${smellType}</h3>
                                        <p><strong>Details:</strong> ${Array.isArray(data.details) ? data.details.join(', ') : data.details}</p>
                                        
                                        <div class="code-comparison" style="margin-top: 15px;">
                                            <div class="code-section">
                                                <h4 style="color: #666;">Current Code:</h4>
                                                <pre style="background: #f8f8f8; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 5px 0;"><code>${formatCode(refactoringExample.before)}</code></pre>
                                            </div>
                                            
                                            <div class="code-section" style="margin-top: 15px;">
                                                <h4 style="color: #090;">Refactored Code:</h4>
                                                <pre style="background: #f8f8f8; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 5px 0;"><code>${formatCode(refactoringExample.after)}</code></pre>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            });
                        }

                        content += `
                            </div>
                            <button class="closeModal" style="
                                margin-top: 20px;
                                background: #f06;
                                color: white;
                                padding: 8px 16px;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                font-weight: bold;
                                display: block;
                                margin-left: auto;
                                margin-right: auto;
                            ">Close</button>
                        `;
                    
                        modal.innerHTML = content;
                        document.body.appendChild(modal);
                    
                        modal.querySelector('.closeModal').addEventListener('click', () => {
                            modal.remove();
                        });

                        // Close modal when clicking outside
                        modal.addEventListener('click', (e) => {
                            if (e.target === modal) {
                                modal.remove();
                            }
                        });

                        // Add syntax highlighting
                        if (window.hljs) {
                            modal.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightBlock(block);
                            });
                        }
                    });
                    
                    link.parentElement.appendChild(icon);
                }
            });
        }

        addSmellIconsReliable(smellsByFile);
        
        let lastUrl = location.href;
        new MutationObserver(() => {
            const currentUrl = location.href;
            if (currentUrl !== lastUrl) {
                lastUrl = currentUrl;
                setTimeout(() => {
                    addSmellIconsReliable(smellsByFile);
                }, 1000);
            }
        }).observe(document, { subtree: true, childList: true });

    } catch (err) {
        console.error("[EXTENSION] Error:", err);
        // alert(Error: ${err.message});
    }
})();