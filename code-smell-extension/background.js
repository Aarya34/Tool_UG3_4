chrome.action.onClicked.addListener((tab) => {
    if (tab.url && tab.url.includes("github.com")) {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"]
      });
    } else {
      alert("Not a GitHub repo page.");
    }
  });
  