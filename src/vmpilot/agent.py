"""
LangChain-based implementation for VMPilot's agent functionality.
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

from vmpilot.agent_logging import log_conversation_messages
from vmpilot.agent_memory import (
    clear_conversation_state,
    get_conversation_state,
    save_conversation_state,
    update_cache_info,
)
from vmpilot.caching.chat_models import ChatAnthropic
from vmpilot.config import MAX_TOKENS, TEMPERATURE, GitConfig
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config
from vmpilot.exchange import Exchange
from vmpilot.prompt import SYSTEM_PROMPT
from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.create_file import CreateFileTool
from vmpilot.tools.edit_tool import EditTool

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

    # Handle system prompt with potential cache control
    prompt_suffix.get()
    messages = state["messages"]

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
    log_conversation_messages(messages, level="debug")
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
        # Only set temperature=1 for o3-mini model
        provider_config = config.get_provider_config(APIProvider.OPENAI)
        model_temperature = 1 if model == "o3-mini" else temperature
        llm = ChatOpenAI(
            model=model,
            temperature=model_temperature,
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
Process user's message through the agent and handle outputs
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
    thread_id: str = None,  # Chat ID for conversation state management
) -> List[dict]:
    """Process messages through the agent and handle outputs.

    Args:
        model: The LLM model to use
        provider: The API provider (OpenAI/Anthropic)
        system_prompt_suffix: Additional text to append to the system prompt
        messages: List of messages to process
        output_callback: Function to call with output chunks
        tool_output_callback: Function to call with tool outputs
        api_key: API key for the provider
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        disable_logging: Whether to disable detailed logging
        recursion_limit: Maximum number of steps to run in the request
        thread_id: Chat ID for conversation state management

    Returns:
        List of processed messages
    """
    logger.debug(
        f"------------- Processing new message: model={model}, provider={provider} --------------- "
    )
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
    # Create an Exchange object to track this user-LLM interaction with Git tracking
    user_message = messages[-1] if messages else {"role": "user", "content": ""}
    exchange = Exchange(
        chat_id=thread_id,
        user_message=user_message,
        output_callback=output_callback,
    )

    # Check Git repository status and handle dirty_repo_action
    if not exchange.check_git_status():
        logger.debug("Git repository has uncommitted changes before LLM operation")

        # Check if we should stop processing based on dirty_repo_action config
        if config.git_config.dirty_repo_action.lower() == "stop":
            # Return a message to the user instead of processing with the LLM
            error_message = "Sorry, the git repository has unsaved changes and the config is set to: *dirty_repo_action = stop*.\n I cannot make any changes."
            # Call output callback with the error message
            output_callback({"type": "text", "text": error_message})
            logger.warning(
                "Dirty repo and dirty_repo_action is set to stop. Stop processing."
            )

            # Return early with just the error message
            return messages + [error_message]
        # For other actions (stash), continue processing

    # Handle prompt caching for Anthropic provider

    logger.debug("DEBUG: Creating agent")
    # Create agent
    agent = await create_agent(
        model, api_key, provider, system_prompt_suffix, temperature, max_tokens
    )

    if provider == APIProvider.OPENAI:
        # Prepend system prompt to messages for OpenAI
        system_prompt = SYSTEM_PROMPT + (
            "\n\n" + system_prompt_suffix if system_prompt_suffix else ""
        )
        messages.insert(
            0,
            {
                "role": "assistant",
                "content": system_prompt,
            },
        )

    logger.debug("DEBUG: Agent created successfully")

    # Check if we have a previous conversation state for this thread_id
    formatted_messages = []
    cache_info = {}
    if thread_id is not None:
        # Determine if this is a new chat session by checking the conversation state first
        previous_messages, previous_cache_info = get_conversation_state(thread_id)

        # If there are no previous messages OR this is explicitly a new chat (len <= 2)
        # then we treat it as a new chat session
        is_new_chat = (not previous_messages) or len(messages) <= 2

        if is_new_chat:
            # For new chats, clear any existing conversation state with this thread_id
            clear_conversation_state(thread_id)
            logger.info(f"Started new chat session with thread_id: {thread_id}")
        else:
            # This is a continuing chat, use the previous conversation state
            logger.info(
                f"Retrieved previous conversation state with {len(previous_messages)} messages for thread_id: {thread_id}"
            )
            formatted_messages.extend(previous_messages)
            cache_info = previous_cache_info
            # If we have previous messages, we only need to process the last message from the current request
            if messages:
                messages = [messages[-1]]
                logger.debug(
                    f"Using only the last message from current request: {messages}"
                )

    # Convert messages from openai to LangChain format
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
    if thread_id is None:
        thread_id = f"vmpilot-{os.getpid()}"
    logger.debug(
        f"Starting agent stream with {len(formatted_messages)} messages and thread_id: {thread_id}"
    )

    """Send the request and process the stream of messages from the agent."""

    # Store the latest response for saving the conversation state later
    response = {"messages": formatted_messages}
    # Track tool calls for the Exchange
    collected_tool_calls = []

    async def send_request():
        nonlocal response, collected_tool_calls
        try:
            async for agent_response in agent.astream(
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
                    if "messages" in agent_response:
                        message = agent_response["messages"][-1]

                        # Log message receipt and usage for all message types
                        log_message_received(message)
                        log_token_usage(message, "info")

                        from langchain_core.messages import (
                            AIMessage,
                            HumanMessage,
                            ToolMessage,
                        )

                        # Update our response object with the latest state
                        response = agent_response

                        # log_conversation_messages(response["messages"], level="info")
                        if isinstance(message, ToolMessage):
                            logger.debug(f"isinstance message: {message}")
                            # Handle tool message responses
                            tool_result = {"output": message.content, "error": None}
                            tool_output_callback(tool_result, message.name)

                            # Track tool call for Exchange
                            collected_tool_calls.append(
                                {"name": message.name, "content": message.content}
                            )

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

                                                # Track tool call for Exchange
                                                collected_tool_calls.append(
                                                    {
                                                        "name": item["name"],
                                                        "content": item["output"],
                                                    }
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
                message = f" I've done {recursion_limit} steps in a row. Type *continue* if you'd like me to keep going."
                logger.info(message)
            # Handle specific tool_use/tool_result error
            elif (
                "Messages containing `tool_use` blocks must be followed by a user message with `tool_result` blocks"
                in error_message
            ):
                logger.error(f"Tool use/result sequence error: {e}")
                message = f"I got the error: {str(e)}."
                logger.error(f"last message: {formatted_messages[-1]}")
            else:
                logger.error(f"Error in agent stream: {e}")
                logger.error("".join(traceback.format_tb(e.__traceback__)))
                logger.error(f"messages: {formatted_messages}")
                message = f"Error in agent stream: {str(e)}"

            # Complete the Exchange with error information
            error_content = f"Error occurred: {message}"
            exchange.complete(AIMessage(content=error_content), collected_tool_calls)

            output_callback({"type": "text", "text": f"{message}"})

    # Run the stream processor
    await send_request()

    # Complete the Exchange with the assistant's response and tool calls
    if response and "messages" in response:
        # Get the assistant's response message (last AI message)
        assistant_messages = [
            msg for msg in response["messages"] if isinstance(msg, AIMessage)
        ]
        if assistant_messages:
            assistant_message = assistant_messages[-1]

            # Complete the exchange with collected tool calls and commit any changes
            exchange.complete(assistant_message, collected_tool_calls)

            # Log exchange summary
            exchange_summary = exchange.get_exchange_summary()
            logger.debug(f"Exchange completed: {exchange_summary}")

            # If changes were committed, log the commit message
            if exchange_summary.get("git_changes_committed"):
                logger.info("Git changes committed successfully")
        else:
            # If no AI messages found but we have a response, use the last message
            last_message = response["messages"][-1] if response["messages"] else None
            if last_message:
                # Convert to AIMessage if it's not already
                if not isinstance(last_message, AIMessage):
                    assistant_message = AIMessage(
                        content=(
                            str(last_message.content)
                            if hasattr(last_message, "content")
                            else ""
                        )
                    )
                else:
                    assistant_message = last_message
                exchange.complete(assistant_message, collected_tool_calls)
            else:
                # Fallback if no messages at all
                exchange.complete(
                    AIMessage(content="No response generated"), collected_tool_calls
                )
    else:
        # In case of error or no response, still try to save what we have
        exchange.complete(AIMessage(content="Error occurred during processing"), [])

    return messages
