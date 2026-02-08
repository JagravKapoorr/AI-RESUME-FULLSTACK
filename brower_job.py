"""
Run this script to check your browse_jobs.html template for errors
Place this in your Django project root and run: python check_template.py
"""

import re
import sys

def check_template(filepath):
    """Check Django template for common syntax errors"""
    
    print("Checking: " + filepath + "\n")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("ERROR: File not found: " + filepath)
        return
    
    errors = []
    warnings = []
    
    # Track open tags
    for_stack = []
    if_stack = []
    
    for i, line in enumerate(lines, 1):
        line_num = i
        
        # Check for {% for %}
        for_matches = re.findall(r'{%\s*for\s+.*?%}', line)
        for match in for_matches:
            for_stack.append((line_num, match))
        
        # Check for {% endfor %}
        if '{% endfor %}' in line:
            if for_stack:
                for_stack.pop()
            else:
                errors.append("Line " + str(line_num) + ": {% endfor %} without matching {% for %}")
        
        # Check for {% if %}
        if_matches = re.findall(r'{%\s*if\s+.*?%}', line)
        for match in if_matches:
            if_stack.append((line_num, match))
        
        # Check for {% elif %}
        elif_matches = re.findall(r'{%\s*elif\s+.*?%}', line)
        for match in elif_matches:
            if not if_stack:
                errors.append("Line " + str(line_num) + ": {% elif %} without matching {% if %}")
        
        # Check for {% endif %}
        if '{% endif %}' in line:
            if if_stack:
                if_stack.pop()
            elif for_stack:
                for for_line, for_tag in for_stack[-1:]:
                    errors.append("Line " + str(line_num) + ": Found {% endif %} but expecting {% endfor %} for loop started at line " + str(for_line))
            else:
                errors.append("Line " + str(line_num) + ": {% endif %} without matching {% if %}")
        
        # Check for multi-line {% if %}
        if '{%' in line and 'if' in line and '%}' not in line:
            warnings.append("Line " + str(line_num) + ": Possible multi-line template tag ({% if %} should be on one line)")
        
        # Check for inline {% if %} spanning lines
        if line.strip().startswith('{% if') and not line.strip().endswith('%}'):
            errors.append("Line " + str(line_num) + ": {% if %} tag not closed on same line")
    
    # Check for unclosed tags
    if for_stack:
        for line_num, tag in for_stack:
            errors.append("Line " + str(line_num) + ": Unclosed {% for %} loop: " + tag)
    
    if if_stack:
        for line_num, tag in if_stack:
            errors.append("Line " + str(line_num) + ": Unclosed {% if %} block: " + tag)
    
    # Print results
    print("=" * 70)
    if errors:
        print("\nERROR: FOUND " + str(len(errors)) + " ERROR(S):\n")
        for error in errors:
            print("  - " + error)
    else:
        print("\nSUCCESS: No syntax errors found!")
    
    if warnings:
        print("\nWARNING: FOUND " + str(len(warnings)) + " WARNING(S):\n")
        for warning in warnings:
            print("  - " + warning)
    
    print("\n" + "=" * 70)
    
    # Show problem areas
    if errors:
        print("\nPROBLEM AREAS:")
        problem_lines = set()
        for error in errors:
            match = re.search(r'Line (\d+):', error)
            if match:
                problem_lines.add(int(match.group(1)))
        
        for line_num in sorted(problem_lines):
            start = max(1, line_num - 2)
            end = min(len(lines), line_num + 3)
            print("\nAround line " + str(line_num) + ":")
            for i in range(start - 1, end):
                marker = ">>> " if i + 1 == line_num else "    "
                print(marker + str(i + 1).rjust(4) + ": " + lines[i].rstrip())

if __name__ == "__main__":
    # Update this path to your template location
    template_path = r"C:\Users\HP\Desktop\AI-Powered Resume Screening\Resume_Analyzer\resumes\templates\browse_jobs.html"
    
    check_template(template_path)