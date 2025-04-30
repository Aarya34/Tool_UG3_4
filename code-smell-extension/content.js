(async () => {

    const pathParts = window.location.pathname.split('/');

    if (pathParts.length < 3 || !pathParts[1] || !pathParts[2]) {
        console.log("[EXTENSION] Not a repository page. Skipping analysis.");
        return;
    }
    const repoPath = window.location.pathname.split('/').slice(1, 3).join('/');
    const repoUrl = https://github.com/${repoPath};
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