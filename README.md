# Code Smell Detector for GitHub Repositories

## Project Overview
Our project aims to improve code quality in open-source repositories by detecting **code smells** in **JavaScript** and **Python**. The tool is divided into two releases:

- **Release-1 (R1):** Code Smell Detector  
- **Release-2 (R2):** Automatic and Semi-Automatic Refactoring Suggestions

**Release-1** focuses on detecting various code smells through a **Chrome extension** that integrates directly into **GitHub**, enabling developers to identify and analyze problematic code patterns easily.

---

## Features

- **Browser-Based Detection:** A local Chrome extension that activates on GitHub repository pages.
- **Interactive UI:** A small icon appears next to each folder in a repo. Clicking it triggers smell detection.
- **File Metrics View:** A statistics icon is also shown beside the info icon. Clicking it displays file-level metrics like- Total number of lines, Average function length, etc.
- **Language Support:** Supports both **JavaScript** and **Python** codebases.
- **Smell Highlighting:** Generates a list of detected smells with **file-wise** and **folder-wise** breakdowns.
- **Smell Report Storage:** All detected smells are stored in `code_smells_report.json` in the repo's root directory.
- **Dual Code Editor:** Displays both original and refactored code side by side.
- **Code Highlighting:** Uses CodeMirror to color and format the code properly.
- **Language Detection:** Supports both Python and JavaScript syntax highlighting.
- **Auto Refactor:** Automatically sends code and smell list to backend and displays the refactored changes.
---

## Code Smells Detected

### JavaScript
- Long Functions  
- Too Many Parameters  
- Large Files  
- Console Log Overuse  
- Deep Nesting  
- Magic Numbers  
- Duplicate Code  
- Unused Variables  
- Callback Hell  
- Long Chained Calls  
- Inconsistent Naming  
- Low Comment Density  
- Empty Catch Blocks  
- Unnecessary Semicolons  

### Python
- High Complexity Functions  
- Low Maintainability Index  
- Large Files  
- Deeply Nested Functions  
- Large Functions  
- Feature Envy  
- Data Clumps  
- Dead Code (Unused Variables)  
- Shotgun Surgery  
- Long Lambdas
- Useless Exceptions  
- Duplicate Code  
- Large Classes  
- Too Many Returns  
- Global Variables  
- Large Parameters  

---

## Running the Tool

1. **Run the Backend:**
   ```
   python server.py
   ```
2. **Run the html:** *(in new terminal)*
   ```
   cd refactor
   python -m http.server 3000
   ```
3.  Load the Chrome Extension
    - Open Chrome and go to: `chrome://extensions/`
    - Enable **Developer Mode** (top right)
    - Click **Load Unpacked** (top left)
    - Select the folder named: `code-smell-extension`

4. Use the Extension on GitHub
    - Open any **public GitHub repository** in a new tab.
    - Click on the **extension icon** (toggle it ON if needed).
    - A small 🛈 (info icon) and 📊 Stats Icon will appear next to each **file/folder**.
    - Click the i icon to view **all detected code smells** for that folder and on 📊 icon to show **refactored code**.

#### Testing Repo - https://github.com/akash-madugundi/testing.git
---

## Methodology & Techniques

### Frontend (Chrome Extension)

- Injects a **content script** into GitHub pages.
- Detects folder structure dynamically and **attaches a clickable icons**.
- Sends **repository URL** and **file paths** to the backend.

### Backend (Python API)

- **Clones** the GitHub repository locally.
- Parses `.js` and `.py` files using:
  - **AST (Abstract Syntax Tree)** analysis for Python.
  - **ESLint** or **Custom Parsers** for JavaScript.
- Applies **rule-based logic** and **heuristics** to detect code smells.
- Aggregates results and sends them back to the extension.

---

## Smell Detection Techniques

- **Cyclomatic Complexity Analysis**
- **Line and Character Thresholds** for file/function size
- **Pattern Matching** for:
  - Console logs
  - Deep nesting
  - Magic numbers
- **Name Pattern Checks** for inconsistent naming
- **Structural Analysis** using AST for:
  - Nesting
  - Dead code
  - Return statements

---

## Contributions

- **Akshatha RH** (CS22B003) - (for js)  Duplicate Code, Too Many Parameters, Unused Variables smells, Low Comment Density, Empty Catch Blocks, Global variables, Refactored code editor
- **A Sai Preethika** (CS22B006) - (for py) Long lambdas, Useless exceptions ,Duplicate code ,Large classes, Too many returns, Display of smell info on icon click, Code editor highlighting
- **Ch Aarya** (CS22B018) - (for py) High complexity functions, Low maintainability, Large file, Globalvariables, Large parameters smells, Integrated code to chrome extension, Py Refactored code
- **K Sanjay Varshith** (CS22B029) - (for py)  Deeply nested functions, Large functions, Feature envy, Data clumps, Dead code variables, Display of info icon beside smelly files, Py Refactored code
- **K Akhil Solomon** (CS22B032) - Callback Hell, Long Chained Calls , Inconsistent Naming smell, Shotgun surgery smell, Unnecessary Semicolons smell,  Useless exceptions smell, Js refactored code
- **M Akash** (CS22B037) -  Long Function smell, Large File smell, Console Log Overuse smell, Deep Nesting smell, Magic Numbers smell, Dead code variables smell, Graph metrics, Js refactored code
