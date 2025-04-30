import ast
import astor
import textwrap
from collections import defaultdict
import re


# Refactor: Deeply Nested Functions
def refactor_deeply_nested_functions(code, details=None):
    class FunctionUnnester(ast.NodeTransformer):
        def __init__(self):
            self.new_funcs = []

        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            new_body = []
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef):
                    self.new_funcs.append(stmt)
                else:
                    new_body.append(stmt)
            node.body = new_body
            return node

    tree = ast.parse(code)
    unnester = FunctionUnnester()
    tree = unnester.visit(tree)
    tree.body.extend(unnester.new_funcs)
    ast.fix_missing_locations(tree)
    return astor.to_source(tree)

# Refactor: Too Many Returns
def refactor_too_many_returns(code, details=None):
    class ReturnMerger(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            return_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
            if len(return_nodes) <= 1:
                return node

            var = ast.Name(id='__result', ctx=ast.Store())
            assign_init = ast.Assign(targets=[var], value=ast.Constant(value=None))
            new_body = [assign_init]
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    new_body.append(
                        ast.Assign(
                            targets=[ast.Name(id="__result", ctx=ast.Store())],
                            value=stmt.value if stmt.value else ast.Constant(value=None)
                        )
                    )
                    new_body.append(ast.Break())
                else:
                    new_body.append(stmt)

            new_func_body = [ast.While(test=ast.Constant(value=True), body=new_body, orelse=[])]
            new_func_body.append(ast.Return(value=ast.Name(id="__result", ctx=ast.Load())))
            node.body = new_func_body
            return node

    tree = ast.parse(code)
    tree = ReturnMerger().visit(tree)
    ast.fix_missing_locations(tree)
    return astor.to_source(tree)


# Refactor: Long Lambdas
def refactor_long_lambdas(code, details=None):
    import re
    lines = code.split('\n')
    output = []
    counter = 0
    for line in lines:
        if 'lambda' in line and len(line) > 80:
            name = f'lambda_func_{counter}'
            args_match = re.search(r'lambda\s+(.*?):', line)
            args = args_match.group(1) if args_match else ''
            expr = line.split(':', 1)[-1]
            output.append(f"def {name}({args.strip()}): return {expr.strip()}")
            line = line.replace(f"lambda {args}:{expr}", name)
            counter += 1
        output.append(line)
    return '\n'.join(output)


# Refactor: Duplicate Code (basic heuristic using common substrings)
import hashlib

def refactor_duplicate_code(code, details=None):
    lines = code.splitlines()
    blocks = {}
    block_size = 3
    for i in range(len(lines) - block_size + 1):
        block = "\n".join(lines[i:i + block_size])
        h = hashlib.md5(block.encode()).hexdigest()
        if h in blocks:
            lines[i:i + block_size] = [f"{blocks[h]}()"]
        else:
            blocks[h] = f"extracted_func_{len(blocks)}"

    # append functions
    for h, fname in blocks.items():
        lines.append(f"\ndef {fname}():\n{textwrap.indent('\n'.join(blocks[h].splitlines()), '    ')}")
    return "\n".join(lines)


# Refactor: Feature Envy
def refactor_feature_envy(code, details):
    for fn_name in details:
        code = code.replace(f"{fn_name}.", f"self.{fn_name}_")
    return code

# Refactor: Large Classes (split methods to helpers)
def refactor_large_classes(code, details=None):
    class SplitLargeClass(ast.NodeTransformer):
        def visit_ClassDef(self, node):
            if len(node.body) > 12:
                helper_methods = node.body[8:]
                node.body = node.body[:8]
                helper_class = ast.ClassDef(
                    name=f"{node.name}Helper",
                    bases=[],
                    keywords=[],
                    body=helper_methods,
                    decorator_list=[]
                )
                return [node, helper_class]
            return node

    tree = ast.parse(code)
    tree = SplitLargeClass().visit(tree)
    ast.fix_missing_locations(tree)
    return astor.to_source(tree)


# Refactor: High Complexity Functions (detects many branches)
def refactor_high_complexity(code, details):
    class ComplexityReducer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            branch_count = sum(isinstance(n, (ast.If, ast.For, ast.While)) for n in ast.walk(node))
            if branch_count > 5:
                node.body.insert(0, ast.Expr(value=ast.Str(s='Refactor: high complexity')))
            return node

    tree = ast.parse(code)
    tree = ComplexityReducer().visit(tree)
    return astor.to_source(tree)

# Refactor: Low Maintainability (replace chained expressions)
def refactor_low_maintainability(code, details):
    class ExpressionUnfolder(ast.NodeTransformer):
        def visit_BinOp(self, node):
            if isinstance(node.left, ast.BinOp):
                temp = ast.Name(id="temp_expr", ctx=ast.Load())
                return ast.BinOp(left=temp, op=node.op, right=node.right)
            return node

    tree = ast.parse(code)
    tree = ExpressionUnfolder().visit(tree)
    return astor.to_source(tree)

# Dummy implementations for missing functions

def refactor_useless_exceptions(code, details=None):
    tree = ast.parse(code)

    class ExceptionHandlerFixer(ast.NodeTransformer):
        def visit_Try(self, node):
            self.generic_visit(node)
            for handler in node.handlers:
                if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                    handler.body[0] = ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id="print", ctx=ast.Load()),
                            args=[ast.Constant(value="TODO: handle exception")],
                            keywords=[]
                        )
                    )
            return node

    fixed_tree = ExceptionHandlerFixer().visit(tree)
    ast.fix_missing_locations(fixed_tree)
    return astor.to_source(fixed_tree)


def refactor_dead_code_variables(code, details=None):
    tree = ast.parse(code)
    
    class DeadCodeVariableRemover(ast.NodeTransformer):
        def visit_Assign(self, node):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if any(target in details for target in targets):
                return None  # Removes the assignment
            return node

    tree = DeadCodeVariableRemover().visit(tree)
    ast.fix_missing_locations(tree)
    return astor.to_source(tree)

def refactor_excessive_comments(code, details=None):
    tree = ast.parse(code)
    
    class CommentRemover(ast.NodeTransformer):
        def visit_Comment(self, node):
            return None  # Removes comments completely

    tree = CommentRemover().visit(tree)
    ast.fix_missing_locations(tree)
    return astor.to_source(tree)


def refactor_large_functions(code, details=None):
    tree = ast.parse(code)
    
    class LargeFunctionSplitter(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if len(node.body) > 20:
                # Create helper function for the first part
                new_func_name = f"{node.name}_helper"
                helper_func = ast.FunctionDef(
                    name=new_func_name,
                    args=node.args,
                    body=node.body[10:],  # The second half of the function
                    decorator_list=[]
                )
                node.body = node.body[:10]  # Keep the first half in the main function
                tree.body.append(helper_func)
                node.body.append(ast.Return(value=ast.Name(id=new_func_name, ctx=ast.Load())))  # Add call to helper
            return node

    tree = LargeFunctionSplitter().visit(tree)
    ast.fix_missing_locations(tree)
    return astor.to_source(tree)

def refactor_data_clumps(code, details=None):
    # Detects repeated parameter groups and refactors them into a dataclass
    tree = ast.parse(code)

    class DataClumpExtractor(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            param_names = [arg.arg for arg in node.args.args]
            if len(param_names) > 3:  # Arbitrary threshold
                clump_vars = param_names[:3]  # Extract first 3 variables (for simplicity)
                new_class_name = "DataClump"
                dataclass_definition = f"""
                @dataclass
                class {new_class_name}:
                    {'\n    '.join([f'{var}: str' for var in clump_vars])}
                """
                node.body.insert(0, ast.Expr(value=ast.Constant(value=dataclass_definition.strip())))
                # Replace usage of multiple parameters with the new class
                for arg in clump_vars:
                    node.args.args.remove(next(a for a in node.args.args if a.arg == arg))
                return node
            return node

    tree = DataClumpExtractor().visit(tree)
    ast.fix_missing_locations(tree)
    return astor.to_source(tree)

def refactor_shotgun_surgery(code, details=None):
    for loc in details:
        # Add a comment indicating the location is affected by shotgun surgery
        code = code.replace(loc, f"# Shotgun surgery: Refactor to group related logic\n{loc}")
    return code


def refactor_large_file(code, details):
    # Add comment at the top
    return "# This file is large, consider splitting it\n\n" + code

# Mapping substrings to smell identifiers used in REFACTOR_FUNCTIONS
SMELL_KEYWORDS = {
    "High Complexity Functions": "high_complexity_functions",
    "Low Maintainability Index": "low_maintainability",
    "Large File": "large_file",
    "Deeply Nested Functions": "deeply_nested_functions",
    "Large Functions": "large_functions",
    "Feature Envy": "feature_envy",
    "Data Clumps": "data_clumps",
    "Dead Code Variables": "dead_code_variables",
    "Shotgun Surgery": "shotgun_surgery",
    "Long Lambdas": "long_lambdas",
    "Useless Exceptions": "useless_exceptions",
    "Duplicate Code": "duplicate_code",
    "Large Classes": "large_classes",
    "Too Many Returns": "too_many_returns",
    "Too Many Parameters": "too_many_parameters",  # Optional if you define its refactor
}

# Mapping smell types to refactoring functions
REFACTOR_FUNCTIONS = {
    "useless_exceptions": refactor_useless_exceptions,
    "dead_code_variables": refactor_dead_code_variables,
    "duplicate_code": refactor_duplicate_code,
    "feature_envy": refactor_feature_envy,
    "large_classes": refactor_large_classes,
    "too_many_returns": refactor_too_many_returns,
    "large_functions": refactor_large_functions,
    "long_lambdas": refactor_long_lambdas,
    "data_clumps": refactor_data_clumps,
    "shotgun_surgery": refactor_shotgun_surgery,
    "high_complexity_functions": refactor_high_complexity,
    "low_maintainability": refactor_low_maintainability,
    "deeply_nested_functions": refactor_deeply_nested_functions,
    "large_file": refactor_large_file,
}

def refactor_python_code(code: str, smell_list: list) -> str:
    for smell_description in smell_list:
        for keyword, smell_type in SMELL_KEYWORDS.items():
            if keyword in smell_description:
                refactor_fn = REFACTOR_FUNCTIONS.get(smell_type)
                if refactor_fn:
                    try:
                        code = refactor_fn(code, smell_description)
                    except Exception as e:
                        print(f"Error while refactoring {smell_type}: {e}")
                break
    return code
