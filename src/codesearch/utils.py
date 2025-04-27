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
        if any(fnmatch.fnmatch(filepath, p) for p in _expand_pattern(pattern)):
            return False

    # Then check if file should be included
    for pattern in include_patterns:
        if any(fnmatch.fnmatch(filepath, p) for p in _expand_pattern(pattern)):
            return True

    # If no include pattern matches, exclude the file
    return False


def _expand_pattern(pattern: str) -> List[str]:
    """
    Expand a glob pattern to handle ** patterns correctly.

    Args:
        pattern: Glob pattern

    Returns:
        List of expanded patterns
    """
    # Handle basic file extension patterns
    if pattern.startswith("*."):
        return [pattern, f"**/{pattern}"]
    return [pattern]


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

    # Debug information
    print(f"DEBUG: Project root: {project_root}", file=os.sys.stderr)
    print(f"DEBUG: Include patterns: {include_patterns}", file=os.sys.stderr)
    print(f"DEBUG: Exclude patterns: {exclude_patterns}", file=os.sys.stderr)

    # Track skipped files for debugging
    skipped_by_pattern = 0
    skipped_by_size = 0
    skipped_by_error = 0

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
                skipped_by_pattern += 1
                continue

            # Skip files that are too large
            try:
                file_size = os.path.getsize(filepath)
                if file_size > max_size_bytes:
                    skipped_by_size += 1
                    continue

                # Read file content
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                collected_files.append((relpath, content))
            except Exception as e:
                skipped_by_error += 1
                # Skip files that can't be read
                continue

    # Debug information
    print(f"DEBUG: Files collected: {len(collected_files)}", file=os.sys.stderr)
    print(f"DEBUG: Files skipped by pattern: {skipped_by_pattern}", file=os.sys.stderr)
    print(f"DEBUG: Files skipped by size: {skipped_by_size}", file=os.sys.stderr)
    print(f"DEBUG: Files skipped by error: {skipped_by_error}", file=os.sys.stderr)

    return collected_files


def estimate_token_count(text: str) -> int:
    """
    Estimate the number of tokens in a text.
    This is a more accurate estimation - approximately 4 characters per token
    but also accounting for whitespace and newlines.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    # Count words (better approximation than characters)
    words = len(text.split())
    # Add extra tokens for newlines and special characters
    extra_tokens = text.count("\n") + sum(
        1 for c in text if not c.isalnum() and not c.isspace()
    )
    # Estimate total - roughly 1 token per word plus extra tokens
    return words + (extra_tokens // 4)


def truncate_files_to_token_limit(
    files: List[Tuple[str, str]], max_tokens: int
) -> List[Tuple[str, str]]:
    """
    Truncate the list of files to fit within a token limit.
    This implementation prioritizes including more files by taking
    files in order of estimated token count (smallest first).

    Args:
        files: List of (file_path, content) tuples
        max_tokens: Maximum number of tokens

    Returns:
        Truncated list of files
    """
    # Sort files by token count (smallest first)
    files_with_tokens = [
        (filepath, content, estimate_token_count(content))
        for filepath, content in files
    ]
    files_with_tokens.sort(key=lambda x: x[2])

    # Add files until we hit the token limit
    result = []
    current_tokens = 0
    skipped_files = []

    for filepath, content, tokens in files_with_tokens:
        # If adding this file would exceed the limit, skip it
        if current_tokens + tokens > max_tokens:
            skipped_files.append((filepath, tokens))
            continue

        result.append((filepath, content))
        current_tokens += tokens

    # Debug information
    print(
        f"DEBUG: Total tokens used: {current_tokens}/{max_tokens}", file=os.sys.stderr
    )
    print(f"DEBUG: Files included after truncation: {len(result)}", file=os.sys.stderr)
    print(
        f"DEBUG: Files skipped due to token limit: {len(skipped_files)}",
        file=os.sys.stderr,
    )

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
