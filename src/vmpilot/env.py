"""
Environment and project directory management for VMPilot.
Handles environment variables, project roots, and directory management.
"""

import logging
import os

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
    # VMPILOT_ROOT environment variable is by the shell script
    vmpilot_root = os.environ.get("VMPILOT_ROOT")

    if vmpilot_root:
        logger.debug(f"Using VMPILOT_ROOT from environment in env: {vmpilot_root}")
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
        logger.debug(f"Using PROJECT_ROOT from environment: {project_root}")
        return project_root

    # Not set
    return ""


def get_plugins_dir() -> str:
    """
    Get the directory containing VMPilot plugins.

    Returns:
        Path to plugins directory
    """
    # Get the VMPilot root directory
    vmp_root = get_vmpilot_root()
    plugins_dir = os.path.join(vmp_root, "src", "vmpilot", "plugins")

    return plugins_dir


def get_docs_dir() -> str:
    """
    Get the directory containing VMPilot documentation.

    Returns:
        Path to documentation directory
    """
    docs_dir = os.path.join(get_vmpilot_root(), "docs", "source")
    return docs_dir


# Initialize environment variables when module is imported
try:
    vmpilot_root = get_vmpilot_root()
    project_root = get_project_root()
    plugins_dir = get_plugins_dir()
    docs_dir = get_docs_dir()

    logger.debug(f"Environment initialized:")
    logger.debug(f"  - VMPilot root: {vmpilot_root}")
    logger.debug(f"  - Project root: {project_root}")
    logger.debug(f"  - Plugins directory: {plugins_dir}")
    logger.debug(f"  - Documentation directory: {docs_dir}")
except Exception as e:
    logger.error(f"Error initializing environment: {str(e)}")
