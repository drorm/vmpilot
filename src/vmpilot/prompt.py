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

<PLUGINS>
{get_plugins_readme()}
</PLUGINS>"""
