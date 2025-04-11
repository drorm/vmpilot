"""
Project management module for VMPilot.

This module handles project-specific configuration and operations,
particularly focusing on the .vmpilot directory structure.
"""

# Patterns to extract project directory from system messages
PROJECT_ROOT_PATTERNS = [
    r"\$PROJECT_ROOT=([^\s]+)",
]

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


class Project:
    """
    Class to manage project-specific configuration and operations.

    This class handles the .vmpilot directory structure and associated files
    that provide context about the project and current work.
    """

    def __init__(self, system_prompt_suffix: str, output_callback: callable):
        self.output_callback = output_callback
        self.finish_chat = False
        self.project_root = None
        self.extract_project_dir(system_prompt_suffix)
        logger.info(f"Extracted project directory in project: {self.project_root}")
        """
        Initialize a Project instance.

        Args:
            system_prompt_suffix: System message to extract project directory from
        """

        if self.project_root is not None:
            self.vmpilot_dir = os.path.join(self.project_root, ".vmpilot")
            self.prompts_dir = os.path.join(self.vmpilot_dir, "prompts")
            self.project_md = os.path.join(self.prompts_dir, "project.md")
            self.current_issue_md = os.path.join(self.prompts_dir, "current_issue.md")

    def check_vmpilot_structure(self):
        """
        Check if .vmpilot directory and required subdirectories exist.

        Returns:
            bool: True if the complete structure exists, False otherwise
        """

        if not self.project_root:
            logger.info("Project root is not set. Won't check .vmpilot structure.")
            return False

        vmpilot_exists = os.path.exists(self.vmpilot_dir)
        prompts_exists = os.path.exists(self.prompts_dir)
        project_md_exists = os.path.exists(self.project_md)

        logger.info(
            f".vmpilot directory {'exists' if vmpilot_exists else 'does not exist'} at {self.vmpilot_dir}"
        )

        if vmpilot_exists:
            logger.info(
                f".vmpilot/prompts directory {'exists' if prompts_exists else 'does not exist'}"
            )

            if prompts_exists:
                logger.info(
                    f"project.md {'exists' if project_md_exists else 'does not exist'}"
                )
                logger.info(
                    f"current_issue.md {'exists' if os.path.exists(self.current_issue_md) else 'does not exist'}"
                )

        # For the complete structure to exist, we need all of these to be present
        return vmpilot_exists and prompts_exists and project_md_exists

    def extract_project_dir(self, system_prompt_suffix: str) -> None:
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
            logger.debug(
                f"Checking pattern: {pattern} in message: {system_prompt_suffix}"
            )
            if match:
                project_root = match.group(1)
                # Expand ~ to user's home directory
                expanded_dir = os.path.expanduser(project_root)
                logger.info(
                    f"Extracted project directory from message: {project_root} (expanded to {expanded_dir})"
                )

                # Set environment variable with expanded path
                os.environ["PROJECT_ROOT"] = expanded_dir
                self.project_root = expanded_dir
                self.change_to_project_dir()
                return

        # No project directory found in system message
        logger.debug("No project directory found in system message")

    def change_to_project_dir(self) -> bool:
        """
        Ensure the project directory exists and is a directory before changing to it.

        Returns:
            True if directory change was successful, False otherwise

        Raises:
            Exception: If the directory doesn't exist, isn't a directory, or can't be accessed
        """

        # Check if directory exists
        if not os.path.exists(self.project_root):
            error = f"Project directory {project_root} does not exist. See https://vmpdocs.a1.lingastic.org/user-guide/?h=project+directory#project-directory-configuration "
            logger.error(error)
            raise Exception(error)

        # Check if it's a directory
        if not os.path.isdir(self.project_root):
            error_msg = f"Failed to change to project directory {self.project_root}: Not a directory"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Try to change to the directory
        try:
            os.chdir(self.project_root)
            logger.debug(f"Changed to project directory: {self.project_root}")

            # Update environment variable in case it was self.project_root
            os.environ["PROJECT_ROOT"] = self.project_root

            return True
        except PermissionError:
            error_msg = f"Failed to change to project directory {self.project_root}: Permission denied"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = (
                f"Failed to change to project directory {self.project_root}: {str(e)}"
            )
            logger.error(error_msg)
            raise Exception(error_msg)

    def check_project_structure(self) -> bool:
        """
        Check if the project has the required .vmpilot directory structure.
        If structure is missing, present options to the user and end the chat.

        """

        has_structure = self.check_vmpilot_structure()
        # If structure doesn't exist, and there's a project root, ask the user
        if not has_structure and self.project_root:
            project_setup_message = """
A project description helps me better understand your codebase and provide relevant assistance. 
Your project structure is not yet set up. Would you like me to:

a. **Recommended:** Analyze your existing code and generate a tailored project description
b. Create standard project files from a template and you can edit them later
c. Skip project setup (I'll remember this preference)

You can change the content of these files at any time. Your choice will help me provide more targeted assistance in future interactions.

Note that the project description is used at the beginning of each conversation to help me understand your project better.

Once you've made your choice, I'll use the project plugin to implement it.
"""
            # Send message to user through the output callback if available
            if hasattr(self, "output_callback") and self.output_callback:
                self.output_callback({"type": "text", "text": project_setup_message})
                self.finish_chat = True
            else:
                # Fallback to print if no callback
                print(project_setup_message)

    def done(self) -> bool:
        """
        Check if we need to finish the chat early since we're asked the user for a project setup.

        Returns:
            bool: True if the chat should be finished, False otherwise
        """
        return self.finish_chat
