import ast
from radon.complexity import cc_visit
from radon.metrics import h_visit, mi_visit
from radon.raw import analyze
from collections import defaultdict

def analyze_py_code(file_path):
    smells = []
    metrics = {}

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()

    complexity_results = cc_visit(code)
    high_complexity = [(func.name, func.complexity) for func in complexity_results if func.complexity > 10]
    if high_complexity:
        smells.append(f"High Complexity Functions (>10): {len(high_complexity)} - {[f'{n}({c})' for n, c in high_complexity]}")

    halstead_metrics = h_visit(code)
    maintainability_index = mi_visit(code, halstead_metrics)
    if maintainability_index < 20:
        smells.append(f"Low Maintainability Index (<20): {maintainability_index:.2f}")

    raw_metrics = analyze(code)
    metrics["total_lines"] = raw_metrics.loc
    if raw_metrics.loc > 500:
        smells.append(f"Large File (>500 lines): {raw_metrics.loc} lines")

    tree = ast.parse(code)

    def get_nesting_depth(node, depth=0):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.FunctionDef)):
            depth += 1
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            max_depth = max(max_depth, get_nesting_depth(child, depth))
        return max_depth

    deeply_nested = [(node.name, get_nesting_depth(node)) for node in ast.walk(tree)
                     if isinstance(node, ast.FunctionDef) and get_nesting_depth(node) > 3]
    if deeply_nested:
        smells.append(f"Deeply Nested Functions (>3): {len(deeply_nested)} - {[f'{n}({d})' for n, d in deeply_nested]}")

    large_funcs = [(node.name, len(node.body)) for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef) and len(node.body) > 100]
    if large_funcs:
        smells.append(f"Large Functions (>100 lines): {len(large_funcs)} - {[f'{n}({l})' for n, l in large_funcs]}")

    feature_envy = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Attribute)]
            external = [n for n in calls if isinstance(n.value, ast.Name)]
            if len(external) > 5:
                feature_envy.append((node.name, len(external)))
    if feature_envy:
        smells.append(f"Feature Envy (>5 external calls): {len(feature_envy)} - {[f'{n}({c})' for n, c in feature_envy]}")

    function_params = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            params = tuple(arg.arg for arg in node.args.args)
            function_params.append(params)
    repeated_params = {p for p in function_params if function_params.count(p) > 1}
    if repeated_params:
        smells.append(f"Data Clumps (Repeated params): {len(repeated_params)} sets - {list(map(list, repeated_params))}")

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
        smells.append(f"Dead Code Variables (Unused): {len(dead_vars)} - {list(dead_vars)}")

    function_calls = defaultdict(int)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function_calls[node.func.id] += 1
    frequent_calls = [(name, count) for name, count in function_calls.items() if count > 10]
    if frequent_calls:
        smells.append(f"Shotgun Surgery (Function called >10 times): {len(frequent_calls)} - {frequent_calls}")

    long_lambdas = [node.lineno for node in ast.walk(tree)
                    if isinstance(node, ast.Lambda) and isinstance(node.body, (ast.List, ast.Tuple)) and len(node.body.elts) > 3]
    if long_lambdas:
        smells.append(f"Long Lambdas (>3 elements): {len(long_lambdas)} - lines {long_lambdas}")

    useless_exceptions = [node.lineno for node in ast.walk(tree)
                          if isinstance(node, ast.Try) and any(
                              isinstance(handler.body[0], ast.Pass) if handler.body else True for handler in node.handlers)]
    if useless_exceptions:
        smells.append(f"Useless Exceptions (Try-Pass): {len(useless_exceptions)} - lines {useless_exceptions}")

    function_bodies = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body_str = "".join(ast.dump(stmt) for stmt in node.body)
            function_bodies[body_str].append(node.name)
    duplicates = [funcs for funcs in function_bodies.values() if len(funcs) > 1]
    if duplicates:
        smells.append(f"Duplicate Code (Identical functions): {len(duplicates)} sets - {duplicates}")

    large_classes = [(node.name, sum(isinstance(n, ast.FunctionDef) for n in node.body))
                     for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                     and sum(isinstance(n, ast.FunctionDef) for n in node.body) > 10]
    if large_classes:
        smells.append(f"Large Classes (>10 methods): {len(large_classes)} - {[f'{n}({m})' for n, m in large_classes]}")

    def count_return_statements(node):
        return sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))

    many_returns = [(node.name, count_return_statements(node)) for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and count_return_statements(node) > 3]
    if many_returns:
        smells.append(f"Too Many Returns (>3): {len(many_returns)} - {[f'{n}({c})' for n, c in many_returns]}")

    global_vars = [node.id for node in ast.walk(tree)
                   if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in assigned_vars]
    if global_vars:
        smells.append(f"Global Variables (Not in function/class): {len(set(global_vars))} - {list(set(global_vars))}")

    too_many_args = [(node.name, len(node.args.args)) for node in ast.walk(tree)
                     if isinstance(node, ast.FunctionDef) and len(node.args.args) > 5]
    if too_many_args:
        smells.append(f"Too Many Parameters (>5): {len(too_many_args)} - {[f'{n}({c})' for n, c in too_many_args]}")

    # Extra Metrics
    metrics["num_functions"] = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    metrics["function_lengths"] = [len(node.body) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    metrics["num_prints"] = sum(1 for node in ast.walk(tree)
                                if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'print')

    return smells, metrics


# if __name__ == "__main__":
#     smells, metrics = analyze_py_code("sample.py")
#     print("Detected Smells:")
#     for smell in smells:
#         print("-", smell)
#     print("\nCode Metrics:")
#     for key, value in metrics.items():
#         print(f"{key}: {value}")
