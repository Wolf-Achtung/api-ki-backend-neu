#!/bin/bash

echo "🔧 Auto-resolving merge conflict in html_sanitizer.py..."

# Create the correct version
cat > services/html_sanitizer.py.fixed << 'FIXED'
    complex_html_sections = {
        'ai_act_table', 'ai_act_compliance_table',
        'business_case', 'business_case_visual',
        'financial_summary', 'kpi_table',
        'tool_comparison', 'benchmark_table',
        # v7.0: Quick Wins needs h3/h4 for structured boxes
        'quick_wins', 'quick_wins_html', 'quick_wins_html_left', 'quick_wins_html_right',
    }
FIXED

# Find and replace the conflicted section
python3 << 'PYTHON'
import re

with open('services/html_sanitizer.py', 'r') as f:
    content = f.read()

# Pattern to find the conflict markers
conflict_pattern = r'<<<<<<< HEAD.*?=======.*?>>>>>>> [a-f0-9]+ \(.*?\)'

# Check if conflict exists
if '<<<<<<< HEAD' in content:
    # Remove the conflict and use the version with quick_wins
    # Find the section between <<<<<<< and >>>>>>>
    start = content.find('<<<<<<< HEAD')
    end = content.find('>>>>>>>', start) + len('>>>>>>> ') + 50  # Skip to end of line
    
    # Find the end of that line
    end = content.find('\n', end) + 1
    
    # Extract before and after
    before = content[:start]
    after = content[end:]
    
    # Insert the fixed version
    with open('services/html_sanitizer.py.fixed', 'r') as f:
        fixed = f.read()
    
    # Find where to insert (look for the pattern before conflict)
    insert_point = before.rfind('complex_html_sections = {')
    if insert_point == -1:
        print("❌ Could not find insertion point")
        exit(1)
    
    # Build new content
    new_content = before[:insert_point] + fixed + after
    
    # Write back
    with open('services/html_sanitizer.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Conflict resolved!")
else:
    print("ℹ️  No conflict markers found")
PYTHON

echo "✅ Done!"
