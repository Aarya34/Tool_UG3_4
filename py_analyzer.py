import ast
from radon.complexity import cc_visit
from radon.metrics import h_visit, mi_visit
from radon.raw import analyze
from collections import defaultdict

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