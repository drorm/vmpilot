"""
LangChain-based implementation for VMPilot's agent functionality.
Replaces the original loop.py from Claude Computer Use with LangChain tools and agents.
"""

import logging
import os
import pathlib
import traceback
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

from vmpilot.caching.chat_models import ChatAnthropic
from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config
from vmpilot.prompt import SYSTEM_PROMPT
from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.create_file import CreateFileTool
from vmpilot.tools.edit_tool import EditTool
from vmpilot.tools.google_search_tool import GoogleSearchTool

# Configure logging
from .agent_logging import (
    log_message_content,
    log_message_processing,
    log_message_received,
    log_token_usage,
)

logging.basicConfig(level=logging.INFO)
# Set logging levels for specific loggers
logger = logging.getLogger(__name__)


# Flag to enable beta features in Anthropic API
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

# The system prompt that's passed on from webui.
prompt_suffix: ContextVar[Optional[Any]] = ContextVar("prompt_suffix", default=None)
# The current provider (Anthropic/OpenAI)
current_provider: ContextVar[Optional[APIProvider]] = ContextVar(
    "current_provider", default=None
)


"""
method to modify the state messages
Called by the agent to modify the messages generated by the agent
"""


def _modify_state_messages(state: AgentState):
    # Keep the last N messages in the state as well as the system prompt
    N_MESSAGES = 30  # TODO: Change this to a config value

    # Handle system prompt with potential cache control
    prompt_suffix.get()
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


"""Initialize and configure the tools we use as described in the prompt."""


def setup_tools(llm=None):
    # Suppress warning about shell tool safeguards
    import warnings

    warnings.filterwarnings(
        "ignore", category=UserWarning, module="langchain_community.tools.shell.tool"
    )

    tools = []

    if llm is not None:
        try:
            shell_tool = SetupShellTool(llm=llm)
            tools.append(shell_tool)
            tools.append(EditTool())  # for editing
            tools.append(CreateFileTool())  # for creating files
            tools.append(GoogleSearchTool())  # for searching
        except Exception as e:
            logger.error(f"Error: Error creating tool: {e}")
            logger.error("".join(traceback.format_tb(e.__traceback__)))

    # Return all tools
    return tools


"""
Create the langchain agent. The agent is in charge of the loop:
1. User request.
2. LLM response.
2. LLM invokation of one or more tools.
3. Sending the tool result to the LLM.
4. Rinse repeat until the llm decides it's done or we hit a recursion limit.
5. Detect when the llm is done.
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
        """We're jumping through hoops here to get the Anthropic caching to work correctly."""
        provider_config = config.get_provider_config(APIProvider.ANTHROPIC)
        if provider_config.beta_flags:
            betas.extend([flag for flag in provider_config.beta_flags.keys()])

        {
            "anthropic-beta": ",".join(betas),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system_content = {
            "type": "text",
            "text": SYSTEM_PROMPT
            + ("\n\n" + system_prompt_suffix if system_prompt_suffix else ""),
        }
        logger.debug(f"System prompt: {system_content}")

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
    recursion_limit: int = None,  # Maximum number of steps to run in the request
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

    logger.debug("DEBUG: Creating agent")
    # Create agent
    agent = await create_agent(
        model, api_key, provider, system_prompt_suffix, temperature, max_tokens
    )
    logger.debug("DEBUG: Agent created successfully")

    # Convert messages from openai to LangChain format
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
                    logger.debug("Processing list of messages")
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

    """Send the request and process the stream of messages from the agent."""

    async def send_request():
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

                    """Process the messages from the agent."""
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
                            tool_result = {"output": message.content, "error": None}
                            tool_output_callback(tool_result, message.name)

                        elif isinstance(message, AIMessage):
                            """Handle AI message responses"""
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
                logger.error(f"messages: {formatted_messages}")
                message = f"Error in agent stream: {str(e)}"
            output_callback({"type": "text", "text": f"{message}"})

    # Run the stream processor
    await send_request()
    return messages
