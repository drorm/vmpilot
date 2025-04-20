"""
LangChain-based implementation for VMPilot's agent functionality.
"""

import logging
import traceback
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from pydantic import SecretStr as PydanticSecretStr

from vmpilot.agent_logging import log_conversation_messages
from vmpilot.agent_memory import (
    clear_conversation_state,
    get_conversation_state,
    save_conversation_state,
)
from vmpilot.caching.chat_models import ChatAnthropic
from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config, current_provider, prompt_suffix
from vmpilot.exchange import Exchange
from vmpilot.init_agent import create_agent
from vmpilot.prompt import get_system_prompt
from vmpilot.request import send_request
from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.create_file import CreateFileTool
from vmpilot.tools.edit_tool import EditTool
from vmpilot.tools.setup_tools import setup_tools
from vmpilot.usage import Usage

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
    recursion_limit: int | None = None,  # Maximum number of steps to run in the request
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

    logger.info(f"Setting current provider to {provider}")
    # Set prompt suffix and provider
    prompt_suffix.set(system_prompt_suffix)
    current_provider.set(provider)

    # Create or retrieve Chat object to handle conversation state
    from .chat import Chat

    # Create Chat object to manage conversation state
    try:
        chat = Chat(
            messages=messages,
            output_callback=output_callback,
            system_prompt_suffix=system_prompt_suffix,
        )
        logger.debug(f"Using chat_id: {chat.chat_id}")

        # Check if project structure is invalid and user needs to make a choice
        if hasattr(chat, "done") and chat.done is True:
            logger.info(
                "Project structure is invalid. Ending chat to allow user to choose an option."
            )
            # Add a placeholder assistant message to ensure proper display
            if output_callback:
                # Message already sent through the chat output callback
                pass
            # Return early with just the existing messages
            return messages

    except Exception as e:
        logger.error(f"Error creating Chat object: {e}")
        raise

    # Create an Exchange object to track this user-LLM interaction with Git tracking
    user_message = messages[-1] if messages else {"role": "user", "content": ""}
    exchange = Exchange(
        chat_id=chat.chat_id,  # Use the chat_id directly from the Chat object
        user_message=user_message,
        output_callback=output_callback,
    )

    # Initialize usage tracking for this exchange with the current provider
    usage = Usage(provider=provider)

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

            # Log empty usage since we're exiting early
            logger.info(
                "TOTAL_TOKEN_USAGE: {'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0, 'input_tokens': 0, 'output_tokens': 0}"
            )

            # Return early with just the error message
            return messages + [
                {"role": "assistant", "content": error_message}
            ]  # Convert to dict format
        # For other actions (stash), continue processing

    # Handle prompt caching for Anthropic provider

    logger.debug("DEBUG: Creating agent")
    # Create agent
    agent = await create_agent(
        model, api_key, provider, system_prompt_suffix, temperature, max_tokens
    )

    # for openai and google preprend the system prompt
    if provider == APIProvider.GOOGLE or provider == APIProvider.OPENAI:
        # Prepend system prompt to messages for OpenAI
        system_prompt = get_system_prompt() + (
            "\n\n" + system_prompt_suffix if system_prompt_suffix else ""
        )
        messages.insert(
            0,
            {
                "role": "assistant",
                "content": system_prompt,
            },
        )  # type: ignore  # Ignoring list item type issue

    logger.debug("DEBUG: Agent created successfully")

    # Check if we have a previous conversation state for this chat session
    formatted_messages = []
    cache_info = {}

    # Determine if this is a new chat session by checking the conversation state
    previous_messages, previous_cache_info = get_conversation_state(chat.chat_id)

    # If there are no previous messages OR this is explicitly a new chat (len <= 2)
    # then we treat it as a new chat session
    is_new_chat = (not previous_messages) or len(messages) <= 2

    if is_new_chat:
        # For new chats, clear any existing conversation state
        clear_conversation_state(chat.chat_id)
        logger.debug(f"Started new chat session with chat_id: {chat.chat_id}")
    else:
        # This is a continuing chat, use the previous conversation state
        logger.info(
            f"Retrieved previous conversation state with {len(previous_messages)} messages for chat_id: {chat.chat_id}"
        )
        formatted_messages.extend(previous_messages)
        cache_info = previous_cache_info
        # Use the Chat class to determine if we should truncate messages
        if messages:
            # Let the Chat class handle message truncation
            messages = chat.get_formatted_messages(messages)
            logger.debug(f"Using formatted messages from Chat: {messages}")

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
    logger.debug(
        f"Starting agent stream with {len(formatted_messages)} messages and chat_id: {chat.chat_id}"
    )

    """Send the request and process the stream of messages from the agent."""

    # Store the latest response for saving the conversation state later
    response = {"messages": formatted_messages}
    # Track tool calls for the Exchange

    # Run the stream processor
    response, collected_tool_calls = await send_request(
        agent,
        chat,
        exchange,
        recursion_limit,
        formatted_messages,
        output_callback,
        tool_output_callback,
        usage,
    )

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

            # Save the full conversation state to ensure all messages are preserved
            save_conversation_state(chat.chat_id, response["messages"], cache_info)
            logger.debug(
                f"Saved complete conversation state with {len(response['messages'])} messages for chat_id: {chat.chat_id}"
            )

            # Log exchange summary
            exchange_summary = exchange.get_exchange_summary()
            logger.debug(f"Exchange completed: {exchange_summary}")

            # If changes were committed, log the commit message
            if exchange_summary.get("git_changes_committed"):
                logger.info("Git changes committed successfully")
    else:
        # In case of error or no response, still try to save what we have
        exchange.complete(AIMessage(content="Error occurred during processing"), [])

    # Log the total token usage and cost for this exchange
    total_usage, cost = usage.get_cost_summary()

    # Get cost message from usage module - it will handle display settings internally
    cost_message = usage.get_cost_message()
    if cost_message:  # Only output if there's a message to display
        logger.debug(cost_message)
        # append cost message to the Messages
        output_callback({"type": "text", "text": cost_message})

    return messages
