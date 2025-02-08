"""
Prompt for the agent
"""

import pathlib
import platform
from datetime import datetime

from vmpilot.config import TOOL_OUTPUT_LINES


# Read plugins README.md
def get_plugins_readme():
    plugins_readme_path = pathlib.Path(__file__).parent / "plugins" / "README.md"
    try:
        with open(plugins_readme_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "No plugins available"


# System prompt maintaining compatibility with original VMPilot
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with bash command execution capabilities
* You can execute any valid bash command but do not install packages
* When using commands that are expected to output very large quantities of text, redirect into a tmp file
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}
* When using your shelltool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
</SYSTEM_CAPABILITY>

<FILE_EDITING>
When editing files, provided the path and use diff blocks to show what to search for and replace:
/path/to/file
<<<<<<< SEARCH
(text to find and replace)
=======
(text to replace it with)
>>>>>>> REPLACE

The SEARCH text must exactly match text in the file. Include enough context for unique matches.
Include all indentation and formatting in both sections.
You can use multiple edit blocks if needed.
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
</TOOLS>

<PLUGINS>
{get_plugins_readme()}
</PLUGINS>"""
