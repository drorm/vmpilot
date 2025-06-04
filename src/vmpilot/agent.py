"""
Agent implementation
Provides a simple agent loop with tool support using LiteLLM.
"""

import json
import logging
import traceback
from typing import Any, Dict, Generator, List, Optional

# Import Chat class
from vmpilot.chat import Chat
from vmpilot.config import MAX_TOKENS, TEMPERATURE, TOOL_OUTPUT_LINES
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config, current_provider, prompt_suffix
from vmpilot.exchange import Exchange
from vmpilot.init_agent import create_agent, modify_state_messages
from vmpilot.tools.setup_tools import get_tool_schemas, setup_tools
from vmpilot.unified_memory import (
    clear_conversation_state,
    get_conversation_state,
    save_conversation_state,
)
from vmpilot.usage import Usage

# Configure logging
logger = logging.getLogger(__name__)

# Suppress LiteLLM info/debug logs
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def parse_tool_calls(response) -> tuple:
    """
    Extract tool calls and content from the LLM response.

    Returns:
        tuple: (tool_calls, content) where content is the text message if present
    """
    tool_calls = []
    content = None

    try:
        # Extract tool calls from the response
        if hasattr(response, "choices") and len(response.choices) > 0:
            message = response.choices[0].message
        else:
            return tool_calls, content

        # Get content if available
        if hasattr(message, "content") and message.content:
            content = message.content

        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                # Parse arguments from JSON string to dict
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {"error": "Failed to parse arguments"}

                tool_calls.append(
                    {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": arguments,
                    }
                )
    except Exception as e:
        logger.error(f"Error parsing tool calls: {str(e)}")

    return tool_calls, content


import asyncio


def truncate_tool_output_for_ui(result):
    """
    Truncate tool output for UI display based on TOOL_OUTPUT_LINES config.
    This replicates the logic from the old tool_callback function.
    """
    outputs = []
    if isinstance(result, dict):
        if "error" in result and result["error"]:
            outputs.append(result["error"])
        if "output" in result and result["output"]:
            outputs.append(result["output"])
    elif hasattr(result, "error") and result.error:
        if hasattr(result, "exit_code") and result.exit_code:
            outputs.append(f"Exit code: {result.exit_code}")
        outputs.append(result.error)
    else:
        outputs.append(str(result))

    truncated_outputs = []
    for output in outputs:
        output_lines = str(output).splitlines()
        truncated_output = "\n".join(output_lines[:TOOL_OUTPUT_LINES])
        if len(output_lines) > (TOOL_OUTPUT_LINES + 1):
            truncated_output += f"\n...\n````\n(and {len(output_lines) - TOOL_OUTPUT_LINES} more lines)\n"
        else:
            truncated_output += "\n"
        truncated_outputs.append(truncated_output)

    return "".join(truncated_outputs)


async def process_messages(
    model,
    provider,
    system_prompt_suffix,
    messages,
    output_callback,
    tool_output_callback,
    api_key,
    max_tokens=MAX_TOKENS,
    temperature=TEMPERATURE,
    disable_logging=False,
    recursion_limit=None,
):
    """
    Coroutine for LiteLLM agent: processes messages, streams LLM and tool responses via output/tool callbacks.
    Accepts the same signature as the original for compatibility.
    """
    # Get recursion limit from config if not explicitly set
    if recursion_limit is None:
        provider_config = config.get_provider_config(provider)
        recursion_limit = provider_config.recursion_limit

    # Handle logging configuration
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if disable_logging:
        # Disable all logging if flag is set
        logging.getLogger("vmpilot").setLevel(logging.INFO)
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("httpcore").setLevel(logging.ERROR)
        logging.getLogger("asyncio").setLevel(logging.ERROR)
        logger.setLevel(logging.ERROR)

    # Set prompt suffix and provider context variables
    prompt_suffix.set(system_prompt_suffix)
    current_provider.set(provider)

    # Use create_agent to get provider-specific configuration
    agent_config = await create_agent(
        model=model,
        api_key=api_key,
        provider=provider,
        system_prompt_suffix=system_prompt_suffix,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    system_prompt = agent_config["system_prompt"]

    # Compose user input (last user message)
    user_input = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_input = msg.get("content", "")
            break
    user_message = {"role": "user", "content": user_input}

    # Set up tools using the standard setup_tools function
    tools = setup_tools(
        model=model
    )  # This returns a list of tool dictionaries, including their schemas and executors

    # Create Chat object to manage conversation state
    # This is a simplified version for lllm, focusing on message formatting for now
    # Full chat persistence, project checks etc. are not yet integrated here.
    try:
        chat = Chat(
            messages=messages,  # Original messages list
            output_callback=output_callback,  # Pass for potential chat_id announcement
            system_prompt_suffix=system_prompt_suffix,  # Pass for potential project dir extraction
        )
        logger.debug(f"LiteLLM agent using chat_id: {chat.chat_id}")

        # If chat.done is True, it means Project found an issue and sent a message.
        # We should stop further processing in lllm/agent.py similar to original agent.py
        if hasattr(chat, "done") and chat.done is True:
            logger.info(
                "Project structure is invalid (detected by Chat object). Ending lllm agent processing."
            )
            # The message to the user was already sent by the Chat/Project object via output_callback.
            # No need to send another message here. Just return.
            return  # Stop processing

    except Exception as e:
        logger.error(f"Error creating Chat object in lllm.agent: {e}")
        # We might want to yield an error message or re-raise depending on desired behavior
        if output_callback:
            output_callback(
                {"type": "text", "text": f"Error initializing chat: {str(e)}"}
            )
        raise  # Re-raise for now, as this is a fundamental part

    # load conversation state --
    if chat and hasattr(chat, "chat_id"):
        chat_id = chat.chat_id
    else:
        chat_id = None
    thread_id = str(chat_id) if chat_id is not None else ""
    previous_messages, previous_cache_info = get_conversation_state(thread_id)

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

    # Create an Exchange object to track this user-LLM interaction with Git tracking
    exchange = Exchange(
        chat_id=chat.chat_id,  # Use the chat_id directly from the Chat object
        user_message=user_message,
        output_callback=output_callback,
    )
    logger.debug(f"Exchange created for chat_id: {chat.chat_id}")

    # Initialize usage tracking for this exchange with the current provider
    usage = Usage(provider=provider)

    if previous_messages:
        messages = previous_messages
        # and append the new user user_input
        messages.append(user_message)
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
    cache_info = previous_cache_info or {}
    logger.debug(f"Messages for agent loop: {messages}")

    # The lllm agent_loop expects a list of messages in OpenAI format.
    # Call agent_loop and stream outputs through the correct callback
    try:
        # agent_loop now uses MAX_TOKENS, TEMPERATURE, and current_provider.api_key from config
        for item in agent_loop(
            user_input=user_input,  # Still needed for the first turn in agent_loop's internal history
            messages=messages,  # Pass original messages for context if needed by agent_loop
            chat_object=chat,  # Pass the chat object for potential future use or context
            system_prompt=system_prompt,  # Now using the dynamically constructed prompt
            tools=tools,
            model=model,  # model is passed correctly
            exchange=exchange,  # Pass exchange for tracking
            usage=usage,  # Pass usage for token tracking
            agent_config=agent_config,  # Pass the full agent configuration
            recursion_limit=recursion_limit,  # Pass recursion limit
        ):
            # Heuristic: if item looks like tool output, call tool_output_callback; else output_callback
            if isinstance(item, dict) and ("output" in item or "error" in item):
                if tool_output_callback:
                    tool_output_callback(item, None)
            else:
                if output_callback:
                    output_callback({"type": "text", "text": item})
            await asyncio.sleep(0)  # Yield control to event loop for streaming

        # After agent loop completes, handle usage tracking and cost display
        if usage:
            # Store usage in database
            _, costs = usage.get_cost_summary()
            usage.store_cost_in_db(
                chat_id=chat.chat_id,
                model=usage.model_name or model,
                request=user_input,
                cost=costs,
                start=exchange.started_at.isoformat() if exchange else "",
                end=(
                    exchange.completed_at.isoformat()
                    if exchange and exchange.completed_at
                    else ""
                ),
            )

            # Display cost information if enabled
            cost_message = usage.get_cost_message(chat.chat_id)
            if cost_message:
                if output_callback:
                    output_callback({"type": "text", "text": cost_message})

    except Exception as e:
        if output_callback:
            output_callback({"type": "text", "text": f"Error: {str(e)}"})
        raise
    # Save conversation state after every assistant message
    if chat and hasattr(chat, "chat_id"):
        save_conversation_state(chat.chat_id, messages, cache_info)
        logger.debug(f"Saved conversation state for chat_id: {chat.chat_id}")


def agent_loop(
    user_input: str,
    system_prompt: str,
    tools: List[Dict[str, Any]],
    model: str = "gpt-4o",
    messages: Optional[List[Dict[str, Any]]] = None,  # Added
    chat_object: Optional[Any] = Chat,
    exchange: Optional[Exchange] = None,
    usage: Optional[Usage] = None,
    agent_config: Optional[Dict[str, Any]] = None,
    recursion_limit: Optional[int] = None,
) -> Generator[str, None, None]:
    """
    Simple agent loop that processes user input, sends it to the LLM,
    executes tools when requested, and yields responses and tool outputs as they are generated.
    """
    messages = messages or []

    # API key, provider, max_tokens, and temperature are now sourced from config.py
    # (current_provider.api_key, current_provider.name, MAX_TOKENS, TEMPERATURE)
    # The 'model' variable is passed as an argument to this function.
    # The 'api_key' for litellm.completion will use current_provider.api_key.

    # Main agent loop
    max_iterations = recursion_limit or 20  # Use recursion_limit or default to 20
    iteration = 0
    all_tool_calls = []  # Track all tool calls for exchange completion

    while iteration < max_iterations:
        iteration += 1
        logger.debug(f"Agent loop iteration {iteration}")

        try:
            # Apply modify_state_messages for cache control (Anthropic)
            modified_messages = modify_state_messages(messages.copy())
            logger.debug(
                f"Modified messages for iteration {iteration}: {modified_messages}"
            )

            # Call LLM via LiteLLM
            # Extract just the schema part for LiteLLM
            # Use model from agent_config if available (includes proper prefixes like gemini/)
            # otherwise fall back to the model parameter
            effective_model = (
                agent_config.get("model") if agent_config else None
            ) or model

            tool_schemas = get_tool_schemas(tools, effective_model)
            # Debug logging
            logger.debug(
                f"Using tools: {[t.get('schema', {}).get('function', {}).get('name') for t in tools]}"
            )
            logger.debug(f"Using effective model: {effective_model}")

            # Prepare completion parameters
            completion_params = {
                "model": effective_model,
                "messages": modified_messages,
                "tools": tool_schemas,  # Pass only the schemas
                "temperature": TEMPERATURE,  # This is a float, not a ContextVar
                "api_key": (
                    agent_config.get("api_key")
                    if agent_config
                    else config.get_api_key(current_provider.get())
                ),  # Use agent_config api_key if available, otherwise fallback
                "max_tokens": MAX_TOKENS,  # This is an int, not a ContextVar
            }

            # Add provider-specific parameters from agent_config
            if agent_config:
                provider = agent_config.get("provider")
                if provider == APIProvider.ANTHROPIC:
                    # Handle Anthropic-specific parameters
                    if "anthropic_system_content" in agent_config:
                        # For Anthropic, replace system message with structured content
                        anthropic_messages = []
                        for msg in modified_messages:
                            if msg.get("role") == "system":
                                continue  # Skip system messages in messages array
                            anthropic_messages.append(msg)
                        completion_params["messages"] = anthropic_messages
                        completion_params["system"] = agent_config[
                            "anthropic_system_content"
                        ]

                    if "anthropic_extra_headers" in agent_config:
                        completion_params["extra_headers"] = agent_config[
                            "anthropic_extra_headers"
                        ]

            import litellm

            response = litellm.completion(**completion_params)

            # Track usage from the response if usage tracking is enabled
            if usage:
                # LiteLLM response structure is different - need to convert to expected format
                usage_data = getattr(response, "usage", None)
                if usage_data is not None:
                    # Create a mock message object with usage metadata for the Usage class
                    class MockMessage:
                        def __init__(self, usage_data, model_name):
                            self.usage_metadata = {
                                "input_tokens": usage_data.prompt_tokens,
                                "output_tokens": usage_data.completion_tokens,
                                "cache_creation_input_tokens": getattr(
                                    usage_data, "cache_creation_input_tokens", 0
                                ),
                            }
                            # Handle completion_tokens_details if present
                            if hasattr(usage_data, "completion_tokens_details"):
                                details = usage_data.completion_tokens_details
                                if hasattr(details, "reasoning_tokens"):
                                    self.usage_metadata["reasoning_tokens"] = (
                                        details.reasoning_tokens
                                    )

                            # Handle prompt_tokens_details if present (for cached tokens)
                            if hasattr(usage_data, "prompt_tokens_details"):
                                details = usage_data.prompt_tokens_details
                                if hasattr(details, "cached_tokens"):
                                    self.usage_metadata["input_token_details"] = {
                                        "cache_read": details.cached_tokens
                                    }

                            self.response_metadata = {
                                "model_name": model_name,
                                "token_usage": {
                                    "prompt_tokens": usage_data.prompt_tokens,
                                    "completion_tokens": usage_data.completion_tokens,
                                    "total_tokens": usage_data.total_tokens,
                                    "cache_creation_input_tokens": getattr(
                                        usage_data, "cache_creation_input_tokens", 0
                                    ),
                                },
                            }
                            # Add prompt_tokens_details if available
                            if hasattr(usage_data, "prompt_tokens_details"):
                                self.response_metadata["token_usage"][
                                    "prompt_tokens_details"
                                ] = {
                                    "cached_tokens": getattr(
                                        usage_data.prompt_tokens_details,
                                        "cached_tokens",
                                        0,
                                    )
                                }

                    # Patch: .usage may not exist on all response types
                    usage_data = getattr(response, "usage", None)
                    if usage_data is not None:
                        mock_message = MockMessage(usage_data, model)
                        usage.add_tokens(mock_message)
                    else:
                        # Some streaming wrappers (CustomStreamWrapper) may keep usage as an attribute in .__dict__
                        if (
                            hasattr(response, "__dict__")
                            and "usage" in response.__dict__
                        ):
                            mock_message = MockMessage(
                                response.__dict__["usage"], model
                            )
                            usage.add_tokens(mock_message)

            # Parse tool calls and content from response
            tool_calls, content = parse_tool_calls(response)

            # Yield LLM's textual response if present
            if content:
                yield content

            # If no tool calls, we've reached the final response from the LLM for this turn
            if not tool_calls:
                # Add the final assistant message to history before completing
                choices = getattr(response, "choices", None)
                if choices and len(choices) > 0:
                    assistant_msg_obj = choices[0].message

                    # Create the assistant message for history
                    final_assistant_msg = {
                        "role": "assistant",
                        "content": (
                            str(assistant_msg_obj.content)
                            if assistant_msg_obj.content is not None
                            else None
                        ),
                    }

                    # Add to messages history
                    messages.append(final_assistant_msg)
                    logger.debug(
                        f"Added final assistant message to history: {final_assistant_msg}"
                    )

                # Complete the exchange with the final assistant message
                if exchange:
                    if choices and len(choices) > 0 and hasattr(choices[0], "message"):
                        assistant_message = choices[0].message
                        if hasattr(assistant_message, "__dict__"):
                            exchange.complete(vars(assistant_message), [])
                        else:
                            exchange.complete({"content": str(assistant_message)}, [])
                    else:
                        exchange.complete({}, [])

                # If there was no textual content, but the LLM didn't call a tool,
                # it might be an empty response or an implicit end of operation.
                # The original code had: final_response = content or response.choices[0].message.content
                # If content was None, but there was a message, yield that.
                # However, parse_tool_calls should already put message.content into `content`.
                # If content is still None and no tools, it's likely the end.
                if not content:
                    if choices and len(choices) > 0 and hasattr(choices[0], "message"):
                        message_content = getattr(choices[0].message, "content", None)
                        if message_content:
                            yield message_content
                return  # End of this agent interaction or loop

            # Append the assistant's message with tool calls to history
            choices = getattr(response, "choices", None)
            if choices and len(choices) > 0:
                assistant_msg_obj = choices[
                    0
                ].message  # This is a litellm.Message object
            else:
                continue  # Skip this iteration if no choices

            history_assistant_msg = {
                "role": assistant_msg_obj.role,
                "content": (
                    str(assistant_msg_obj.content)
                    if assistant_msg_obj.content is not None
                    else None
                ),
            }

            if (
                hasattr(assistant_msg_obj, "tool_calls")
                and assistant_msg_obj.tool_calls
            ):
                clean_tool_calls_for_history = []
                for tc_instance in assistant_msg_obj.tool_calls:
                    # tc_instance is expected to be litellm.types.CompletionMessageToolCall
                    # It should have .id, .type, .function (with .name, .arguments)
                    try:
                        # Ensure arguments is a string (JSON string)
                        func_args = tc_instance.function.arguments
                        if not isinstance(func_args, str):
                            logger.warning(
                                f"Tool call function arguments were not a string: {type(func_args)}. Converting to JSON string."
                            )
                            func_args = json.dumps(
                                func_args
                            )  # Should already be JSON string from LLM

                        clean_tool_calls_for_history.append(
                            {
                                "id": tc_instance.id,
                                "type": tc_instance.type,
                                "function": {
                                    "name": tc_instance.function.name,
                                    "arguments": func_args,
                                },
                            }
                        )
                    except AttributeError as e:
                        logger.warning(
                            f"Skipping tool call in history due to missing attributes: {tc_instance}, error: {e}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error processing tool call for history: {tc_instance}, error: {e}"
                        )

                if clean_tool_calls_for_history:  # Only add if list is not empty
                    history_assistant_msg["tool_calls"] = clean_tool_calls_for_history

            messages.append(history_assistant_msg)

            # Add tool calls to collection for exchange tracking
            all_tool_calls.extend(tool_calls)

            # Execute each tool call and add results to messages
            for (
                tool_call
            ) in (
                tool_calls
            ):  # tool_calls here is from parse_tool_calls(), a list of dicts
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                logger.debug(f"Executing tool: {tool_name}")
                tool_result_for_history = ""

                # General tool execution: find the tool by name and call its executor
                matched_tool = None
                for tool in tools:
                    schema = tool.get("schema")
                    logger.debug(f"Checking tool: {schema}")

                    # LiteLLM tool schemas have a standard format: {"type": "function", "function": {...}}
                    if isinstance(schema, dict):
                        if schema.get("type") == "function" and isinstance(
                            schema.get("function"), dict
                        ):
                            # Extract function name from the nested structure
                            schema_name = schema.get("function", {}).get("name")
                        else:
                            # Direct name extraction (old format)
                            schema_name = schema.get("name")
                    elif hasattr(schema, "name") and schema is not None:
                        schema_name = schema.name
                    else:
                        schema_name = None

                    logger.debug(f"Tool name from schema: {schema_name}")

                    if schema_name == tool_name:
                        matched_tool = tool
                        break
                if matched_tool is not None:
                    try:
                        # Optionally, special handling if you want to yield the command first for shell
                        if (
                            tool_name == "shell_tool" or tool_name == "shell"
                        ) and tool_args.get("command"):
                            yield f"\n\n**$ {tool_args['command']}**\n"

                        # Ensure the executor exists
                        if "executor" not in matched_tool:
                            error_msg = f"Error: Tool '{tool_name}' found but has no executor function"
                            logger.error(error_msg)
                            tool_result_for_history = error_msg
                            truncated_output = truncate_tool_output_for_ui(error_msg)
                            yield truncated_output
                        else:
                            tool_output = matched_tool["executor"](tool_args)
                            # Store full output for LLM/history
                            tool_result_for_history = (
                                tool_output
                                if isinstance(tool_output, str)
                                else str(tool_output)
                            )
                            # Yield truncated output for UI
                            truncated_output = truncate_tool_output_for_ui(tool_output)
                            yield truncated_output
                    except Exception as e:
                        error_msg = f"Error executing {tool_name} tool: {str(e)}"
                        logger.error(error_msg)
                        logger.error(traceback.format_exc())
                        tool_result_for_history = error_msg
                        truncated_output = truncate_tool_output_for_ui(error_msg)
                        yield truncated_output + "\n"
                else:
                    # List all available tools for debugging
                    available_tools = []
                    for t in tools:
                        schema = t.get("schema")
                        if isinstance(schema, dict):
                            if schema.get("type") == "function" and isinstance(
                                schema.get("function"), dict
                            ):
                                available_tools.append(
                                    schema.get("function", {}).get("name")
                                )
                            else:
                                available_tools.append(schema.get("name"))
                        elif hasattr(schema, "name") and schema is not None:
                            available_tools.append(schema.name)

                    error_msg = f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(available_tools) if available_tools else 'None'}"
                    logger.error(error_msg)
                    tool_result_for_history = error_msg
                    truncated_output = truncate_tool_output_for_ui(error_msg)
                    yield truncated_output + "\n"

                # Add the tool result to messages for the next LLM call
                logger.debug(
                    f"Adding tool result to messages: {tool_result_for_history}"
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": tool_result_for_history,  # Use the carefully prepared history entry
                        "tool_call_id": tool_call["id"],
                    }
                )
            # After processing all tool calls for this iteration, continue the loop
            # for the LLM to process the tool results.

        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}\n{traceback.format_exc()}")
            yield f"Error: {str(e)}"
            # Complete exchange with error if there's an exception
            if exchange:
                error_message = {"content": f"Error: {str(e)}", "role": "assistant"}
                exchange.complete(error_message, all_tool_calls)
            return

    notice = f'I\'ve done {max_iterations} steps. Type "continue" or "next" to continue. You can change this, recursion_limit, in config.ini.'
    # If we've reached max iterations, complete the exchange
    if exchange:
        error_message = {
            "content": notice,
            "role": "assistant",
        }
        logger.info(notice)
        exchange.complete(error_message, all_tool_calls)

    yield notice
