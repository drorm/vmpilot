import logging
import traceback

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig

from .agent_logging import log_message_content, log_message_received

logging.basicConfig(level=logging.INFO)
# Set logging levels for specific loggers
logger = logging.getLogger(__name__)


from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from langchain_core.runnables import Runnable


def log_token_usage(message: Any) -> None:
    """Log token usage and related metadata"""
    response_metadata = getattr(message, "response_metadata", {})
    usage = response_metadata.get("usage", {})

    # if there's no usage data, return
    if not usage:
        return

    # Log token usage in single line format
    logger.info(
        "TOKEN_USAGE: {'cache_creation_input_tokens': %d, 'cache_read_input_tokens': %d, 'input_tokens': %d, 'output_tokens': %d}",
        usage.get("cache_creation_input_tokens", 0),
        usage.get("cache_read_input_tokens", 0),
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
    )


async def send_request(
    agent: Runnable,
    chat: Any,
    exchange: Any,
    recursion_limit: int,
    formatted_messages: List[Union[HumanMessage, AIMessage]],
    output_callback: Callable[[Dict[str, Any]], None],
    tool_output_callback: Callable[[Dict[str, Any], str], None],
    usage: Any,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, str]]]:
    collected_tool_calls = []
    response = None  # Initialize response variable
    try:
        async for agent_response in agent.astream(
            {"messages": formatted_messages},
            config=RunnableConfig(
                recursion_limit=recursion_limit,
                configurable={
                    "thread_id": chat.chat_id,  # Use the chat_id directly from the Chat object
                    "run_name": f"vmpilot-run-{chat.chat_id}",
                },
            ),
            stream_mode="values",
        ):
            logger.debug(f"Got response: {agent_response}")
            try:

                """Process the messages from the agent."""
                # Handle different response types
                if "messages" in agent_response:
                    message = agent_response["messages"][-1]

                    # Log message receipt and usage for all message types
                    log_message_received(message)
                    log_token_usage(message)

                    # Add tokens to usage tracker
                    usage.add_tokens(message)

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
                        tool_result = {
                            "output": (
                                message.content if message.content is not None else ""
                            ),
                            "error": None,
                        }
                        tool_output_callback(
                            tool_result,
                            (
                                message.name
                                if message.name is not None
                                else "unknown_tool"
                            ),
                        )

                        # Track tool call for Exchange
                        collected_tool_calls.append(
                            {
                                "name": message.name,
                                "content": (
                                    message.content
                                    if message.content is not None
                                    else ""
                                ),
                            }
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
                                and isinstance(content, str)
                                and content.strip()
                                == (
                                    formatted_messages[-1].content.strip()
                                    if isinstance(formatted_messages[-1].content, str)
                                    else str(formatted_messages[-1].content)
                                )
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
        # Make sure response is properly initialized before returning
        if not "response" in locals():
            response = None
        return (response, collected_tool_calls)
    except Exception as e:  # pragma: no cover
        from langchain_core.messages import AIMessage, HumanMessage

        error_message = str(e)
        message = ""
        if "Recursion limit" in error_message and "reached" in error_message:
            message = f" I've done {recursion_limit} steps in a row. Type *continue* if you'd like me to keep going."
            logger.info(message)
            return (
                # pyright: ignore
                response,
                collected_tool_calls,
            )  # This is not a real error, just a limit, so we treat it as a normal response
        # Handle specific tool_use/tool_result error
        elif "Request timed out" in error_message:
            logger.error(f"Request timed out: {e}")
            message = f"Request timed out: {str(e)}"
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
            logger.debug(f"messages: {formatted_messages}")
            message = f"Error in agent stream: {str(e)}"

        # Complete the Exchange with error information
        error_content = f"Error occurred: {message}"
        exchange.complete(AIMessage(content=error_content), collected_tool_calls)

        output_callback({"type": "text", "text": f"{message}"})

        # Return a tuple to match the function's return type
        return (None, collected_tool_calls)
