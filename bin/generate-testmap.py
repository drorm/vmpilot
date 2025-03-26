#!/usr/bin/env python3
"""
Testmap Generator Script for VMPilot

This script generates a component map for testing a specified Python module.
It can be used directly or called from the Makefile.

Usage:
    python generate-testmap.py <source_file> <template_file> <output_file>
    
Example:
    python generate-testmap.py src/vmpilot/agent.py \
           src/vmpilot/plugins/coverage/test_template.md \
           .vmpilot/testmap/agent.md
"""

import os
import sys
import argparse
import subprocess
import re
from pathlib import Path


def get_coverage_for_file(file_path):
    """Get coverage information for a specific file."""
    try:
        # Extract the relative path if it's within the project
        if os.path.isabs(file_path):
            project_root = os.getcwd()
            if file_path.startswith(project_root):
                rel_path = os.path.relpath(file_path, project_root)
            else:
                rel_path = os.path.basename(file_path)
        else:
            rel_path = file_path
            
        # Convert to module path format for coverage
        module_path = str(rel_path).replace('/', '.').replace('.py', '')
        
        # Run pytest with coverage for this specific file
        cmd = [
            "python", "-m", "pytest", 
            f"--cov={os.path.dirname(rel_path)}", 
            "--cov-report=term-missing", 
            "tests/unit/"
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
        
        # Very basic import analysis - in a real implementation this would be more sophisticated
        import_lines = []
        for line in content.split('\n'):
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append(line.strip())
        
        return import_lines
    except Exception as e:
        print(f"Error analyzing imports: {e}", file=sys.stderr)
        return []


def generate_testmap(source_file, template_file, output_file):
    """Generate a testmap based on the template and source file analysis."""
    try:
        # Read template
        with open(template_file, 'r') as f:
            template = f.read()
        
        # Get file information
        file_path = Path(source_file)
        try:
            rel_path = file_path.relative_to(Path.cwd())
        except ValueError:
            # If we can't get a relative path, use the absolute path
            rel_path = file_path
        
        # Get coverage information
        coverage_info = get_coverage_for_file(str(rel_path))
        
        # Analyze imports
        imports = analyze_imports(source_file)
        
        # Replace template placeholders
        content = template.replace('<relative/path/from/project/root>', str(rel_path))
        
        # Add basic file summary
        with open(source_file, 'r') as f:
            file_content = f.read()
            # Extract docstring if available
            docstring_match = re.search(r'"""(.*?)"""', file_content, re.DOTALL)
            summary = "No description available"
            if docstring_match:
                summary = docstring_match.group(1).strip()
        
        # Replace the Summary section
        content = re.sub(r'## Summary\n.*?\n\n', f'## Summary\n{summary}\n\n', content, flags=re.DOTALL)
        
        # Add imports information
        imports_text = "- **Imports**:\n"
        for imp in imports[:10]:  # Limit to 10 imports for brevity
            imports_text += f"  - `{imp}`\n"
        if len(imports) > 10:
            imports_text += f"  - ... and {len(imports) - 10} more\n"
        
        content = re.sub(r'- \*\*Imports\*\*:.*?\n', imports_text, content, flags=re.DOTALL)
        
        # Add coverage information
        coverage_text = f"- Current coverage: {coverage_info['coverage']}%\n"
        coverage_text += f"- Total statements: {coverage_info['statements']}, Missed: {coverage_info['missed']}\n"
        coverage_text += f"- Missing coverage in lines: {coverage_info['missing_lines']}\n"
        
        content = re.sub(r'- Current coverage:.*?\n', coverage_text, content, flags=re.DOTALL)
        
        # Write to output file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"Generated testmap: {output_file}")
        return True
    except Exception as e:
        print(f"Error generating testmap: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate a testmap for a Python module")
    parser.add_argument("source_file", help="Path to the source file")
    parser.add_argument("template_file", help="Path to the template file")
    parser.add_argument("output_file", help="Path where the testmap should be saved")
    
    args = parser.parse_args()
    
    success = generate_testmap(args.source_file, args.template_file, args.output_file)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
