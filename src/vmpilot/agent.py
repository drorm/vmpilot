"""
LangChain-based implementation for VMPilot's agent functionality.
Replaces the original loop.py from Claude Computer Use with LangChain tools and agents.
"""

import json
import logging
import os
import sys
import traceback
from contextvars import ContextVar
from enum import StrEnum
from typing import Optional

import httpx

from vmpilot.config import TOOL_OUTPUT_LINES

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

logging.basicConfig(level=logging.INFO)
# Set logging levels for specific loggers
logger = logging.getLogger(__name__)


import platform
from datetime import datetime
from typing import Any, Callable, Dict, List

from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config
from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.langchain_edit import FileEditTool
from vmpilot.tools.aider_edit import AiderTool
from vmpilot.caching.chat_models import ChatAnthropic

# Flag to enable beta features in Anthropic API
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

# The system prompt that's passed on from webui.
prompt_suffix: ContextVar[Optional[Any]] = ContextVar("prompt_suffix", default=None)
# The current provider (Anthropic/OpenAI)
current_provider: ContextVar[Optional[APIProvider]] = ContextVar(
    "current_provider", default=None
)

# System prompt maintaining compatibility with original VMPilot
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with bash command execution capabilities
* You can execute any valid bash command but do not install packages
* When using commands that are expected to output very large quantities of text, redirect into a tmp file
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}
* When using your shelltool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
</SYSTEM_CAPABILITY>

<FILE_EDITING>
When editing files, use diff blocks to show what to search for and replace:
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
* Use the shell tool to execute system commands. Provide commands as a single string.
* Use the AiderTool tool for editing files.
</TOOLS>"""


"""
method to modify the state messages
Called by the agent to modify the messages generated by the agent
"""


def _modify_state_messages(state: AgentState):
    # Keep the last N messages in the state as well as the system prompt
    N_MESSAGES = 30  # TODO: Change this to a config value

    # Handle system prompt with potential cache control
    suffix = prompt_suffix.get()
    new_messages = []
    messages = state["messages"][:N_MESSAGES]

    # Get current provider
    provider = current_provider.get()

    if provider != APIProvider.ANTHROPIC:
        return state["messages"]

    # If the provider is Anthropic, add cache control to messages. https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
    cached = 3  # antropic allows up to 4 and we use one for system
    for message in reversed(messages):
        if cached > 0:
            if isinstance(message.content, list):
                for block in message.content:
                    block["cache_control"] = {"type": "ephemeral"}
                    logger.debug(f"Added cache_eph block: {block}")
                    cached -= 1
            else:
                message.additional_kwargs["cache_control"] = {"type": "ephemeral"}
                logger.debug(
                    f"Added cache_eph message: {message}, additional_kwargs: {message.additional_kwargs}"
                )
                cached -= 1
        else:
            if isinstance(message.content, list):
                for block in message.content:
                    block.pop("cache_control", None)
            else:
                message.additional_kwargs.pop("cache_control", None)

    logger.debug(f"Modified state messages: {state['messages']}")
    return messages


def setup_tools(llm=None):
    """Initialize and configure LangChain tools."""
    # Suppress warning about shell tool safeguards
    import warnings

    warnings.filterwarnings(
        "ignore", category=UserWarning, module="langchain_community.tools.shell.tool"
    )

    tools = []

    # Initialize Shell Tool with fencing capability if LLM is provided
    if llm is not None:
        try:
            shell_tool = SetupShellTool(llm=llm)
            shell_tool.description = """Execute bash commands in the system. Input should be a single command string. Example inputs:
            - ls /path
            - cat file.txt
            - head -n 10 file.md
            - grep pattern file
            The output will be automatically formatted with appropriate markdown syntax."""
            tools.append(shell_tool)
        except Exception as e:
            logger.error(f"Error: Error creating SetupShellTool: {e}")

    # Add file editing tool (excluding view operations which are handled by shell tool)
    # tools.append(FileEditTool(view_in_shell=True))
    tools.append(AiderTool())

    # Return all tools
    return tools


"""
Create the langchain agent
"""


async def create_agent(
    model: str,
    api_key: str,
    provider: APIProvider,
    system_prompt_suffix: str = "",
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
):
    """Create a LangChain agent with the configured tools."""
    enable_prompt_caching = False
    betas = [COMPUTER_USE_BETA_FLAG]

    # openai caches automatically
    if provider == APIProvider.ANTHROPIC:
        enable_prompt_caching = True

    if enable_prompt_caching:
        betas.append(PROMPT_CACHING_BETA_FLAG)

    if provider == APIProvider.ANTHROPIC:
        # Get beta flags from config
        provider_config = config.get_provider_config(APIProvider.ANTHROPIC)
        if provider_config.beta_flags:
            betas.extend([flag for flag in provider_config.beta_flags.keys()])

        headers = {
            "anthropic-beta": ",".join(betas),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system_content = {
            "type": "text",
            "text": SYSTEM_PROMPT
            + ("\n\n" + system_prompt_suffix if system_prompt_suffix else ""),
        }

        if enable_prompt_caching:
            system_content["cache_control"] = {"type": "ephemeral"}

        llm = ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=api_key,
            timeout=30,  # Add 30-second timeout
            model_kwargs={
                "extra_headers": {"anthropic-beta": ",".join(betas)},
                "system": [system_content],
            },
        )
    elif provider == APIProvider.OPENAI:
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
            openai_api_key=api_key,
            timeout=30,
        )

    # Set up tools with LLM for fencing capability
    tools = setup_tools(llm=llm)

    # Create React agent
    agent = create_react_agent(
        llm, tools, state_modifier=_modify_state_messages, checkpointer=MemorySaver()
    )

    return agent


"""
Process messages through the agent and handle outputs
"""


async def process_messages(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: List[dict],
    output_callback: Callable[[Dict], None],
    tool_output_callback: Callable[[Any, str], None],
    api_key: str,
    max_tokens: int = MAX_TOKENS,
    temperature: float = TEMPERATURE,
    disable_logging: bool = False,
    recursion_limit: int = None,
) -> List[dict]:
    logger.debug(f"DEBUG: model={model}, provider={provider}")
    """Process messages through the agent and handle outputs."""
    # Get recursion limit from config if not explicitly set
    if recursion_limit is None:
        provider_config = config.get_provider_config(provider)
        recursion_limit = provider_config.recursion_limit

    logging.getLogger("httpx").setLevel(logging.WARNING)
    if disable_logging:
        # Disable all logging if flag is set
        logging.getLogger("vmpilot").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("httpcore").setLevel(logging.ERROR)
        logging.getLogger("asyncio").setLevel(logging.ERROR)
        logger.setLevel(logging.ERROR)

    # Set prompt suffix and provider
    prompt_suffix.set(system_prompt_suffix)
    current_provider.set(provider)

    # Handle prompt caching for Anthropic provider
    enable_prompt_caching = provider == APIProvider.ANTHROPIC

    logger.debug("DEBUG: Creating agent")
    # Create agent
    agent = await create_agent(
        model, api_key, provider, system_prompt_suffix, temperature, max_tokens
    )
    logger.debug("DEBUG: Agent created successfully")

    # Convert messages to LangChain format
    formatted_messages = []
    try:
        for msg in messages:
            logger.debug(f"Processing message: {msg}")
            log_message_processing(msg["role"], type(msg["content"]).__name__)
            if msg["role"] == "user":
                if isinstance(msg["content"], str):
                    logger.debug("Processing single message")
                    formatted_messages.append(
                        HumanMessage(content=msg["content"], additional_kwargs={})
                    )
                elif isinstance(msg["content"], list):
                    logger.debug(f"Processing list of messages")
                    # Handle structured content
                    for item in msg["content"]:
                        if item["type"] == "text":
                            # Preserve cache control if present
                            additional_kwargs = {}
                            if "cache_control" in item:
                                additional_kwargs["cache_control"] = item[
                                    "cache_control"
                                ]
                            formatted_messages.append(
                                HumanMessage(
                                    content=item["text"],
                                    cache_control=item.get("cache_control"),
                                    additional_kwargs=(
                                        additional_kwargs if additional_kwargs else {}
                                    ),
                                )
                            )
            elif msg["role"] == "assistant":
                if isinstance(msg["content"], str):
                    formatted_messages.append(AIMessage(content=msg["content"]))
                elif isinstance(msg["content"], list):
                    # Combine all content parts into one message
                    content_parts = []
                    for item in msg["content"]:
                        if item["type"] == "text":
                            content_parts.append(item["text"])
                        elif item["type"] == "tool_use":
                            # Include tool name and output in the message
                            tool_output = item.get("output", "")
                            if isinstance(tool_output, dict):
                                tool_output = tool_output.get("output", "")
                            content_parts.append(
                                f"Tool use: {item['name']}\nOutput: {tool_output}"
                            )
                    if content_parts:
                        formatted_messages.append(
                            AIMessage(content="\n".join(content_parts))
                        )

        logger.debug(f"Formatted {len(formatted_messages)} messages")
    except Exception as e:
        logger.error(f"Error formatting messages: {e}")
        raise

    # Stream agent responses
    thread_id = f"vmpilot-{os.getpid()}"
    logger.debug(f"Starting agent stream with {len(formatted_messages)} messages")

    async def process_stream():
        try:
            async for response in agent.astream(
                {"messages": formatted_messages},
                config={
                    "thread_id": thread_id,
                    "run_name": f"vmpilot-run-{thread_id}",
                    "recursion_limit": recursion_limit,
                },
                stream_mode="values",
            ):
                logger.debug(f"Got response: {response}")
                try:
                    logger.debug(
                        {"type": "text", "text": f"RAW LLM RESPONSE: {response}\n"}
                    )

                    # Handle different response types
                    if "messages" in response:
                        message = response["messages"][-1]

                        # Log message receipt and usage for all message types
                        log_message_received(message)
                        log_token_usage(message, "info")

                        from langchain_core.messages import (
                            AIMessage,
                            HumanMessage,
                            ToolMessage,
                        )

                        if isinstance(message, ToolMessage):
                            logger.debug(f"isinstance message: {message}")
                            # Handle tool message responses
                            log_tool_message(message)
                            log_message_content(message, message.content)

                            tool_result = {"output": message.content, "error": None}
                            tool_output_callback(tool_result, message.name)

                        elif isinstance(message, AIMessage):
                            content = message.content
                            log_message_content(message, content)

                            if isinstance(content, str):
                                # Skip if content matches last user message
                                if (
                                    formatted_messages
                                    and isinstance(formatted_messages[-1], HumanMessage)
                                    and content.strip()
                                    == formatted_messages[-1].content.strip()
                                ):
                                    continue
                                output_callback({"type": "text", "text": content})

                            elif isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict):
                                        if item.get("type") == "text":
                                            output_callback(
                                                {"type": "text", "text": item["text"]}
                                            )

                                        elif item.get("type") == "tool_use":
                                            # Log tool usage declaration
                                            logger.debug(
                                                f"Tool use declared: {item['name']}"
                                            )

                                            # Handle tool output if present
                                            if "output" in item:
                                                tool_result = {
                                                    "output": item["output"],
                                                    "error": None,
                                                }
                                                tool_output_callback(
                                                    tool_result, item["name"]
                                                )
                                    else:
                                        logger.warning(
                                            f"Unknown content item type: {type(item)}"
                                        )
                        else:
                            logger.debug(
                                f"Unhandled message type: {type(message).__name__}"
                            )
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
                    output_callback(
                        {"type": "text", "text": f"Error processing response: {str(e)}"}
                    )
        except Exception as e:
            error_message = str(e)
            message = ""
            if "Recursion limit" in error_message and "reached" in error_message:
                message = f" I've done {recursion_limit} steps in a row. Let me know if you'd like me to continue. "
                logger.info(message)
            else:
                logger.error(f"Error in agent stream: {e}")
                logger.error("".join(traceback.format_tb(e.__traceback__)))
                message = f"Error in agent stream: {str(e)}"
            output_callback({"type": "text", "text": f"{message}"})

    # Run the stream processor
    await process_stream()
    return messages
