import ast
import astor
import textwrap
from collections import defaultdict
import re

# Refactoring Functions

def refactor_global_variables(code, global_vars):
    for var in global_vars:
        # Refactor global variables by enclosing them inside an object or passing them as parameters
        code = re.sub(rf'\b{var}\b', f'window.{var}', code)  # Access global variable through the `window` object
        code = code.replace(f"var {var}", f"let {var}")  # Use let instead of var
        code = code.replace(f"const {var}", f"let {var}")  # If const, change to let for mutability
    return code

def refactor_magic_numbers(code, magic_numbers):
    # Replace magic numbers with constants for better readability
    constants = {num: f"const {num}_VALUE = {num};" for num in set(magic_numbers)}  # Create constants
    constant_declarations = "\n".join(constants.values())  # Form the declarations block
    code = constant_declarations + "\n\n" + code  # Add constants at the top of the code
    
    for num in set(magic_numbers):
        code = code.replace(str(num), f"{num}_VALUE")  # Replace magic numbers in the code with the defined constants
    return code

def refactor_duplicate_code(code, duplicate_blocks):
    for block in duplicate_blocks:
        block_str = '\n'.join(block)
        function_name = f"refactored_function_{duplicate_blocks.index(block)}"
        function_code = f"function {function_name}() {{\n{block_str}\n}}"
        code = code.replace(block_str, f"{function_name}()")  # Replace duplicated blocks with function calls
    return code

def refactor_unused_variables(code, unused_vars):
    for var in unused_vars:
        # Check if variable is declared but not used and comment it out
        code = re.sub(rf'\b{var}\b', f"// {var} (Unused variable)", code)
    return code

def refactor_callback_hell(code, nested_callbacks):
    for callback in nested_callbacks:
        # Refactor nested callbacks to use async/await or extract them into separate functions
        code = code.replace(callback, callback.replace("function", "async function"))  # Convert callbacks to async functions
        nested_function_name = f"handleNestedCallback{nested_callbacks.index(callback)}"
        code = code.replace(callback, nested_function_name)  # Replace callback with function call
        code = f"async function {nested_function_name}() {{\n{callback}\n}};\n" + code  # Define the new async function
    return code

def refactor_dead_code_variables(code, unused_vars):
    for var in unused_vars:
        code = re.sub(rf'\b{var}\b', f"// {var} (Dead code - unused variable)", code)
    return code

def refactor_excessive_comments(code):
    # Remove excessive comments or unnecessary explanations from the code
    code = re.sub(r'//.*', '', code)  # Remove single-line comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)  # Remove multi-line comments
    return code

def refactor_large_functions(code, functions_to_refactor):
    for fn_name in functions_to_refactor:
        # Add a comment at the top of large functions indicating they need refactoring
        code = re.sub(rf"def {fn_name}\s*\(", f"# TODO: Refactor large function\n\ndef {fn_name}(", code)
    return code

# Base Function to Apply Refactorings

