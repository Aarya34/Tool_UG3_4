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
        return

    python_files = list(Path(repo_path).rglob("*.py"))
    js_files = list(Path(repo_path).rglob("*.js"))
    
    print(f"[+] {len(python_files)} Python files found.")
    print(f"[+] {len(js_files)} JavaScript files found.")
    
    report = {}
    for file in python_files:
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()
            report[file.name] = analyze_python_code(code)
    
    smell_report = defaultdict(list)
    for file in js_files:
        smells, details = analyze_js_code(file)
        if smells:
            smell_report[file] = (smells, details)
    
    shutil.rmtree(repo_path)
    
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
    
    return issues
    

def analyze_js_code(file_path):
    smells = []
    function_details = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()
    
    lines = code.splitlines()
    num_lines = len(lines)
    
    function_defs = re.finditer(r'function\s+\w+\s*\([^)]*\)\s*{', code)
    for match in function_defs:
        start = match.start()
        open_braces = 0
        end = start
        for i in range(start, len(code)):
            if code[i] == '{':
                open_braces += 1
            elif code[i] == '}':
                open_braces -= 1
                if open_braces == 0:
                    end = i
                    break
        func_code = code[start:end]
        func_lines = func_code.count('\n') + 1
        function_details.append(func_lines)
        if func_lines > 50:
            smells.append(f"Long Function (>50 lines): {func_lines} lines")
    
    if num_lines > 300:
        smells.append(f"Large File (>300 lines): {num_lines} lines")
    
    console_logs = [line for line in lines if 'console.log' in line]
    if len(console_logs) > 10:
        smells.append(f"Console Log Overuse (>10 logs): {len(console_logs)} logs")
    
    nesting_level = 0
    max_nesting = 0
    for line in lines:
        nesting_level += line.count('{') - line.count('}')
        max_nesting = max(max_nesting, nesting_level)
    if max_nesting >= 4:
        smells.append(f"Deep Nesting (>=4 levels): {max_nesting} levels")
    
    magic_numbers = re.findall(r'[^a-zA-Z](\d+)[^a-zA-Z]', code)
    magic_numbers = [num for num in magic_numbers if num not in ['0', '1']]
    if len(magic_numbers) > 5:
        smells.append(f"Magic Numbers (>5 occurrences): {len(magic_numbers)} found")
    
    return list(set(smells)), {
        'total_lines': num_lines,
        'num_console_logs': len(console_logs),
        'num_functions': len(function_details),
        'function_lengths': function_details,
        'max_nesting_level': max_nesting,
    }

if __name__ == "__main__":
    repo_url = input("Enter GitHub repository URL: ")
    analyze_repo(repo_url)
