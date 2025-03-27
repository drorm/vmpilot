#!/usr/bin/env python3
"""
File Analysis Script for VMPilot Coverage Plugin

This script analyzes a Python file to extract useful information for test component maps:
- Coverage statistics
- Imports
- Docstrings
- Function definitions

Usage:
    python analyze_file.py <source_file>
    
Example:
    python analyze_file.py src/vmpilot/agent.py
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path


def get_coverage_for_file(file_path):
    """Get coverage information for a specific file."""
    try:
        # Extract the relative path if it's within the project
        project_root = "/home/dror/vmpilot"
        
        if os.path.isabs(file_path):
            if file_path.startswith(project_root):
                rel_path = os.path.relpath(file_path, project_root)
            else:
                rel_path = os.path.basename(file_path)
        else:
            # If not absolute, assume it's relative to the project root
            rel_path = file_path
            
        # Get the absolute path to the tests directory
        tests_dir = os.path.join(project_root, "tests/unit/")
            
        # Run pytest with coverage for this specific file
        cmd = [
            "python", "-m", "pytest", 
            f"--cov={os.path.dirname(os.path.join(project_root, rel_path))}", 
            "--cov-report=term-missing", 
            tests_dir
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Extract coverage information for this file
        coverage_pattern = rf"{re.escape(rel_path)}\s+(\d+)\s+(\d+)\s+(\d+)%\s+(.*)"
        match = re.search(coverage_pattern, result.stdout)
        
        if match:
            statements = match.group(1)
            missed = match.group(2)
            coverage = match.group(3)
            missing_lines = match.group(4)
            return {
                'statements': statements,
                'missed': missed,
                'coverage': coverage,
                'missing_lines': missing_lines
            }
        
        # If no match, try with just the filename
        filename = os.path.basename(file_path)
        coverage_pattern = rf"{re.escape(filename)}\s+(\d+)\s+(\d+)\s+(\d+)%\s+(.*)"
        match = re.search(coverage_pattern, result.stdout)
        
        if match:
            statements = match.group(1)
            missed = match.group(2)
            coverage = match.group(3)
            missing_lines = match.group(4)
            return {
                'statements': statements,
                'missed': missed,
                'coverage': coverage,
                'missing_lines': missing_lines
            }
            
        return {
            'statements': 'N/A',
            'missed': 'N/A',
            'coverage': '0',
            'missing_lines': 'N/A'
        }
    except Exception as e:
        print(f"Error getting coverage: {e}", file=sys.stderr)
        return {
            'statements': 'N/A',
            'missed': 'N/A',
            'coverage': '0',
            'missing_lines': 'Error running coverage'
        }


def analyze_imports(file_path):
    """Analyze imports in the file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract import statements
        import_lines = []
        for line in content.split('\n'):
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append(line.strip())
        
        return import_lines
    except Exception as e:
        print(f"Error analyzing imports: {e}", file=sys.stderr)
        return []


def extract_docstring(file_path):
    """Extract the module docstring from the file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract module docstring
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()
        return "No description available"
    except Exception as e:
        print(f"Error extracting docstring: {e}", file=sys.stderr)
        return "Error extracting docstring"


def extract_functions(file_path):
    """Extract function definitions from the file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract function definitions
        function_pattern = r'def\s+(\w+)\s*\(([^)]*)\):'
        functions = []
        
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            func_params = match.group(2).strip()
            
            # Get the line number of the function definition
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if the function is a method (indented)
            line_start = content[:match.start()].rfind('\n') + 1
            indentation = match.start() - line_start
            
            functions.append({
                'name': func_name,
                'params': func_params,
                'line': line_num,
                'is_method': indentation > 0
            })
        
        return functions
    except Exception as e:
        print(f"Error extracting functions: {e}", file=sys.stderr)
        return []


def analyze_file(file_path):
    """Analyze a file and return useful information for test component maps."""
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)
        if not os.path.isfile(abs_path):
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return {}
        
        # Get relative path from project root
        project_root = "/home/dror/vmpilot"
        try:
            rel_path = Path(abs_path).relative_to(Path(project_root))
        except ValueError:
            rel_path = Path(abs_path)
        
        # Gather all the information
        coverage_info = get_coverage_for_file(str(rel_path))
        imports = analyze_imports(abs_path)
        docstring = extract_docstring(abs_path)
        functions = extract_functions(abs_path)
        
        # Compile the analysis results
        result = {
            'file_path': str(rel_path),
            'abs_path': abs_path,
            'docstring': docstring,
            'coverage': coverage_info,
            'imports': imports,
            'functions': functions
        }
        
        return result
    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        return {
            'error': str(e)
        }


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_file.py <source_file>", file=sys.stderr)
        return 1
    
    file_path = sys.argv[1]
    analysis = analyze_file(file_path)
    
    # Print the analysis as JSON
    print(json.dumps(analysis, indent=2))
    
    # Provide guidance for next steps
    rel_path = analysis.get('file_path', os.path.basename(file_path))
    testmap_path = rel_path.replace('.py', '.md')
    testmap_path = os.path.join('/home/dror/vmpilot/.vmpilot/testmap', testmap_path)
    
    print("\n--- Next Steps ---", file=sys.stderr)
    print(f"File analysis complete for {rel_path}", file=sys.stderr)
    print(f"Test map template created at: {testmap_path}", file=sys.stderr)
    print("Please edit the test map file with detailed information using the analysis data above.", file=sys.stderr)
    print("Refer to the test_template.md file for the recommended structure.", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
