"""
Environment and project directory management for VMPilot.
Handles environment variables, project roots, and directory management.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from . import config

logger = logging.getLogger(__name__)

# Patterns to extract project directory from system messages
PROJECT_ROOT_PATTERNS = [
    r"\$PROJECT_ROOT=([^\s]+)",
]


def get_vmpilot_root() -> str:
    """
    Get the root directory of VMPilot installation.

    Returns:
        Path to VMPilot root directory
    """
    # Check if VMPILOT_ROOT environment variable is set
    vmpilot_root = os.environ.get("VMPILOT_ROOT")

    if vmpilot_root:
        logger.info(f"Using VMPILOT_ROOT from environment: {vmpilot_root}")
        return vmpilot_root

    # If not set, calculate based on the location of this file
    # Go up three levels from this file: src/vmpilot/env.py -> src/vmpilot -> src -> root
    calculated_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    logger.info(f"Calculated VMPILOT_ROOT: {calculated_root}")

    # Set environment variable for other components
    os.environ["VMPILOT_ROOT"] = calculated_root

    return calculated_root


def get_project_root() -> str:
    """
    Get the root directory of the current project.

    Returns:
        Path to project root directory
    """
    # Check if PROJECT_ROOT environment variable is set
    project_root = os.environ.get("PROJECT_ROOT")

    if project_root:
        # Make sure it's expanded (in case it contains ~)
        expanded_root = os.path.expanduser(project_root)
        if expanded_root != project_root:
            os.environ["PROJECT_ROOT"] = expanded_root
            project_root = expanded_root
        logger.info(f"Using PROJECT_ROOT from environment: {project_root}")
        return project_root

    # If not set, use current working directory
    project_root = os.getcwd()
    logger.info(f"Using current directory as PROJECT_ROOT: {project_root}")

    # Set environment variable for other components
    os.environ["PROJECT_ROOT"] = project_root

    return project_root


def extract_project_dir(system_prompt_suffix: str) -> Optional[str]:
    """
    Extract project directory from system message if present.

    Args:
        system_prompt_suffix: System message suffix to extract project directory from

    Returns:
        Project directory if found, None otherwise
    """
    logger.debug(
        f"Extracting project directory from system message: {system_prompt_suffix}"
    )
    # Look for system message
    # Check for project directory patterns
    for pattern in PROJECT_ROOT_PATTERNS:
        match = re.search(pattern, system_prompt_suffix)
        logger.debug(f"Checking pattern: {pattern} in message: {system_prompt_suffix}")
        if match:
            project_dir = match.group(1)
            # Expand ~ to user's home directory
            expanded_dir = os.path.expanduser(project_dir)
            logger.info(
                f"Extracted project directory from message: {project_dir} (expanded to {expanded_dir})"
            )

            # Set environment variable with expanded path
            os.environ["PROJECT_ROOT"] = expanded_dir
            change_to_project_dir(expanded_dir)
            return expanded_dir

    # No project directory found in system message
    logger.debug("No project directory found in system message")
    return None


def change_to_project_dir(project_dir: Optional[str] = None) -> bool:
    """
    Ensure the project directory exists and is a directory before changing to it.

    Args:
        project_dir: Project directory to change to, or None to use PROJECT_ROOT env var

    Returns:
        True if directory change was successful, False otherwise

    Raises:
        Exception: If the directory doesn't exist, isn't a directory, or can't be accessed
    """
    # Use provided project_dir or get from environment
    if project_dir is None:
        project_dir = get_project_root()

    expanded_dir = os.path.expanduser(project_dir)
    logger.info(f"Attempting to change to project directory: {expanded_dir}")

    # Check if directory exists
    if not os.path.exists(expanded_dir):
        error = f"Project directory {project_dir} does not exist. See https://vmpdocs.a1.lingastic.org/user-guide/?h=project+directory#project-directory-configuration "
        logger.error(error)
        raise Exception(error)

    # Check if it's a directory
    if not os.path.isdir(expanded_dir):
        error_msg = (
            f"Failed to change to project directory {project_dir}: Not a directory"
        )
        logger.error(error_msg)
        raise Exception(error_msg)

    # Try to change to the directory
    try:
        os.chdir(expanded_dir)
        logger.info(f"Changed to project directory: {expanded_dir}")

        # Update environment variable in case it was expanded
        os.environ["PROJECT_ROOT"] = expanded_dir

        return True
    except PermissionError:
        error_msg = (
            f"Failed to change to project directory {project_dir}: Permission denied"
        )
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to change to project directory {project_dir}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def get_plugins_dir() -> str:
    """
    Get the directory containing VMPilot plugins.

    Returns:
        Path to plugins directory
    """
    # Get the VMPilot root directory
    vmp_root = get_vmpilot_root()
    plugins_dir = os.path.join(vmp_root, "src", "vmpilot", "plugins")

    logger.info(f"Plugins directory: {plugins_dir}")
    return plugins_dir


def get_docs_dir() -> str:
    """
    Get the directory containing VMPilot documentation.

    Returns:
        Path to documentation directory
    """
    docs_dir = os.path.join(get_vmpilot_root(), "docs", "source")
    logger.info(f"Documentation directory: {docs_dir}")
    return docs_dir


# Initialize environment variables when module is imported
try:
    vmpilot_root = get_vmpilot_root()
    project_root = get_project_root()
    plugins_dir = get_plugins_dir()
    docs_dir = get_docs_dir()

    logger.info(f"Environment initialized:")
    logger.info(f"  - VMPilot root: {vmpilot_root}")
    logger.info(f"  - Project root: {project_root}")
    logger.info(f"  - Plugins directory: {plugins_dir}")
    logger.info(f"  - Documentation directory: {docs_dir}")
except Exception as e:
    logger.error(f"Error initializing environment: {str(e)}")
