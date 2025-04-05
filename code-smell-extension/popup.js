document.getElementById("analyze").addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url;
  
    if (!url.includes("github.com")) {
      alert("Not a GitHub repository!");
      return;
    }
  
    const response = await fetch("http://localhost:5000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: url })
    });
  
    const data = await response.json();
    document.getElementById("result").textContent = JSON.stringify(data, null, 2);
  });
  