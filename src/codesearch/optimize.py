#!/usr/bin/env python3
"""
Test script for debugging file pattern matching.
Uses configuration from searchconfig.yaml.
"""

import os
import os.path
import sys

from utils import (
    _expand_pattern,
    estimate_token_count,
    load_config,
    should_include_file,
)


def main():
    # Load configuration from YAML file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "searchconfig.yaml")
    config = load_config(config_path)

    # Get patterns and limits from config
    include_patterns = config["file_patterns"]["include"]
    exclude_patterns = config["file_patterns"]["exclude"]
    max_size_kb = config["limits"]["max_file_size_kb"]

    # Get base directory from config if available, otherwise use current directory
    directory = config.get("general", {}).get("base_dir", ".")
    directory = os.path.expanduser(directory)
    if not os.path.isdir(directory):
        print(
            f"Warning: Base directory '{directory}' not found, using current directory instead."
        )
        directory = "."
    else:
        print(f"Using base directory: {directory}")

    show_excluded = True  # Default to showing excluded files

    # Expand all patterns
    include_expanded = []
    for pattern in include_patterns:
        include_expanded.extend(_expand_pattern(pattern))

    exclude_expanded = []
    for pattern in exclude_patterns:
        exclude_expanded.extend(_expand_pattern(pattern))

    print(f"Expanded include patterns: {include_expanded}")
    print(f"Expanded exclude patterns: {exclude_expanded}")
    print(f"Maximum file size: {max_size_kb} KB")
    print("\nScanning files...\n")

    # Count matches and tokens
    included = 0
    excluded = 0
    excluded_files = []
    included_files = []
    total_tokens = 0
    max_size_bytes = max_size_kb * 1024

    # Walk the directory
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, directory)

            try:
                # Check file size
                file_size = os.path.getsize(filepath)
                if file_size > max_size_bytes:
                    excluded += 1
                    excluded_files.append((relpath, "Too large"))
                    continue

                # Check patterns
                if should_include_file(relpath, include_patterns, exclude_patterns):
                    included += 1
                    # Read file and count tokens
                    try:
                        with open(
                            filepath, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()
                        tokens = estimate_token_count(content)
                        total_tokens += tokens
                        included_files.append((relpath, tokens, len(content)))
                    except Exception as e:
                        included_files.append((relpath, 0, 0))
                        print(f"ERROR reading {relpath}: {str(e)}")
                else:
                    excluded += 1
                    excluded_files.append((relpath, "Pattern mismatch"))
            except Exception as e:
                excluded += 1
                excluded_files.append((relpath, f"Error: {str(e)}"))

    # Sort included files by token count (descending)
    included_files.sort(key=lambda x: x[1], reverse=True)

    # Print included files with token counts
    print("INCLUDED FILES:")
    print(f"{'FILE PATH':<60} {'TOKENS':<10} {'SIZE (BYTES)':<15}")
    print("-" * 85)
    for relpath, tokens, size in included_files:
        print(f"{relpath:<60} {tokens:<10} {size:<15}")

    # Print excluded files if requested
    if show_excluded:
        print("\nEXCLUDED FILES:")
        print(f"{'FILE PATH':<60} {'REASON':<20}")
        print("-" * 85)
        for relpath, reason in excluded_files:
            print(f"{relpath:<60} {reason:<20}")

    # Print summary
    print("\nSUMMARY:")
    print(f"Total files included: {included}")
    print(f"Total files excluded: {excluded}")
    print(f"Total tokens in included files: {total_tokens}")
    print(f"Average tokens per file: {total_tokens / included if included else 0:.2f}")


if __name__ == "__main__":
    main()
