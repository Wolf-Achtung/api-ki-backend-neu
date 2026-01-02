#!/usr/bin/env python3
"""Final fix for html_sanitizer.py"""

with open('services/html_sanitizer.py', 'r') as f:
    lines = f.readlines()

# Find and fix the section
fixed_lines = []
skip_next_closing_brace = False

for i, line in enumerate(lines):
    # Skip if we're on line 987-ish and it's the complex_html_sections
    if i >= 985 and i <= 995:
        # If this is the complex_html_sections line
        if 'complex_html_sections = {' in line:
            # Ensure it has proper indentation (4 spaces)
            fixed_lines.append('    complex_html_sections = {\n')
            skip_next_closing_brace = False
            continue
        
        # If we just closed the dict, check for duplicate closing brace
        if line.strip() == '}' and i > 986:
            # Check if previous line was also a closing brace
            if fixed_lines and fixed_lines[-1].strip() == '}':
                # Skip this duplicate
                print(f"Skipping duplicate }} at line {i+1}")
                continue
    
    fixed_lines.append(line)

# Write back
with open('services/html_sanitizer.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Final fix applied!")

# Verify syntax
import py_compile
try:
    py_compile.compile('services/html_sanitizer.py', doraise=True)
    print("✅ Syntax is valid!")
except py_compile.PyCompileError as e:
    print(f"❌ Still has errors: {e}")
