"""
LangChain-based implementation for VMPilot's agent functionality.
Replaces the original loop.py from Claude Computer Use with LangChain tools and agents.
"""

import logging
import os
from contextvars import ContextVar
from enum import StrEnum
from typing import Optional

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
# Set logging levels for specific loggers
logger = logging.getLogger(__name__)


import platform
from datetime import datetime
from typing import Any, Callable, Dict, List

from langchain_anthropic import ChatAnthropic
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

from vmpilot.config import Provider as APIProvider
from vmpilot.config import config
from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.langchain_edit import FileEditTool

# Flag to enable beta features in Anthropic API
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

# The system prompt that's passed on from webui.
prompt_suffix: ContextVar[Optional[Any]] = ContextVar("prompt_suffix", default=None)

# System prompt maintaining compatibility with original VMPilot
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with bash command execution capabilities
* You can execute any valid bash command but do not install packages
* When using commands that are expected to output very large quantities of text, redirect into a tmp file
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* Only execute valid bash commands
* Use bash to view files using commands like cat, head, tail, or less
* Each command should be a single string (e.g. "head -n 10 file.txt" not ["head", "-n", "10", "file.txt"])
</IMPORTANT>

<TOOLS>
* Use the bash tool to execute system commands. Provide commands as a single string.
* Use the str_replace_editor tool for editing files.
</TOOLS>"""


def _modify_state_messages(state: AgentState):
    # Keep the last N messages in the state as well as the system prompt
    N_MESSAGES = 30

    # Handle system prompt with potential cache control
    suffix = prompt_suffix.get()
    if isinstance(suffix, list):
        # Handle structured system prompt array
        system_messages = []
        for item in suffix:
            if (
                not isinstance(item, dict)
                or "type" not in item
                or item["type"] != "text"
            ):
                continue

            text = item.get("text", "").strip()
            if not text:
                continue

            additional_kwargs = {}
            if "cache_control" in item:
                additional_kwargs["cache_control"] = item["cache_control"]

            system_messages.append(
                SystemMessage(content=text, additional_kwargs=additional_kwargs)
            )

        if system_messages:
            messages = system_messages + state["messages"][:N_MESSAGES]
        else:
            # Fallback to basic system message
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"][
                :N_MESSAGES
            ]
    else:
        # Regular system prompt without cache control
        system_prompt = SYSTEM_PROMPT
        if suffix and isinstance(suffix, str) and suffix.strip():
            system_prompt = f"{system_prompt}\n\n{suffix.strip()}"
        system_message = SystemMessage(content=system_prompt)
        messages = [system_message] + state["messages"][:N_MESSAGES]

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
    tools.append(FileEditTool(view_in_shell=True))

    # Return all tools
    return tools


async def create_agent(
    model: str,
    api_key: str,
    provider: APIProvider,
    temperature: float = 0.7,
    max_tokens: int = 4096,
):
    """Create a LangChain agent with the configured tools."""
    if provider == APIProvider.ANTHROPIC:
        headers = {
            "anthropic-beta": f"{COMPUTER_USE_BETA_FLAG},{PROMPT_CACHING_BETA_FLAG}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        llm = ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=api_key,
            timeout=30,  # Add 30-second timeout
            model_kwargs={
                "extra_headers": {
                    "anthropic-beta": f"{COMPUTER_USE_BETA_FLAG},{PROMPT_CACHING_BETA_FLAG}"
                },
                "system": [
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            },
        )
    elif provider == APIProvider.OPENAI:
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=1024,
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


from vmpilot.prompt_cache import (
    add_cache_control,
    create_ephemeral_system_prompt,
    inject_prompt_caching,
)


async def process_messages(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: List[dict],
    output_callback: Callable[[Dict], None],
    tool_output_callback: Callable[[Any, str], None],
    api_key: str,
    max_tokens: int = 8192,
    temperature: float = 0.7,
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

    # Handle prompt caching for Anthropic provider
    if provider == APIProvider.ANTHROPIC:
        # Don't set system prompt in prompt_suffix since it's handled in model_kwargs
        prompt_suffix.set(None)
        # Just inject caching for message history
        inject_prompt_caching(messages)
    else:
        prompt_suffix.set(system_prompt_suffix)
    logger.debug("DEBUG: Creating agent")
    # Create agent
    agent = await create_agent(model, api_key, provider, temperature, max_tokens)
    logger.debug("DEBUG: Agent created successfully")

    # Convert messages to LangChain format
    formatted_messages = []
    try:
        for msg in messages:
            logger.debug(f"Processing message: {msg}")
            if msg["role"] == "user":
                if isinstance(msg["content"], str):
                    formatted_messages.append(
                        HumanMessage(content=msg["content"], additional_kwargs={})
                    )
                elif isinstance(msg["content"], list):
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
                                    additional_kwargs=(
                                        additional_kwargs if additional_kwargs else {}
                                    ),
                                )
                            )
            elif msg["role"] == "assistant":
                if isinstance(msg["content"], str):
                    formatted_messages.append(
                        AIMessage(
                            content=msg["content"],
                            additional_kwargs=(
                                {"cache_control": {"type": "ephemeral"}}
                                if provider == APIProvider.ANTHROPIC
                                else None
                            ),
                        )
                    )
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
                            AIMessage(
                                content="\n".join(content_parts),
                                additional_kwargs=(
                                    {"cache_control": {"type": "ephemeral"}}
                                    if provider == APIProvider.ANTHROPIC
                                    else None
                                ),
                            )
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
                        content = message.content

                        if isinstance(content, str):
                            # Skip if the content exactly matches the last user message
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
                                        output_callback(
                                            {
                                                "type": "tool_use",
                                                "name": item["name"],
                                                "input": item.get("input", {}),
                                            }
                                        )
                                        # Pass tool output back to agent
                                        tool_output_callback(
                                            {
                                                "output": item.get("output", ""),
                                                "error": None,
                                            },
                                            item["name"],
                                        )
                                else:
                                    logger.warning(
                                        f"Unknown content item type: {type(item)}"
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
                message = f"Error in agent stream: {str(e)}"
            output_callback({"type": "text", "text": f"{message}"})

    # Run the stream processor
    await process_stream()
    return messages