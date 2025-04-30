import os
import re
import shutil
import git
import tempfile
import subprocess
from pathlib import Path
from collections import defaultdict, Counter
from radon.complexity import cc_visit
from radon.metrics import h_visit, mi_visit
from radon.raw import analyze
import ast
import json
import os
import stat
from refactoring_suggestions import (
    get_python_refactoring_examples,
    get_javascript_refactoring_examples
)

REPO_DIR = "temp_repo"


def clone_github_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    print(f"[+] Cloning repo into {temp_dir} ...")
    try:
        git.Repo.clone_from(repo_url, temp_dir)
    except Exception as e:
        print(f"Error cloning repo: {str(e)}")
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
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()
            smells = analyze_python_code(code)
            # Add refactoring examples for each smell
            report[file.name] = {
                smell_type: {
                    'details': details,
                    'refactoring_example': get_python_refactoring_examples(smell_type, details)
                }
                for smell_type, details in smells.items()
            }
    
    smell_report = {}
    for file in js_files:
        smell_report[file.name] = analyze_js_code(file)
    
    shutil.rmtree(repo_path, onerror=lambda _, path, __: os.chmod(path, stat.S_IWRITE))
    
    # Combine Python and JavaScript smells into a single report
    combined_report = {
        "python": report,
        "javascript": smell_report
    }
    
    # Write the combined report to a JSON file
    output_file = "code_smells_report.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(combined_report, json_file, indent=4)
    
    print(f"\n[+] Code smells report saved to {output_file}")
    return combined_report

    print("\nCode Smells Report (Python):")
    for filename, issues in report.items():
        print(f"\nFile: {filename}")
        for issue, details in issues.items():
            print(f"  {issue}: {details}")
    
    print("\nCode Smells Report (JavaScript):")
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

def analyze_python_code(code: str):
    issues = {}
    complexity_results = cc_visit(code)
    high_complexity = [func.name for func in complexity_results if func.complexity > 10]
    if high_complexity:
        issues["high_complexity_functions"] = high_complexity
    
    halstead_metrics = h_visit(code)
    maintainability_index = mi_visit(code, halstead_metrics)
    if maintainability_index < 20:
        issues["low_maintainability"] = maintainability_index
    
    raw_metrics = analyze(code)
    if raw_metrics.loc > 500:
        issues["large_file"] = raw_metrics.loc

    tree = ast.parse(code)

    def get_nesting_depth(node, depth=0):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.FunctionDef)):
            depth += 1
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            max_depth = max(max_depth, get_nesting_depth(child, depth))
        return max_depth

    deep_nested_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and get_nesting_depth(node) > 3
    ]
    if deep_nested_functions:
        issues["deeply_nested_functions"] = deep_nested_functions
        
    long_lambdas = [
    node.lineno for node in ast.walk(tree)
    if isinstance(node, ast.Lambda) and isinstance(node.body, (ast.List, ast.Tuple)) and len(node.body.elts) > 3
]

    if long_lambdas:
        issues["long_lambdas"] = long_lambdas

    useless_exceptions = [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.Try) and any(
            isinstance(handler.body[0], ast.Pass) if handler.body else True for handler in node.handlers
        )
    ]
    if useless_exceptions:
        issues["useless_exceptions"] = useless_exceptions
     
    function_bodies = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):