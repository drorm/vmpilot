#!/usr/bin/env python3
"""
Code Search CLI Tool - Searches code using Gemini API based on natural language queries.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
import openai

from codesearch.build_execute import build_search_prompt, execute_search
from codesearch.utils import (
    collect_files,
    estimate_token_count,
    format_output,
    load_config,
    truncate_files_to_token_limit,
)

# Set up logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


import time


def search_project_code(
    query: str,
    project_root: Optional[str] = None,
    config_path: Optional[str] = None,
    output_format: str = "markdown",
    model: Optional[str] = None,
) -> str:
    """
    Search code in a project using natural language queries.

    This function is designed to be imported and used programmatically,
    providing the same functionality as the CLI but as a Python function.

    Args:
        query: The natural language query to search for
        project_root: Root directory of the project to search (defaults to config base_dir or current directory)
        config_path: Path to the search configuration file (defaults to searchconfig.yaml in module directory)
        output_format: Output format - "markdown", "json", or "text"
        model: LLM model to use (overrides config setting)

    Returns:
        Formatted search results as a string
    """
    start_time = time.time()
    try:
        # Set default config path if not provided
        if config_path is None:
            # Look for config in current directory first
            if os.path.exists("searchconfig.yaml"):
                config_path = "searchconfig.yaml"
            else:
                # Fall back to the config in the script's directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(script_dir, "searchconfig.yaml")

        # Load configuration
        config = load_config(config_path)

        # Use project_root from arguments if provided, otherwise use base_dir from config
        if project_root is None:
            project_root = config.get("general", {}).get("base_dir", os.getcwd())

        # Ensure path is expanded and absolute
        project_root = os.path.abspath(os.path.expanduser(project_root))

        # Override model if specified
        if model:
            if "api" not in config:
                config["api"] = {}
            config["api"]["model"] = model

        # Setup API
        setup_api(config)

        # Get files and build prompt
        file_patterns = config.get("file_patterns", {})
        include_patterns = file_patterns.get("include", ["*.py"])
        exclude_patterns = file_patterns.get(
            "exclude", ["**/node_modules/**", "**/.git/**"]
        )
        limits = config.get("limits", {})
        max_file_size_kb = limits.get("max_file_size_kb", 500)
        max_files = limits.get("max_files_to_include", 50)

        # Collect files
        files = collect_files(
            project_root=project_root,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_file_size_kb=max_file_size_kb,
            max_files=max_files,
        )

        # Truncate files to fit token limit
        max_total_tokens = limits.get("max_total_tokens", 8000)
        files = truncate_files_to_token_limit(files, max_total_tokens)

        # Build prompt and execute search
        prompt = build_search_prompt(files, query, config)
        result = execute_search(prompt, config, files=files)

        # Add query and files searched to result
        result["query"] = query
        result["files_searched"] = [f[0] for f in files]

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Add elapsed time to result
        result["elapsed_time"] = elapsed_time

        # Format the output
        return format_output(result, output_format)

    except Exception as e:
        logger.error(f"Error in search_project_code: {str(e)}")
        elapsed_time = time.time() - start_time
        return (
            f"Error searching code: {str(e)} (elapsed time: {elapsed_time:.2f} seconds)"
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
    provider = api_config.get("provider", "openai")

    if provider == "gemini":
        # Check for API key in environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
    elif provider == "openai":
        # Check for API key in environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        openai.api_key = api_key
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
    project_root: Optional[str],
    config: Dict[str, Any],
    output_format: str,
    verbose: bool = False,
) -> str:
    """
    Search code using the provided query and configuration.

    Args:
        query: The search query
        project_root: Root directory of the project (optional, overrides config)
        config: Configuration dictionary
        output_format: Output format (json, text, markdown)
        verbose: Whether to print verbose information

    Returns:
        Formatted search results
    """
    start_time = time.time()
    # Use project_root from arguments if provided, otherwise use base_dir from config
    if not project_root:
        project_root = config.get("general", {}).get("base_dir", ".")

    # Ensure path is expanded and absolute
    project_root = os.path.abspath(os.path.expanduser(project_root))

    if verbose:
        logger.info(f"Using project root: {project_root}")

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
        logger.info(f"Collecting files from {project_root}...")

    files = collect_files(
        project_root=project_root,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        max_file_size_kb=max_file_size_kb,
        max_files=max_files,
    )

    if verbose:
        logger.info(f"Found {len(files)} files matching patterns.")

    # Calculate total tokens before truncation
    total_tokens_before = sum(estimate_token_count(content) for _, content in files)

    # Truncate files to fit token limit
    files = truncate_files_to_token_limit(files, max_total_tokens)

    # Calculate total tokens after truncation
    total_tokens_after = sum(estimate_token_count(content) for _, content in files)

    if verbose:
        logger.info(f"Total tokens before truncation: {total_tokens_before}")
        logger.info(f"Total tokens after truncation: {total_tokens_after}")
        logger.info(f"Files included in search: {len(files)}")
        if len(files) > 0:
            logger.info("\nFiles included in search:")
            for filepath, _ in files:
                logger.info(f"- {filepath}")
        logger.info("")

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

    # Call API
    try:
        if api_config.get("provider", "openai") == "gemini":
            if verbose:
                logger.info(f"Sending query to Gemini API...")
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-001",
                # model_name="gemini-1.5-flash-8b",
                generation_config={
                    "temperature": temperature,
                    "top_p": top_p,
                },
            )

            response = model.generate_content(prompt)
            response_text = response.text

        elif api_config.get("provider", "openai") == "openai":
            if verbose:
                logger.info(f"Sending query to OpenAI API...")
            response = openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p,
            )
            response_text = response.choices[0].message.content

        if verbose:
            logger.info(f"Response received from API.")

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Format results
        results = {
            "query": query,
            "response": response_text,
            "files_searched": [f[0] for f in files],
            "elapsed_time": elapsed_time,
        }

        return format_output(results, output_format)

    except Exception as e:
        error_msg = str(e)
        if verbose:
            logger.info(f"Error from API: {error_msg}")

        # Calculate elapsed time even for errors
        elapsed_time = time.time() - start_time

        results = {
            "query": query,
            "error": error_msg,
            "files_searched": [f[0] for f in files],
            "elapsed_time": elapsed_time,
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
        default=None,
        help="Root directory of the project to search",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--output-format",
        "-o",
        type=str,
        default="markdown",
        choices=["json", "text", "markdown"],
        help="Output format (json, text, markdown)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with file list and token counts",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="LLM model to use (overrides config setting)",
    )

    args = parser.parse_args()

    try:
        # Set up logging level
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug("Verbose mode enabled")

        # Set environment variable for testing if needed (remove in production)
        if "GEMINI_API_KEY" not in os.environ and "OPENAI_API_KEY" not in os.environ:
            logger.warning(
                "No API key found. Using dummy key for demonstration purposes."
            )
            os.environ["GEMINI_API_KEY"] = "dummy_key_for_testing"

        # Use the search_project_code function
        result = search_project_code(
            query=args.query,
            project_root=args.project_root,
            config_path=args.config,
            output_format=args.output_format,
            model=args.model,
        )

        # Print result
        print(result)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
