import re
from collections import defaultdict

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
        if re.findall(rf'\b{re.escape(var)}\b', code) == [var]:
            global_variables.append(var)
    if global_variables:
        smells.append(f"Global Variables Found: {len(global_variables)} variables")

    # --- Long Function & Too Many Parameters ---
    function_defs = re.finditer(r'function\s+\w*\s*\((.*?)\)\s*\{', code, re.DOTALL)
    for match in function_defs:
        start = match.start()
        params = match.group(1).split(',')
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
    console_logs = re.findall(r'\bconsole\.log\b', code)
    if len(console_logs) >= 10:
        smells.append(f"Console Log Overuse (≥10 logs): {len(console_logs)} logs")

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
    long_chains = re.findall(r'\w+(?:\.\w+){3,}', code)
    if long_chains:
        smells.append(f"Long Chained Calls Found: {len(long_chains)} chains")

    # --- Inconsistent Naming ---
    snake_case = set(re.findall(r'\b[a-z]+(?:_[a-z]+)+\b', code))
    camel_case = set(re.findall(r'\b[a-z]+(?:[A-Z][a-zA-Z0-9]*)+\b', code))
    if snake_case and camel_case:
        smells.append(f"Inconsistent Naming Found: Mixed camelCase and snake_case ({len(snake_case)} snake, {len(camel_case)} camel)")

    # --- Callback Hell (4+ nested function definitions) ---
    nested_callback_depth = 0
    max_callback_depth = 0
    for line in lines:
        if re.search(r'function\s*\(', line) and '=>' not in line:
            nested_callback_depth += 1
            max_callback_depth = max(max_callback_depth, nested_callback_depth)
        if '}' in line:
            nested_callback_depth = max(0, nested_callback_depth - 1)
    if max_callback_depth >= 4:
        smells.append(f"Callback Hell Detected: {max_callback_depth} nested functions")

    # --- Low Comment Density ---
    comments = [line for line in lines if line.strip().startswith('//') or '/*' in line or '*/' in line]
    comment_ratio = len(comments) / num_lines if num_lines else 0
    if comment_ratio < 0.02:
        smells.append(f"Low Comment Density (<2%): {len(comments)} comments")

    # --- Empty Catch Blocks ---
    empty_catches = re.findall(r'catch\s*\(.*?\)\s*\{\s*\}', code, re.DOTALL)
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

# if __name__ == "__main__":
#     smells, metrics = analyze_js_code("sample.js")
#     print("Detected Smells:")
#     for smell in smells:
#         print("-", smell)
#     print("\nCode Metrics:")
#     for key, value in metrics.items():
#         print(f"{key}: {value}")