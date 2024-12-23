"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
"""

import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast

from anthropic import (
    Anthropic,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from .tools import BashTool, EditTool, ToolCollection, ToolResult
import subprocess
import os

# Configure logging
from .agent_logging import (
    log_error,
    log_message,
    log_message_content,
    log_message_processing,
    log_message_received,
    log_token_usage,
    log_tool_message,
)


def execute_shell_command(command: str, language: str = "bash") -> ToolResult:
    """Execute a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        return ToolResult(success=result.returncode == 0, output=output)
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def execute_file_edit(command: str, path: str, **kwargs) -> ToolResult:
    """Execute file operations."""
    try:
        if command == "create":
            if os.path.exists(path):
                return ToolResult(success=False, output=f"File already exists: {path}")
            with open(path, "w") as f:
                f.write(kwargs.get("file_text", ""))
            return ToolResult(success=True, output=f"Created file: {path}")

        elif command == "str_replace":
            if not os.path.exists(path):
                return ToolResult(success=False, output=f"File not found: {path}")
            with open(path, "r") as f:
                content = f.read()
            new_content = content.replace(kwargs["old_str"], kwargs["new_str"])
            with open(path, "w") as f:
                f.write(new_content)
            return ToolResult(success=True, output=f"Replaced text in {path}")

        elif command == "insert":
            if not os.path.exists(path):
                return ToolResult(success=False, output=f"File not found: {path}")
            with open(path, "r") as f:
                lines = f.readlines()
            insert_at = kwargs["insert_line"]
            lines.insert(insert_at, kwargs["new_str"] + "\n")
            with open(path, "w") as f:
                f.writelines(lines)
            return ToolResult(
                success=True, output=f"Inserted text at line {insert_at} in {path}"
            )

        return ToolResult(success=False, output=f"Unknown command: {command}")
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def handle_tool_use(tool_use: dict) -> ToolResult:
    """Handle tool use by executing the specified tool."""
    tool_name = tool_use.get("name")
    tool_args = tool_use.get("args", {})

    if tool_name == "shell":
        return execute_shell_command(
            tool_args["command"], tool_args.get("language", "bash")
        )
    elif tool_name == "edit_file":
        return execute_file_edit(**tool_args)
    else:
        return ToolResult(success=False, output=f"Unknown tool: {tool_name}")


# Import config from vmpilot
from vmpilot.config import (
    DEFAULT_PROVIDER,
    MAX_TOKENS,
    RECURSION_LIMIT,
    TEMPERATURE,
    TOOL_OUTPUT_LINES,
    Provider,
    config,
)

import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
}


SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with bash command execution capabilities
* You can execute any valid bash command but do not install packages
* When using commands that are expected to output very large quantities of text, redirect into a tmp file
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using the shell tool, provide both command and language parameters:
  - command: The shell command to execute (e.g. "ls -l", "cat file.py")
  - language: Output syntax highlighting (e.g. "bash", "python", "text")
* Only execute valid bash commands
* Use bash to view files using commands like cat, head, tail, or less
* Each command should be a single string (e.g. "head -n 10 file.txt" not ["head", "-n", "10", "file.txt"])
* The output of the command is passed fully to you, but truncated to {TOOL_OUTPUT_LINES} lines when shown to the user

</IMPORTANT>

<TOOLS>
* Use the bash tool to execute system commands. Provide commands as a single string.
* Use the str_replace_editor tool for editing files.
</TOOLS>"""


async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaContentBlockParam], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    temperature: float,
    max_tokens: int = 4096,
):
    """
    Agentic sampling loop for the assistant/tool interaction of computer use.
    """
    tool_collection = ToolCollection(
        BashTool(),
        EditTool(),
    )

    system = BetaTextBlockParam(
        type="text",
        text=f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}",
    )

    while True:
        enable_prompt_caching = False
        betas = [COMPUTER_USE_BETA_FLAG]
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key, max_retries=4)
            enable_prompt_caching = True

        if enable_prompt_caching:
            betas.append(PROMPT_CACHING_BETA_FLAG)
            _inject_prompt_caching(messages)
            # Because cached reads are 10% of the price, we don't think it's
            # ever sensible to break the cache by truncating images
            system["cache_control"] = {"type": "ephemeral"}

        # Call the API
        # we use raw_response to provide debug information to streamlit. Your
        # implementation may be able call the SDK directly with:
        # `response = client.messages.create(...)` instead.
        try:
            raw_response = client.beta.messages.with_raw_response.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=[system],
                tools=tool_collection.to_params(),
                betas=betas,
            )
            logger.debug(f"API call successful: {raw_response}")
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(e.request, e.response, e)
            return messages
        except APIError as e:
            logger.error(e.request, e.body, e)
            return messages

        # logger.info.http_response.request, raw_response.http_response, None

        response = raw_response.parse()
        # logger.info(f"API response: {response}")

        response_params = _response_to_params(response)
        messages.append(
            {
                "role": "assistant",
                "content": response_params,
            }
        )

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            output_callback(content_block)
            if content_block["type"] == "tool_use":
                result = await tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast(dict[str, Any], content_block["input"]),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block["id"])
                )
                tool_output_callback(result, content_block["id"])

        if not tool_result_content:
            return messages

        messages.append({"content": tool_result_content, "role": "user"})
        # Format tool results as properly structured messages
        logger.debug(f"Processing tool results: {tool_result_content}")
        formatted_tool_results = []
        for result in tool_result_content:
            # Create a formatted message that includes both tool use and result
            if isinstance(result["content"], list):
                for content in result["content"]:
                    if content["type"] == "text":
                        formatted_tool_results.append(
                            {
                                "type": "text",
                                "text": f"Tool Result ({result['tool_use_id']}) {'[ERROR]' if result.get('is_error') else ''}:\n{content['text']}",
                            }
                        )
            elif isinstance(result["content"], str):
                formatted_tool_results.append(
                    {
                        "type": "text",
                        "text": f"Tool Result ({result['tool_use_id']}):\n{result['content']}",
                    }
                )

        # Add formatted results to message history
        messages.append({"role": "user", "content": formatted_tool_results})


def _response_to_params(
    response: BetaMessage,
) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
    res: list[BetaTextBlockParam | BetaToolUseBlockParam] = []
    for block in response.content:
        if isinstance(block, BetaTextBlock):
            res.append({"type": "text", "text": block.text})
        else:
            res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    return res


def _inject_prompt_caching(
    messages: list[BetaMessageParam],
):
    """
    Set cache breakpoints for the 3 most recent turns
    one cache breakpoint is left for tools/system prompt, to be shared across sessions
    """

    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(
            content := message["content"], list
        ):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                    {"type": "ephemeral"}
                )
            else:
                content[-1].pop("cache_control", None)
                # we'll only every have one extra turn per loop
                break


def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text
