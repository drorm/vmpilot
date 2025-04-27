#!/usr/bin/env python3
"""
Code Search CLI Tool - Searches code using Gemini API based on natural language queries.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from utils import (
    collect_files,
    estimate_token_count,
    format_output,
    load_config,
    truncate_files_to_token_limit,
)

# Default configuration file path
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "searchconfig.yaml"
)


def setup_api(config: Dict[str, Any]) -> None:
    """
    Setup the API client based on configuration.

    Args:
        config: Configuration dictionary
    """
    api_config = config.get("api", {})
    provider = api_config.get("provider", "gemini")

    if provider == "gemini":
        # Check for API key in environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
    else:
        raise ValueError(f"Unsupported API provider: {provider}")


def construct_prompt(query: str, files: List[tuple[str, str]]) -> str:
    """
    Construct a prompt for the LLM based on the query and files.

    Args:
        query: The search query
        files: List of (file_path, content) tuples

    Returns:
        Constructed prompt
    """
    prompt = f"""
You are a code search assistant that helps developers find relevant information in their codebase.

SEARCH QUERY: {query}

I'll provide you with the content of relevant files from the codebase.
Your task is to analyze these files and provide a comprehensive answer to the search query.

For each relevant section of code, include:
1. The file path
2. The specific code snippet that's relevant
3. An explanation of how it relates to the query

CODEBASE FILES:
"""

    for filepath, content in files:
        prompt += f"\n--- FILE: {filepath} ---\n"
        prompt += content
        prompt += "\n--- END FILE ---\n"

    prompt += """
INSTRUCTIONS:
1. Focus on directly answering the search query with specific code references
2. If the provided files don't contain relevant information, say so clearly
3. If you need additional context or files to provide a complete answer, mention what's missing
4. Format your response in a clear, structured way with code snippets and explanations
5. Prioritize accuracy over comprehensiveness

Now, please provide a comprehensive answer to the search query based on the provided code files.
"""

    return prompt


def search_code(
    query: str,
    project_root: str,
    config: Dict[str, Any],
    output_format: str,
    verbose: bool = False,
) -> str:
    """
    Search code using the provided query and configuration.

    Args:
        query: The search query
        project_root: Root directory of the project
        config: Configuration dictionary
        output_format: Output format (json, text, markdown)
        verbose: Whether to print verbose information

    Returns:
        Formatted search results
    """
    # Extract configuration values
    file_patterns = config.get("file_patterns", {})
    include_patterns = file_patterns.get("include", ["*.py"])
    exclude_patterns = file_patterns.get(
        "exclude", ["**/node_modules/**", "**/.git/**"]
    )

    limits = config.get("limits", {})
    max_file_size_kb = limits.get("max_file_size_kb", 500)
    max_total_tokens = limits.get("max_total_tokens", 8000)
    max_files = limits.get("max_files_to_include", 50)

    api_config = config.get("api", {})
    temperature = api_config.get("temperature", 0.2)
    top_p = api_config.get("top_p", 0.95)

    # Collect files
    if verbose:
        print(f"Collecting files from {project_root}...", file=sys.stderr)

    files = collect_files(
        project_root=project_root,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        max_file_size_kb=max_file_size_kb,
        max_files=max_files,
    )

    if verbose:
        print(f"Found {len(files)} files matching patterns.", file=sys.stderr)

    # Calculate total tokens before truncation
    total_tokens_before = sum(estimate_token_count(content) for _, content in files)

    # Truncate files to fit token limit
    files = truncate_files_to_token_limit(files, max_total_tokens)

    # Calculate total tokens after truncation
    total_tokens_after = sum(estimate_token_count(content) for _, content in files)

    if verbose:
        print(f"Total tokens before truncation: {total_tokens_before}", file=sys.stderr)
        print(f"Total tokens after truncation: {total_tokens_after}", file=sys.stderr)
        print(f"Files included in search: {len(files)}", file=sys.stderr)
        if len(files) > 0:
            print("\nFiles included in search:", file=sys.stderr)
            for filepath, _ in files:
                print(f"- {filepath}", file=sys.stderr)
        print("", file=sys.stderr)

    # If no files found, return early
    if not files:
        results = {
            "query": query,
            "response": "No matching files found in the project.",
            "files_searched": [],
        }
        return format_output(results, output_format)

    # Construct prompt
    prompt = construct_prompt(query, files)

    if verbose:
        print(f"Sending query to Gemini API...", file=sys.stderr)

    # Call API
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-04-17",
            generation_config={
                "temperature": temperature,
                "top_p": top_p,
            },
        )

        response = model.generate_content(prompt)

        if verbose:
            print(f"Response received from API.", file=sys.stderr)

        # Format results
        results = {
            "query": query,
            "response": response.text,
            "files_searched": [f[0] for f in files],
        }

        return format_output(results, output_format)

    except Exception as e:
        error_msg = str(e)
        if verbose:
            print(f"Error from API: {error_msg}", file=sys.stderr)

        results = {
            "query": query,
            "error": error_msg,
            "files_searched": [f[0] for f in files],
        }
        return format_output(results, output_format)


def main():
    """Main entry point for the code search tool."""
    parser = argparse.ArgumentParser(
        description="Search code using natural language queries."
    )
    parser.add_argument("--query", "-q", type=str, required=True, help="Search query")
    parser.add_argument(
        "--project-root",
        "-p",
        type=str,
        default=".",
        help="Root directory of the project",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--output-format",
        "-o",
        type=str,
        default="markdown",  # Changed default to markdown
        choices=["json", "text", "markdown"],
        help="Output format (json, text, markdown)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with file list and token counts",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args.config)

        # Setup API
        setup_api(config)

        # Search code
        result = search_code(
            query=args.query,
            project_root=args.project_root,
            config=config,
            output_format=args.output_format,
            verbose=args.verbose,
        )

        # Print result
        print(result)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
