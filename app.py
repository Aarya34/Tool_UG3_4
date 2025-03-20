import os
import shutil
import git
from radon.complexity import cc_visit
from radon.metrics import h_visit, mi_visit 
from radon.metrics import h_visit
from radon.raw import analyze
from pathlib import Path

REPO_DIR = "temp_repo"

def analyze_repo(github_url: str):

    if os.path.exists(REPO_DIR):
        shutil.rmtree(REPO_DIR)

    try:
        git.Repo.clone_from(github_url, REPO_DIR)
    except Exception as e:
        print(f"Error cloning repo: {str(e)}")
        return

    python_files = list(Path(REPO_DIR).rglob("*.py"))
    if not python_files:
        print("No Python files found in the repo")
        return

    report = {}
    for file in python_files:
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()
            report[file.name] = analyze_code(code)

    shutil.rmtree(REPO_DIR)  

    print("Code Smells Report:")
    for filename, issues in report.items():
        print(f"\nFile: {filename}")
        for issue, details in issues.items():
            print(f"  {issue}: {details}")

def analyze_code(code: str):
    issues = {}

    complexity_results = cc_visit(code)
    high_complexity = [func.name for func in complexity_results if func.complexity > 10]
    if high_complexity:
        issues["high_complexity_functions"] = high_complexity

    return issues

if __name__ == "__main__":
    repo_url = input("Enter GitHub repository URL: ")
    analyze_repo(repo_url)
