"""
LangChain-based implementation for VMPilot's core functionality.
Replaces the original loop.py with LangChain tools and agents.
"""

import logging
import os
from enum import StrEnum
from contextvars import ContextVar
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
# Set logging levels for specific loggers
logger = logging.getLogger(__name__)


from typing import Any, Callable, Dict, List
from datetime import datetime
import platform

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import FileManagementToolkit
from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.langchain_edit import FileEditTool
from vmpilot.config import Provider as APIProvider, config

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"

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

    # Our global system prompt
    system_prompt = SYSTEM_PROMPT
    # Append the suffix to the system prompt
    suffix = prompt_suffix.get()
    system_prompt = f"{system_prompt}\n\n{suffix}"

    messages = [SystemMessage(content=system_prompt)] + state["messages"][:N_MESSAGES]
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
        llm = ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=api_key,
            timeout=30,  # Add 30-second timeout
            model_kwargs={
                "extra_headers": {"anthropic-beta": COMPUTER_USE_BETA_FLAG},
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
                    formatted_messages.append(HumanMessage(content=msg["content"]))
                elif isinstance(msg["content"], list):
                    # Handle structured content
                    for item in msg["content"]:
                        if item["type"] == "text":
                            formatted_messages.append(
                                HumanMessage(content=item["text"])
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
