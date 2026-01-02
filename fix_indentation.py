#!/usr/bin/env python3
"""Fix the indentation error in html_sanitizer.py"""

with open('services/html_sanitizer.py', 'r') as f:
    lines = f.readlines()

# Find the line with the error and the context around it
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Look for the problematic section (around line 987)
    if 'complex_html_sections = {' in line and i > 980 and i < 1000:
        # Check if this is inside a function (should be indented)
        # Find the function definition above
        found_function = False
        for j in range(i-1, max(0, i-50), -1):
            if lines[j].strip().startswith('def ') and 'is_text_section' in lines[j]:
                found_function = True
                break
        
        if found_function:
            # This should be indented (inside function)
            # Make sure it has 4 spaces
            if not line.startswith('    '):
                line = '    ' + line.lstrip()
                print(f"Fixed indentation at line {i+1}")
        
    fixed_lines.append(line)
    i += 1

# Write back
with open('services/html_sanitizer.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Indentation fixed!")
