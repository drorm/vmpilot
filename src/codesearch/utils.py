#!/usr/bin/env python3
"""
Utility functions for code search tool.
"""

import fnmatch
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing configuration
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {str(e)}")


def should_include_file(
    filepath: str, include_patterns: List[str], exclude_patterns: List[str]
) -> bool:
    """
    Determine if a file should be included based on patterns.

    Args:
        filepath: Path to the file
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude

    Returns:
        True if the file should be included, False otherwise
    """
    # First check if file should be excluded
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(filepath, pattern):
            return False

    # Then check if file should be included
    for pattern in include_patterns:
        if fnmatch.fnmatch(filepath, pattern):
            return True

    # If no include pattern matches, exclude the file
    return False


def collect_files(
    project_root: str,
    include_patterns: List[str],
    exclude_patterns: List[str],
    max_file_size_kb: int,
    max_files: int,
) -> List[Tuple[str, str]]:
    """
    Collect files from project that match include/exclude patterns.

    Args:
        project_root: Root directory to start search
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude
        max_file_size_kb: Maximum file size in KB
        max_files: Maximum number of files to include

    Returns:
        List of tuples containing (relative_path, file_content)
    """
    collected_files = []
    max_size_bytes = max_file_size_kb * 1024

    # Convert to absolute path
    project_root = os.path.abspath(project_root)

    for root, _, files in os.walk(project_root):
        if len(collected_files) >= max_files:
            break

        for file in files:
            if len(collected_files) >= max_files:
                break

            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, project_root)

            # Skip files that don't match patterns
            if not should_include_file(relpath, include_patterns, exclude_patterns):
                continue

            # Skip files that are too large
            try:
                file_size = os.path.getsize(filepath)
                if file_size > max_size_bytes:
                    continue

                # Read file content
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                collected_files.append((relpath, content))
            except Exception:
                # Skip files that can't be read
                continue

    return collected_files


def estimate_token_count(text: str) -> int:
    """
    Estimate the number of tokens in a text.
    This is a simple estimation - approximately 4 characters per token.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


def truncate_files_to_token_limit(
    files: List[Tuple[str, str]], max_tokens: int
) -> List[Tuple[str, str]]:
    """
    Truncate the list of files to fit within a token limit.

    Args:
        files: List of (file_path, content) tuples
        max_tokens: Maximum number of tokens

    Returns:
        Truncated list of files
    """
    result = []
    current_tokens = 0

    for filepath, content in files:
        # Estimate tokens for this file
        file_tokens = estimate_token_count(content)

        # If adding this file would exceed the limit, stop
        if current_tokens + file_tokens > max_tokens:
            break

        result.append((filepath, content))
        current_tokens += file_tokens

    return result


def format_output(results: Dict[str, Any], format_type: str) -> str:
    """
    Format search results according to specified format.

    Args:
        results: Dictionary of search results
        format_type: Format type (json, text, markdown)

    Returns:
        Formatted results as string
    """
    if format_type == "json":
        return json.dumps(results, indent=2)
    elif format_type == "text":
        # Simple text format
        output = f"Query: {results.get('query', '')}\n\n"
        output += f"Results:\n{results.get('response', '')}\n\n"
        output += "Files searched:\n"
        for file in results.get("files_searched", []):
            output += f"- {file}\n"
        return output
    elif format_type == "markdown":
        # Markdown format
        output = f"## Code Search Results\n\n"
        output += f"**Query:** {results.get('query', '')}\n\n"
        output += f"### Response\n\n{results.get('response', '')}\n\n"
        output += "### Files Searched\n\n"
        for file in results.get("files_searched", []):
            output += f"- `{file}`\n"
        return output
    else:
        # Default to JSON if format not recognized
        return json.dumps(results, indent=2)
