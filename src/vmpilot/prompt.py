"""
Prompt for the agent
"""

import logging
import pathlib
import platform
from datetime import datetime

from vmpilot.config import TOOL_OUTPUT_LINES
from vmpilot.config import Provider as APIProvider
from vmpilot.config import current_provider
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


def get_available_tools_description():
    """Generate a description of available tools based on actual configuration."""
    from vmpilot.tools.setup_tools import setup_tools

    try:
        tools = setup_tools()
        if not tools:
            return "No tools are currently available."

        tool_descriptions = []
        for tool in tools:
            schema = tool.get("schema", {})
            if schema.get("type") == "function":
                func_info = schema.get("function", {})
                name = func_info.get("name", "Unknown")
                description = func_info.get("description", "No description available")
                tool_descriptions.append(
                    f"* Use the {name} tool for {description.split('.')[0].lower()}."
                )

        if tool_descriptions:
            return "\n".join(tool_descriptions)
        else:
            return "Tools are available but descriptions could not be generated."

    except Exception as e:
        logger.warning(f"Failed to get tools description: {e}")
        return "* Use the shell tool for executing bash commands.\n* Use the create_file tool for creating files.\n* Use the edit_file tool for editing files."


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
* The root of the project, if any, is {project_root}
* The root of VMPilot is {get_vmpilot_root()}
* VMPilot's plugins are located in {get_plugins_dir()}
* VMPilot's documentation is located in {get_docs_dir()}
* When using your shelltool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
</SYSTEM_CAPABILITY>

<FILE_EDITING>
When editing files, provid the *full* path and use diff blocks to show what to search for and replace:
```
/path/to/file
<<<<<<< SEARCH
(text to find and replace)
=======
(text to replace it with)
>>>>>>> REPLACE
```

The SEARCH text must EXACTLY match text in the file. Include enough context for unique matches.
Include ALL indentation and formatting in both sections.
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
{get_available_tools_description()}
</TOOLS>

<PLUGINS>
{get_plugins_readme()}
</PLUGINS>
{project_md_content}
<CURRENT ISSUE>
This is the current issue we're working on. You do not need to fetch it again.
{full_current_issue}
</CURRENT ISSUE>
"""
    # Determine current provider
    provider_name = ""
    provider = current_provider.get()

    if provider == APIProvider.ANTHROPIC:
        provider_name = "anthropic"
    elif provider == APIProvider.OPENAI:
        provider_name = "openai"
    elif provider == APIProvider.GOOGLE:
        provider_name = "google"

    # Try to load a prompt file for the provider
    prompts_dir = pathlib.Path(__file__).parent / "prompts"
    prompt_file = prompts_dir / f"{provider_name}.md"
    provider_prompt = ""
    if prompt_file.exists():
        try:
            with open(prompt_file, "r") as f:
                provider_prompt = f.read()
            logger.debug(f"Loaded provider-specific prompt from {prompt_file}")
        except Exception as e:
            logger.warning(f"Failed to read prompt file {prompt_file}: {e}")
            provider_prompt = ""
    logger.debug(f"Provider prompt: {provider_prompt}")

    prompt += provider_prompt

    return prompt
