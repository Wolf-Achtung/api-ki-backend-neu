#!/usr/bin/env python3
"""Quick fix script to add quick_wins to complex_html_sections"""

import re

# Read the file
with open('services/html_sanitizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the pattern to find
pattern = r"(    'tool_comparison', 'benchmark_table',\n)(    \})"

# Define the replacement
replacement = r"\1    # v7.0: Quick Wins needs h3/h4 for structured boxes\n    'quick_wins', 'quick_wins_html', 'quick_wins_html_left', 'quick_wins_html_right',\n\2"

# Check if already fixed
if "'quick_wins'" in content:
    print("✅ Already fixed! quick_wins found in file.")
else:
    # Apply the fix
    new_content = re.sub(pattern, replacement, content)
    
    # Verify the change was made
    if new_content != content:
        # Write back
        with open('services/html_sanitizer.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Fix applied successfully!")
        print("\n📝 Changes made:")
        print("   Added quick_wins to complex_html_sections")
    else:
        print("❌ Pattern not found. Manual fix required.")

