"""
Project management module for VMPilot.

This module handles project-specific configuration and operations,
particularly focusing on the .vmpilot directory structure.
"""

import os
import logging

logger = logging.getLogger(__name__)

class Project:
    """
    Class to manage project-specific configuration and operations.
    
    This class handles the .vmpilot directory structure and associated files
    that provide context about the project and current work.
    """
    
    def __init__(self, project_path):
        """
        Initialize a Project instance.
        
        Args:
            project_path (str): Path to the project root directory
        """
        self.project_path = project_path
        self.vmpilot_dir = os.path.join(project_path, '.vmpilot')
        self.prompts_dir = os.path.join(self.vmpilot_dir, 'prompts')
        self.project_md = os.path.join(self.prompts_dir, 'project.md')
        self.current_issue_md = os.path.join(self.prompts_dir, 'current_issue.md')
        
    def check_vmpilot_structure(self):
        """
        Check if .vmpilot directory and required subdirectories exist.
        
        Returns:
            bool: True if the complete structure exists, False otherwise
        """
        vmpilot_exists = os.path.exists(self.vmpilot_dir)
        prompts_exists = os.path.exists(self.prompts_dir)
        project_md_exists = os.path.exists(self.project_md)
        
        logger.info(f".vmpilot directory {'exists' if vmpilot_exists else 'does not exist'} at {self.vmpilot_dir}")
        
        if vmpilot_exists:
            logger.info(f".vmpilot/prompts directory {'exists' if prompts_exists else 'does not exist'}")
            
            if prompts_exists:
                logger.info(f"project.md {'exists' if project_md_exists else 'does not exist'}")
                logger.info(f"current_issue.md {'exists' if os.path.exists(self.current_issue_md) else 'does not exist'}")
        
        # For the complete structure to exist, we need all of these to be present
        return vmpilot_exists and prompts_exists and project_md_exists
    
    def has_readme(self):
        """
        Check if the project has a README file at the root.
        
        Returns:
            str or None: Path to the README file if found, None otherwise
        """
        # Check for various common README filenames
        readme_variants = ['README.md', 'Readme.md', 'readme.md', 'README.txt', 'README']
        
        for variant in readme_variants:
            readme_path = os.path.join(self.project_path, variant)
            if os.path.exists(readme_path):
                logger.info(f"Found README at {readme_path}")
                return readme_path
        
        logger.info("No README found in project root")
        return None
