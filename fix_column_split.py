#!/usr/bin/env python3
"""Fix the _split_li_list_to_columns call to preserve v7.0 format"""

with open('gpt_analyze.py', 'r') as f:
    lines = f.readlines()

# Find the line with _split_li_list_to_columns
for i, line in enumerate(lines):
    if 'left, right = _split_li_list_to_columns(qw_html)' in line:
        # Found it! Insert detection before this line
        indent = '    '
        
        # Create the new code
        new_code = [
            f'{indent}# v7.0: Detect structured format and skip column split\n',
            f'{indent}if \'<div class="quick-win">\' in qw_html:\n',
            f'{indent}    # v7.0: Use full HTML without column split\n',
            f'{indent}    left = qw_html\n',
            f'{indent}    right = ""\n',
            f'{indent}else:\n',
            f'{indent}    # v6.0: Use column split for bullet lists\n',
            f'{indent}    left, right = _split_li_list_to_columns(qw_html)\n',
        ]
        
        # Replace the original line
        lines[i] = ''.join(new_code)
        
        print(f"✅ Fixed line {i+1}")
        break

# Write back
with open('gpt_analyze.py', 'w') as f:
    f.writelines(lines)

print("✅ Column split fix applied!")
