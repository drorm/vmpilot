"""
Prompt for the agent
"""

import logging
import pathlib
import platform
from datetime import datetime

from vmpilot.config import TOOL_OUTPUT_LINES
from vmpilot.env import (
    get_docs_dir,
    get_plugins_dir,
    get_project_root,
    get_vmpilot_root,
)
from vmpilot.project import get_chat_info, get_project_description

logger = logging.getLogger(__name__)


# Read plugins README.md
def get_plugins_readme():
    plugins_readme_path = pathlib.Path(get_plugins_dir()) / "README.md"
    try:
        with open(plugins_readme_path, "r") as f:
            logger.debug(f"Loaded plugins README from {plugins_readme_path}")
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Plugins README not found at {plugins_readme_path}")
        return "No plugins available"


# Generate system prompt on demand, ensuring current project root is used
def get_system_prompt():
    project_root = get_project_root()
    project_md_content = get_project_description()
    current_issue_content = get_chat_info()
    # if it's None or empty,
    if current_issue_content is None or current_issue_content == "":
        full_current_issue = ""
    else:
        # if it's not empty, use it
        full_current_issue = f"""
<CURRENT ISSUE>
This is the current issue we're working on. You do not need to fetch it again.
{current_issue_content}
</CURRENT ISSUE>
"""

    prompt = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with bash command execution capabilities
* You can execute any valid bash command but do not install packages
* When using commands that are expected to output very large quantities of text, redirect into a tmp file
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}
* The root of the project is {project_root}
* The root of VMPilot is {get_vmpilot_root()}
* VMPilot's plugins are located in {get_plugins_dir()}
* VMPilot's documentation is located in {get_docs_dir()}
* When using your shelltool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
</SYSTEM_CAPABILITY>

<FILE_EDITING>
When editing files, provid the *full* path and use diff blocks to show what to search for and replace:
/path/to/file
<<<<<<< SEARCH
(text to find and replace)
=======
(text to replace it with)
>>>>>>> REPLACE

The SEARCH text must exactly match text in the file. Include enough context for unique matches.
Include all indentation and formatting in both sections.
Use multiple edit blocks if needed.
</FILE_EDITING>

<IMPORTANT>
* When using the shell tool, provide both command and language parameters:
  - command: The shell command to execute bash command (e.g. "ls -l", "cat file.py")
  - language: Output syntax highlighting (e.g. "bash", "python", "text")
* Only execute valid bash commands
* Use bash to view files using commands like cat, head, tail, or less
* Each command should be a single string (e.g. "head -n 10 file.txt" not ["head", "-n", "10", "file.txt"])
* The output of the command is passed fully to you, but truncated to {TOOL_OUTPUT_LINES} lines when shown to the user

</IMPORTANT>

<TOOLS>
* Use the EditTool tool for editing files.
* Use the CreateFileTool tool for creating files. Takes path and content as input. **Always use this to create files.**
* Use the GoogleSearchTool tool for searching the web. The output will be a list of relevant search results.
* Use the WebContentTool tool for fetching web content. The output will be the content of the page.
</TOOLS>

<PLUGINS>
{get_plugins_readme()}
</PLUGINS>
{project_md_content}
<CURRENT ISSUE>
This is the current issue we're working on. You do not need to fetch it again.
{full_current_issue}
</CURRENT ISSUE>
<WORKFLOW_CONTROL>
Follow this sequence:
1. **Investigate**: Collect necessary information (e.g., from files or system state) to understand the task.
2. **Plan**: Present a clear plan to the user, including what you intend to change or create. Wait for explicit approval.
3. **Implement**: Only proceed with actions (e.g., file edits or shell commands) *after* the user confirms the plan.
</WORKFLOW_CONTROL>
"""
    logger.debug(f"Prompt: {current_issue_content}")
    return prompt
