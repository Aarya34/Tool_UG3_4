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
            report[file.name] = analyze_python_code(code)
    
    smell_report = {}
    for file in js_files:
        smells, details = analyze_js_code(file)
        smell_report[file.name] = (smells, details) 
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
    return {
            "python": report,
            "javascript": smell_report,
            "metadata": {
                "python_files": len(python_files),
                "js_files": len(js_files),
                "repo": repo_url
            }
    }

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

    too_many_arguments = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and len(node.args.args) > 5
    ]
    if too_many_arguments:
        issues["too_many_arguments"] = too_many_arguments

    return issues
    

def analyze_js_code(file_path):
    smells = []
    function_details = []
    global_variables = []

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()

    lines = code.splitlines()
    num_lines = len(lines)

    # --- Global Variables ---
    var_decls = re.findall(r'(?:var|let|const)\s+(\w+)', code)
    for var in var_decls:
        if not re.search(rf'function\s+\w+\s*\(.*\)\s*{{.*\b{var}\b.*}}', code):
            global_variables.append(var)
    if global_variables:
        smells.append(f"Global Variables Found: {len(global_variables)} variables")

    # --- Long Function & Too Many Parameters ---
    function_defs = re.finditer(r'function\s+(\w+)?\s*\(([^)]*)\)\s*{', code)
    for match in function_defs:
        start = match.start()
        params = match.group(2).split(',')
        param_count = len([p.strip() for p in params if p.strip()])
        if param_count > 4:
            smells.append(f"Too Many Parameters (>4): {param_count} parameters")

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

    # --- Large File ---
    if num_lines > 300:
        smells.append(f"Large File (>300 lines): {num_lines} lines")

    # --- Console Log Overuse ---
    console_logs = [line for line in lines if 'console.log' in line]
    if len(console_logs) > 10:
        smells.append(f"Console Log Overuse (>10 logs): {len(console_logs)} logs")

    # --- Deep Nesting ---
    nesting_level = 0
    max_nesting = 0
    for line in lines:
        nesting_level += line.count('{') - line.count('}')
        max_nesting = max(max_nesting, nesting_level)
    if max_nesting >= 4:
        smells.append(f"Deep Nesting (>=4 levels): {max_nesting} levels")

    # --- Magic Numbers ---
    magic_numbers = re.findall(r'[^a-zA-Z](\d+)[^a-zA-Z]', code)
    magic_numbers = [num for num in magic_numbers if num not in ['0', '1']]
    if magic_numbers:
        smells.append(f"Magic Numbers Found: {len(magic_numbers)} occurrences")

    # --- Duplicate Code Blocks (3+ lines repeated) ---
    block_counts = defaultdict(int)
    for i in range(len(lines) - 2):
        block = tuple(lines[i:i+3])
        if all(line.strip() for line in block):  # non-empty lines
            block_counts[block] += 1
    duplicate_blocks = [block for block, count in block_counts.items() if count > 1]
    if duplicate_blocks:
        smells.append(f"Duplicate Code Blocks: {len(duplicate_blocks)} blocks repeated")

    # --- Unused Variables ---
    unused_vars = []
    for var in var_decls:
        if len(re.findall(r'\b' + re.escape(var) + r'\b', code)) == 1:
            unused_vars.append(var)
    if unused_vars:
        smells.append(f"Unused Variables: {len(unused_vars)} variables")

    # --- Long Chained Calls ---
    long_chains = re.findall(r'\w+\.(?:\w+\.){3,}', code)
    if long_chains:
        smells.append(f"Long Chained Calls Found: {len(long_chains)} chains")

    # --- Inconsistent Naming ---
    camel_case_vars = re.findall(r'\b[a-z][a-zA-Z0-9]*\b', code)
    snake_case_vars = re.findall(r'\b[a-z0-9]+(?:_[a-z0-9]+)+\b', code)
    inconsistent_names = [name for name in camel_case_vars if name in snake_case_vars]
    if inconsistent_names:
        smells.append(f"Inconsistent Naming Found: {len(inconsistent_names)} inconsistencies")

    # --- Callback Hell (Deeply Nested Callbacks) ---
    callback_patterns = re.findall(r'\(\s*function\s*\(.*\)\s*\{', code)
    nested_callbacks = [callback for callback in callback_patterns if callback.count('{') > 3]
    if nested_callbacks:
        smells.append(f"Callback Hell Detected: {len(nested_callbacks)} deeply nested callbacks")

    # --- Low Comment Density ---
    comments = [line for line in lines if line.strip().startswith('//') or line.strip().startswith('/*')]
    comment_ratio = len(comments) / num_lines if num_lines else 0
    if comment_ratio < 0.02:
        smells.append(f"Low Comment Density (<2%): {len(comments)} comments")

    # --- Empty Catch Blocks ---
    empty_catches = re.findall(r'catch\s*\(.*\)\s*\{\s*\}', code)
    if empty_catches:
        smells.append(f"Empty Catch Blocks Found: {len(empty_catches)} blocks")

    # --- Unnecessary Semicolons ---
    unnecessary_semis = [line for line in lines if line.strip() == ';']
    if unnecessary_semis:
        smells.append(f"Unnecessary Semicolons: {len(unnecessary_semis)} found")

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
