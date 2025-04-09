import os
import shutil
import git
import tempfile
import stat
import json
from pathlib import Path
from py_analyzer import analyze_python_code
from js_analyzer import analyze_js_code

REPO_DIR = "temp_repo"

def clone_github_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    print(f"[+] Cloning repo into {temp_dir} ...")
    try:
        git.Repo.clone_from(repo_url, temp_dir)
    except Exception as e:
        print(f"[-] Error cloning repo: {str(e)}")
        return None
    print("[+] Clone complete.")
    return temp_dir


def analyze_repo(repo_url):
    repo_path = clone_github_repo(repo_url)
    if not repo_path:
        raise ValueError(f"Failed to clone repository: {repo_url}")

    python_files = list(Path(repo_path).rglob("*.py"))
    js_files = list(Path(repo_path).rglob("*.js"))
    
    print(f"[+] {len(python_files)} Python files found.")
    print(f"[+] {len(js_files)} JavaScript files found.")
    
    report = {}
    for file in python_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()
                report[file.name] = analyze_python_code(code)
        except Exception as e:
            print(f"[-] Error analyzing Python file {file.name}: {str(e)}")

    smell_report = {}
    for file in js_files:
        try:
            smells, details = analyze_js_code(file)
            smell_report[file.name] = (smells, details)
        except Exception as e:
            print(f"[-] Error analyzing JS file {file.name}: {str(e)}")

    # Clean up temp repo (force delete if needed)
    shutil.rmtree(repo_path, onerror=lambda _, path, __: os.chmod(path, stat.S_IWRITE))

    combined_report = {
        "python": report,
        "javascript": smell_report
    }

    # Save report to JSON
    output_file = "code_smells_report.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(combined_report, json_file, indent=4)
    
    print(f"\n[+] Code smells report saved to {output_file}")

    # Optional: Print results to console
    print("\n[Python Code Smells]")
    for filename, issues in report.items():
        print(f"\nFile: {filename}")
        for issue, detail in issues.items():
            print(f"  {issue}: {detail}")

    print("\n[JavaScript Code Smells]")
    for file, (smells, details) in smell_report.items():
        print("\n==========")
        print(f"File: {file}")
        print(f"Total Lines: {details['total_lines']}")
        print(f"Functions: {details['num_functions']}, Lengths: {details['function_lengths']}")
        print(f"Console Logs: {details['num_console_logs']}")
        print(f"Max Nesting Level: {details['max_nesting_level']}")
        print("Detected Smells:")
        for smell in smells:
            print(f"  - {smell}")

    return {
        "python": report,
        "javascript": smell_report,
        "metadata": {
            "python_files": len(python_files),
            "js_files": len(js_files),
            "repo": repo_url
        }
    }


if __name__ == "__main__":
    repo_url = input("Enter GitHub repository URL: ").strip()
    try:
        analyze_repo(repo_url)
    except Exception as e:
        print(f"[-] Failed to analyze repo: {e}")