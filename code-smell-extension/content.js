(async () => {
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length < 3 || !pathParts[1] || !pathParts[2]) {
        console.log("[EXTENSION] Not a repository page. Skipping analysis.");
        return;
    }

    const repoPath = pathParts.slice(1, 3).join('/');
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

        Object.entries(data.python || {}).forEach(([file, content]) => {
            if ((content?.smells?.length > 0) || content?.metrics) {
                smellsByFile[file] = {
                    smells: content.smells || [],
                    metrics: content.metrics || {}
                };
            }
        });

        Object.entries(data.javascript || {}).forEach(([file, content]) => {
            if ((content?.smells?.length > 0) || content?.metrics) {
                smellsByFile[file] = {
                    smells: content.smells || [],
                    metrics: content.metrics || {}
                };
            }
        });

        console.log("[EXTENSION] Processed smells + metrics:", smellsByFile);

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
                const fileSmells = fileData?.smells || [];
                const metrics = fileData?.metrics || {};

                // ℹ️ Smell icon
                if (fileSmells.length > 0 && !link.parentElement.querySelector('.smell-indicator')) {
                    const infoIcon = document.createElement('span');
                    infoIcon.className = 'smell-indicator';
                    infoIcon.innerHTML = ' ℹ️';
                    infoIcon.style.cssText = `font-size: 16px; color: #f06; cursor: pointer; margin-left: 8px; position: relative;`;

                    const tooltip = document.createElement('div');
                    tooltip.className = 'smell-tooltip';
                    tooltip.style.cssText = `
                        display: none;
                        position: absolute;
                        padding: 8px;
                        z-index: 100;
                        background: #fff;
                        border: 1px solid #d1d5da;
                        border-radius: 4px;
                        top: 20px;
                        left: 0;
                        box-shadow: 0 1px 5px rgba(0,0,0,0.2);
                        white-space: normal;
                        width: 300px;
                    `;

                    tooltip.innerHTML = `
                        <strong>Smells in ${fileName}:</strong>
                        <ul style="margin-top: 5px; padding-left: 20px;">
                            ${fileSmells.map(smell => `<li>${smell}</li>`).join('')}
                        </ul>
                    `;

                    infoIcon.appendChild(tooltip);

                    infoIcon.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();

                        document.querySelectorAll('.smell-modal').forEach(m => m.remove());

                        const modal = document.createElement('div');
                        modal.className = 'smell-modal';
                        modal.style.cssText = `
                            position: absolute;
                            color: black;
                            top: ${e.clientY + window.scrollY + 10}px;
                            left: ${e.clientX + window.scrollX + 10}px;
                            width: 500px;
                            max-height: 50%;
                            overflow-y: auto;
                            background: white;
                            border: 1px solid #ccc;
                            border-radius: 8px;
                            padding: 20px;
                            z-index: 9999;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                        `;

                        modal.innerHTML = `
                            <h2>Smells in ${fileName}</h2>
                            <ul style="margin-top: 10px; padding-left: 20px;">
                                ${fileSmells.map(smell => `<li>${smell}</li>`).join('')}
                            </ul>
                            <button class="closeModal" style="margin-top: 20px; background: #f06; color: white; padding: 5px 10px; border: none; border-radius: 5px; cursor: pointer;">Close</button>
                        `;

                        document.body.appendChild(modal);
                        modal.querySelector('.closeModal').addEventListener('click', () => modal.remove());
                    });

                    link.parentElement.appendChild(infoIcon);
                }

                // 📊 Metrics icon
                if (Object.keys(metrics).length > 0 && !link.parentElement.querySelector('.metrics-indicator')) {
                    const chartIcon = document.createElement('span');
                    chartIcon.className = 'metrics-indicator';
                    chartIcon.innerHTML = ' 📊';
                    chartIcon.style.cssText = `font-size: 16px; color: #06f; cursor: pointer; margin-left: 4px;`;

                    chartIcon.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();

                        document.querySelectorAll('.metrics-modal').forEach(m => m.remove());

                        const modal = document.createElement('div');
                        modal.className = 'metrics-modal';
                        modal.style.cssText = `
                            position: absolute;
                            color: black;
                            top: ${e.clientY + window.scrollY + 10}px;
                            left: ${e.clientX + window.scrollX + 10}px;
                            width: 520px;
                            background: white;
                            border: 1px solid #ccc;
                            border-radius: 8px;
                            padding: 20px;
                            z-index: 9999;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                        `;

                        const metricEntries = Object.entries(metrics);
                        const bars = metricEntries.map(([key, value]) => {
                            const width = Math.min(100, value); // bar width capped at 100%
                            return `
                                <div style="margin: 8px 0;">
                                    <div>${key}: ${value}</div>
                                    <div style="height: 20px; background: #eee; border-radius: 5px; overflow: hidden;">
                                        <div style="height: 100%; width: ${width}%; background: #06f;"></div>
                                    </div>
                                </div>
                            `;
                        }).join('');

                        modal.innerHTML = `
                            <h2>Metrics in ${fileName}</h2>
                            <div>${bars}</div>
                            <button class="closeMetrics" style="margin-top: 20px; background: #06f; color: white; padding: 5px 10px; border: none; border-radius: 5px; cursor: pointer;">Close</button>
                        `;

                        document.body.appendChild(modal);
                        modal.querySelector('.closeMetrics').addEventListener('click', () => modal.remove());
                    });

                    link.parentElement.appendChild(chartIcon);
                }
            });
        }

        addSmellIconsReliable(smellsByFile);

        let lastUrl = location.href;
        new MutationObserver(() => {
            const currentUrl = location.href;
            if (currentUrl !== lastUrl) {
                lastUrl = currentUrl;
                setTimeout(() => addSmellIconsReliable(smellsByFile), 1000);
            }
        }).observe(document, { subtree: true, childList: true });

    } catch (err) {
        console.error("[EXTENSION] Error:", err);
    }
})();
