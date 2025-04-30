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
def refactor_js_code(code, smells):
    """
    This function accepts the main code and a dictionary of detected smells
    and applies the relevant refactoring functions.
    """
    
    # Refactor Global Variables
    if "Global Variables Found" in smells:
        global_vars = smells["Global Variables Found"]["details"]
        code = refactor_global_variables(code, global_vars)

    # Refactor Magic Numbers
    if "Magic Numbers Found" in smells:
        magic_numbers = smells["Magic Numbers Found"]["details"]
        code = refactor_magic_numbers(code, magic_numbers)

    # Refactor Duplicate Code
    if "Duplicate Code" in smells:
        duplicate_blocks = smells["Duplicate Code"]["details"]
        code = refactor_duplicate_code(code, duplicate_blocks)

    # Refactor Unused Variables
    if "Unused Variables" in smells:
        unused_vars = smells["Unused Variables"]["details"]
        code = refactor_unused_variables(code, unused_vars)

    # Refactor Callback Hell (Deep Nesting)
    if "Deep Nesting" in smells:
        nested_callbacks = smells["Deep Nesting"]["details"]
        code = refactor_callback_hell(code, nested_callbacks)

    # Refactor Dead Code Variables
    if "Dead Code Variables" in smells:
        dead_code_vars = smells["Dead Code Variables"]["details"]
        code = refactor_dead_code_variables(code, dead_code_vars)

    # Refactor Excessive Comments
    code = refactor_excessive_comments(code)

    # Refactor Large Functions
    if "Large Functions" in smells:
        large_functions = smells["Large Functions"]["details"]
        code = refactor_large_functions(code, large_functions)

    return code
