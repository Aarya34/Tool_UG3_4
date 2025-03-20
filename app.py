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
        if isinstance(node, ast.Lambda) and len(node.body.elts) > 3
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
            body_str = "".join(ast.dump(stmt) for stmt in node.body)
            function_bodies[body_str].append(node.name)
    duplicates = [funcs for funcs in function_bodies.values() if len(funcs) > 1]
    if duplicates:
        issues["duplicate_code"] = duplicates

    comment_lines = sum(1 for line in code.split("\n") if line.strip().startswith("#"))
    total_lines = len(code.split("\n"))
    if total_lines > 0 and (comment_lines / total_lines) > 0.3:
        issues["excessive_comments"] = f"{(comment_lines / total_lines) * 100:.2f}% comments"

    large_classes = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and sum(isinstance(n, ast.FunctionDef) for n in node.body) > 10
    ]
    if large_classes:
        issues["large_classes"] = large_classes
    
    def count_return_statements(node):
        return sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))
    many_return_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and count_return_statements(node) > 3
    ]
    if many_return_functions:
        issues["too_many_returns"] = many_return_functions

    large_functions = [
        node.name for node in ast.walk(tree) 
        if isinstance(node, ast.FunctionDef) and len(node.body) > 100
    ]
    if large_functions:
        issues["large_functions"] = large_functions

    feature_envy_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            method_calls = [n for n in ast.walk(node) if isinstance(n, ast.Attribute)]
            external_calls = [n for n in method_calls if isinstance(n.value, ast.Name)]
            if len(external_calls) > 5:
                feature_envy_funcs.append(node.name)
    if feature_envy_funcs:
        issues["feature_envy"] = feature_envy_funcs

    function_params = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            params = tuple(arg.arg for arg in node.args.args)
            function_params.append(params)

    repeated_params = {p for p in function_params if function_params.count(p) > 1}
    if repeated_params:
        issues["data_clumps"] = [list(p) for p in repeated_params]

    assigned_vars = set()
    used_vars = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_vars.add(target.id)
        elif isinstance(node, ast.Name):
            used_vars.add(node.id)
    dead_vars = assigned_vars - used_vars
    if dead_vars:
        issues["dead_code_variables"] = list(dead_vars)

    function_calls = defaultdict(int)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function_calls[node.func.id] += 1
    frequent_changes = [name for name, count in function_calls.items() if count > 10]
    if frequent_changes:
        issues["shotgun_surgery"] = frequent_changes
    
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
