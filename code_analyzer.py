import ast
import re
from typing import Dict, List, Tuple, Any
import astor
from collections import defaultdict

class CodeAnalyzer:
    def __init__(self, code: str, language: str):
        self.code = code
        self.language = language
        self.tree = ast.parse(code) if language == 'python' else None
        self.smells = {}
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze the code and return detected smells with refactoring suggestions."""
        if self.language == 'python':
            self._analyze_python()
        else:
            self._analyze_javascript()
        return self.smells
    
    def _analyze_python(self):
        """Analyze Python code for smells and generate specific refactoring suggestions."""
        # High Complexity Functions
        self._analyze_complex_functions()
        
        # Deep Nesting
        self._analyze_nesting()
        
        # Feature Envy
        self._analyze_feature_envy()
        
        # Duplicate Code
        self._analyze_duplicate_code()
        
        # Long Methods
        self._analyze_long_methods()
        
        # Magic Numbers
        self._analyze_magic_numbers()
        
        # Unused Variables
        self._analyze_unused_variables()
    
    def _analyze_javascript(self):
        """Analyze JavaScript code for smells and generate specific refactoring suggestions."""
        # Global Variables
        self._analyze_global_variables()
        
        # Callback Hell
        self._analyze_callback_hell()
        
        # Magic Numbers
        self._analyze_magic_numbers()
        
        # Duplicate Code
        self._analyze_duplicate_code()
        
        # Unused Variables
        self._analyze_unused_variables()
        
        # Deep Nesting
        self._analyze_nesting()
    
    def _analyze_complex_functions(self):
        """Analyze functions for high cyclomatic complexity."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    func_code = astor.to_source(node)
                    self.smells[f"high_complexity_{node.name}"] = {
                        "type": "high_complexity",
                        "details": f"Function '{node.name}' has complexity of {complexity}",
                        "refactoring": self._suggest_complexity_refactoring(node, func_code)
                    }
    
    def _analyze_nesting(self):
        """Analyze code for deep nesting."""
        if self.language == 'python':
            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef):
                    max_depth = self._get_max_nesting_depth(node)
                    if max_depth > 3:
                        func_code = astor.to_source(node)
                        self.smells[f"deep_nesting_{node.name}"] = {
                            "type": "deep_nesting",
                            "details": f"Function '{node.name}' has nesting depth of {max_depth}",
                            "refactoring": self._suggest_nesting_refactoring(node, func_code)
                        }
        else:
            # JavaScript nesting analysis
            nested_patterns = re.finditer(r'\(\s*function\s*\(.\)\s\{', self.code)
            for match in nested_patterns:
                start = match.start()
                end = self._find_matching_brace(self.code, start)
                if end != -1:
                    nested_code = self.code[start:end+1]
                    if nested_code.count('{') > 3:
                        self.smells[f"deep_nesting_{start}"] = {
                            "type": "deep_nesting",
                            "details": "Deeply nested callback function found",
                            "refactoring": self._suggest_js_nesting_refactoring(nested_code)
                        }
    
    def _analyze_feature_envy(self):
        """Analyze code for feature envy."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                external_calls = self._count_external_calls(node)
                if external_calls > 5:
                    func_code = astor.to_source(node)
                    self.smells[f"feature_envy_{node.name}"] = {
                        "type": "feature_envy",
                        "details": f"Function '{node.name}' makes {external_calls} external calls",
                        "refactoring": self._suggest_feature_envy_refactoring(node, func_code)
                    }
    
    def _analyze_duplicate_code(self):
        """Analyze code for duplication."""
        if self.language == 'python':
            function_bodies = defaultdict(list)
            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef):
                    body_str = "".join(ast.dump(stmt) for stmt in node.body)
                    function_bodies[body_str].append(node)
            
            for body, funcs in function_bodies.items():
                if len(funcs) > 1:
                    func_code = astor.to_source(funcs[0])
                    self.smells[f"duplicate_code_{funcs[0].name}"] = {
                        "type": "duplicate_code",
                        "details": f"Code duplicated in functions: {', '.join(f.name for f in funcs)}",
                        "refactoring": self._suggest_duplicate_code_refactoring(funcs, func_code)
                    }
        else:
            # JavaScript duplicate code analysis
            lines = self.code.split('\n')
            block_counts = defaultdict(int)
            for i in range(len(lines) - 2):
                block = tuple(lines[i:i+3])
                if all(line.strip() for line in block):
                    block_counts[block] += 1
            
            for block, count in block_counts.items():
                if count > 1:
                    self.smells[f"duplicate_code_{hash(block)}"] = {
                        "type": "duplicate_code",
                        "details": f"Code block duplicated {count} times",
                        "refactoring": self._suggest_js_duplicate_code_refactoring(block)
                    }
    
    def _analyze_long_methods(self):
        """Analyze methods for excessive length."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                lines = len(node.body)
                if lines > 20:
                    func_code = astor.to_source(node)
                    self.smells[f"long_method_{node.name}"] = {
                        "type": "long_method",
                        "details": f"Function '{node.name}' has {lines} lines",
                        "refactoring": self._suggest_long_method_refactoring(node, func_code)
                    }
    
    def _analyze_magic_numbers(self):
        """Analyze code for magic numbers."""
        if self.language == 'python':
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Num) and node.n not in [0, 1]:
                    self.smells[f"magic_number_{node.n}"] = {
                        "type": "magic_number",
                        "details": f"Magic number found: {node.n}",
                        "refactoring": self._suggest_magic_number_refactoring(node)
                    }
        else:
            # JavaScript magic number analysis
            magic_numbers = re.findall(r'[^a-zA-Z](\d+)[^a-zA-Z]', self.code)
            magic_numbers = [num for num in magic_numbers if num not in ['0', '1']]
            if magic_numbers:
                self.smells["magic_numbers"] = {
                    "type": "magic_number",
                    "details": f"Magic numbers found: {', '.join(magic_numbers)}",
                    "refactoring": self._suggest_js_magic_number_refactoring(magic_numbers)
                }
    
    def _analyze_unused_variables(self):
        """Analyze code for unused variables."""
        if self.language == 'python':
            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef):
                    unused = self._find_unused_variables(node)
                    if unused:
                        self.smells[f"unused_variables_{node.name}"] = {
                            "type": "unused_variables",
                            "details": f"Unused variables in '{node.name}': {', '.join(unused)}",
                            "refactoring": self._suggest_unused_variables_refactoring(node, unused)
                        }
        else:
            # JavaScript unused variables analysis
            var_decls = re.findall(r'(?:var|let|const)\s+(\w+)', self.code)
            unused_vars = []
            for var in var_decls:
                if len(re.findall(r'\b' + re.escape(var) + r'\b', self.code)) == 1:
                    unused_vars.append(var)
            if unused_vars:
                self.smells["unused_variables"] = {
                    "type": "unused_variables",
                    "details": f"Unused variables: {', '.join(unused_vars)}",
                    "refactoring": self._suggest_js_unused_variables_refactoring(unused_vars)
                }
    
    def _analyze_global_variables(self):
        """Analyze JavaScript code for global variables."""
        global_vars = re.findall(r'(?:var|let|const)\s+(\w+)', self.code)
        if global_vars:
            self.smells["global_variables"] = {
                "type": "global_variables",
                "details": f"Global variables found: {', '.join(global_vars)}",
                "refactoring": self._suggest_global_variables_refactoring(global_vars)
            }
    
    def _analyze_callback_hell(self):
        """Analyze JavaScript code for callback hell."""
        callback_patterns = re.findall(r'\(\s*function\s*\(.\)\s\{', self.code)
        nested_callbacks = [callback for callback in callback_patterns if callback.count('{') > 3]
        if nested_callbacks:
            self.smells["callback_hell"] = {
                "type": "callback_hell",
                "details": "Deeply nested callbacks found",
                "refactoring": self._suggest_callback_hell_refactoring(nested_callbacks)
            }
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
        return complexity
    
    def _get_max_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth of a function."""
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.FunctionDef)):
            depth += 1
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            max_depth = max(max_depth, self._get_max_nesting_depth(child, depth))
        return max_depth
    
    def _count_external_calls(self, node: ast.FunctionDef) -> int:
        """Count external method calls in a function."""
        external_calls = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                external_calls += 1
        return external_calls
    
    def _find_unused_variables(self, node: ast.FunctionDef) -> List[str]:
        """Find unused variables in a function."""
        used_vars = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                used_vars.add(child.id)
        
        unused = []
        for arg in node.args.args:
            if arg.arg not in used_vars:
                unused.append(arg.arg)
        return unused
    
    def _find_matching_brace(self, code: str, start: int) -> int:
        """Find the matching closing brace for a given opening brace."""
        count = 0
        for i in range(start, len(code)):
            if code[i] == '{':
                count += 1
            elif code[i] == '}':
                count -= 1
                if count == 0:
                    return i
        return -1
    
    def _suggest_complexity_refactoring(self, node: ast.FunctionDef, original_code: str) -> Dict[str, str]:
        """Generate specific refactoring suggestions for complex functions."""
        # Analyze the function's structure and generate specific suggestions
        parts = self._split_function_into_parts(node)
        refactored_code = self._generate_refactored_complex_function(node.name, parts)
        
        return {
            "before": original_code,
            "after": refactored_code,
            "explanation": "Function was split into smaller, focused functions based on its logical parts"
        }
    
    def _suggest_nesting_refactoring(self, node: ast.FunctionDef, original_code: str) -> Dict[str, str]:
        """Generate specific refactoring suggestions for deeply nested code."""
        flattened_code = self._flatten_nested_code(node)
        
        return {
            "before": original_code,
            "after": flattened_code,
            "explanation": "Nested conditions were flattened using early returns and helper functions"
        }
    
    def _suggest_feature_envy_refactoring(self, node: ast.FunctionDef, original_code: str) -> Dict[str, str]:
        """Generate specific refactoring suggestions for feature envy."""
        target_class = self._identify_target_class(node)
        refactored_code = self._generate_refactored_feature_envy(node, target_class)
        
        return {
            "before": original_code,
            "after": refactored_code,
            "explanation": f"Function was moved to {target_class} where it belongs"
        }
    
    def _suggest_duplicate_code_refactoring(self, funcs: List[ast.FunctionDef], original_code: str) -> Dict[str, str]:
        """Generate specific refactoring suggestions for duplicate code."""
        common_code = self._extract_common_code(funcs)
        refactored_code = self._generate_refactored_duplicate_code(funcs, common_code)
        
        return {
            "before": original_code,
            "after": refactored_code,
            "explanation": "Common code was extracted into a shared function"
        }
    
    def _suggest_long_method_refactoring(self, node: ast.FunctionDef, original_code: str) -> Dict[str, str]:
        """Generate specific refactoring suggestions for long methods."""
        parts = self._split_function_into_parts(node)
        refactored_code = self._generate_refactored_long_method(node.name, parts)
        
        return {
            "before": original_code,
            "after": refactored_code,
            "explanation": "Long method was split into smaller, focused methods"
        }
    
    def _suggest_magic_number_refactoring(self, node: ast.Num) -> Dict[str, str]:
        """Generate specific refactoring suggestions for magic numbers."""
        return {
            "before": str(node.n),
            "after": f"CONSTANT_{abs(node.n)}",
            "explanation": f"Magic number {node.n} was replaced with a named constant"
        }
    
    def _suggest_unused_variables_refactoring(self, node: ast.FunctionDef, unused_vars: List[str]) -> Dict[str, str]:
        """Generate specific refactoring suggestions for unused variables."""
        original_code = astor.to_source(node)
        refactored_code = self._remove_unused_variables(node, unused_vars)
        
        return {
            "before": original_code,
            "after": refactored_code,
            "explanation": f"Unused variables {', '.join(unused_vars)} were removed"
        }
    
    def _suggest_js_nesting_refactoring(self, nested_code: str) -> Dict[str, str]:
        """Generate specific refactoring suggestions for JavaScript nested callbacks."""
        refactored_code = self._flatten_js_nesting(nested_code)
        
        return {
            "before": nested_code,
            "after": refactored_code,
            "explanation": "Nested callbacks were flattened using async/await"
        }
    
    def _suggest_js_duplicate_code_refactoring(self, block: Tuple[str, ...]) -> Dict[str, str]:
        """Generate specific refactoring suggestions for JavaScript duplicate code."""
        refactored_code = self._extract_js_duplicate_code(block)
        
        return {
            "before": "\n".join(block),
            "after": refactored_code,
            "explanation": "Duplicate code was extracted into a reusable function"
        }
    
    def _suggest_js_magic_number_refactoring(self, numbers: List[str]) -> Dict[str, str]:
        """Generate specific refactoring suggestions for JavaScript magic numbers."""
        constants = "\n".join(f"const NUM_{i} = {num};" for i, num in enumerate(numbers))
        refactored_code = f"// Define constants\n{constants}\n\n// Use constants instead of magic numbers"
        
        return {
            "before": ", ".join(numbers),
            "after": refactored_code,
            "explanation": "Magic numbers were replaced with named constants"
        }
    
    def _suggest_js_unused_variables_refactoring(self, unused_vars: List[str]) -> Dict[str, str]:
        """Generate specific refactoring suggestions for JavaScript unused variables."""
        return {
            "before": f"let {', '.join(unused_vars)};",
            "after": "// Removed unused variables",
            "explanation": f"Unused variables {', '.join(unused_vars)} were removed"
        }
    
    def _suggest_global_variables_refactoring(self, global_vars: List[str]) -> Dict[str, str]:
        """Generate specific refactoring suggestions for JavaScript global variables."""
        module_code = "const module = (function() {\n"
        for var in global_vars:
            module_code += f"    let {var};\n"
        module_code += "    return {\n"
        module_code += "        // Expose necessary variables/functions here\n"
        module_code += "    };\n"
        module_code += "})();"
        
        return {
            "before": "\n".join(f"let {var};" for var in global_vars),
            "after": module_code,
            "explanation": "Global variables were encapsulated in a module"
        }
    
    def _suggest_callback_hell_refactoring(self, callbacks: List[str]) -> Dict[str, str]:
        """Generate specific refactoring suggestions for JavaScript callback hell."""
        refactored_code = """async function processData() {
    try {
        // Use async/await to flatten the callback structure
        const result1 = await step1();
        const result2 = await step2(result1);
        return await step3(result2);
    } catch (error) {
        console.error('Error:', error);
    }
}"""
        
        return {
            "before": "\n".join(callbacks),
            "after": refactored_code,
            "explanation": "Callback hell was refactored using async/await"
        }
    
    def _split_function_into_parts(self, node: ast.FunctionDef) -> List[Tuple[str, List[ast.AST]]]:
        """Split a function into logical parts for refactoring."""
        # Implementation depends on the specific function structure
        # This is a simplified version
        parts = []
        current_part = []
        
        for stmt in node.body:
            if isinstance(stmt, (ast.If, ast.For, ast.While)):
                if current_part:
                    parts.append(("part", current_part))
                    current_part = []
                parts.append(("control", [stmt]))
            else:
                current_part.append(stmt)
        
        if current_part:
            parts.append(("part", current_part))
        
        return parts
    
    def _generate_refactored_complex_function(self, func_name: str, parts: List[Tuple[str, List[ast.AST]]]) -> str:
        """Generate refactored code for a complex function."""
        refactored = []
        helper_funcs = []
        
        for i, (part_type, stmts) in enumerate(parts):
            if part_type == "part":
                helper_name = f"{func_name}_part_{i+1}"
                helper_code = astor.to_source(ast.FunctionDef(
                    name=helper_name,
                    args=ast.arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                    body=stmts,
                    decorator_list=[]
                ))
                helper_funcs.append(helper_code)
                refactored.append(f"    result_{i+1} = {helper_name}()")
            else:
                refactored.append(astor.to_source(stmts[0]))
        
        main_func = f"""def {func_name}():
{chr(10).join('    ' + line for line in refactored)}
    return combine_results({', '.join(f'result_{i+1}' for i in range(len(parts)) if parts[i][0] == 'part')})"""
        
        return "\n\n".join(helper_funcs + [main_func])
    
    def _flatten_nested_code(self, node: ast.FunctionDef) -> str:
        """Flatten nested code using early returns and helper functions."""
        flattened = []
        for stmt in node.body:
            if isinstance(stmt, ast.If):
                condition = astor.to_source(stmt.test).strip()
                flattened.append(f"if not {condition}:")
                flattened.append("    return False")
            else:
                flattened.append(astor.to_source(stmt))
        
        return f"""def {node.name}():
{chr(10).join('    ' + line for line in flattened)}
    return True"""
    
    def _identify_target_class(self, node: ast.FunctionDef) -> str:
        """Identify the target class for feature envy refactoring."""
        # Simplified implementation - in reality, this would analyze the function's
        # interactions with different classes to determine the best target
        return "TargetClass"
    
    def _generate_refactored_feature_envy(self, node: ast.FunctionDef, target_class: str) -> str:
        """Generate refactored code for feature envy."""
        return f"""class {target_class}:
    def {node.name}(self):
        # Move the logic here
        pass"""
    
    def _extract_common_code(self, funcs: List[ast.FunctionDef]) -> str:
        """Extract common code from duplicate functions."""
        # Simplified implementation - in reality, this would analyze the functions
        # to find the common parts
        return "def shared_functionality():\n    # Common code goes here\n    pass"
    
    def _generate_refactored_duplicate_code(self, funcs: List[ast.FunctionDef], common_code: str) -> str:
        """Generate refactored code for duplicate functions."""
        refactored = [common_code]
        for func in funcs:
            refactored.append(f"""def {func.name}():
    shared_functionality()
    # Additional specific code""")
        return "\n\n".join(refactored)
    
    def _generate_refactored_long_method(self, func_name: str, parts: List[Tuple[str, List[ast.AST]]]) -> str:
        """Generate refactored code for a long method."""
        return self._generate_refactored_complex_function(func_name, parts)
    
    def _remove_unused_variables(self, node: ast.FunctionDef, unused_vars: List[str]) -> str:
        """Remove unused variables from a function."""
        # Create a new function definition without the unused variables
        new_args = [arg for arg in node.args.args if arg.arg not in unused_vars]
        new_node = ast.FunctionDef(
            name=node.name,
            args=ast.arguments(
                args=new_args,
                vararg=node.args.vararg,
                kwonlyargs=node.args.kwonlyargs,
                kw_defaults=node.args.kw_defaults,
                kwarg=node.args.kwarg,
                defaults=node.args.defaults
            ),
            body=node.body,
            decorator_list=node.decorator_list
        )
        return astor.to_source(new_node)
    
    def _flatten_js_nesting(self, nested_code: str) -> str:
        """Flatten JavaScript nested callbacks."""
        return """async function processData() {
    try {
        // Use async/await to flatten the callback structure
        const result1 = await step1();
        const result2 = await step2(result1);
        return await step3(result2);
    } catch (error) {
        console.error('Error:', error);
    }
}"""
    
    def _extract_js_duplicate_code(self, block: Tuple[str, ...]) -> str:
        """Extract duplicate JavaScript code into a reusable function."""
        return f"""function reusableFunction(params) {{
    {chr(10).join('    ' + line for line in block)}
}}

// Call the function where needed""" 