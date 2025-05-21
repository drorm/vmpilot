"""
Agent implementation for LiteLLM Migration MVP.
Provides a simple agent loop with tool support using LiteLLM.
"""

import json
import logging
import os
import queue
import threading
import traceback
from typing import Any, Dict, Generator, List, Optional

import litellm

# Import Chat class
from vmpilot.chat import Chat
from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config, current_provider, prompt_suffix

# Import shell tool from lllm implementation
from vmpilot.tools.setup_tools import setup_tools

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
        message = response.choices[0].message

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


async def process_messages(
    model,
    provider,
    system_prompt_suffix,
    messages,
    output_callback,
    tool_output_callback,
    api_key,
    max_tokens,
    temperature,
    disable_logging=False,
    recursion_limit=None,
):
    """
    Coroutine for LiteLLM agent: processes messages, streams LLM and tool responses via output/tool callbacks.
    Accepts the same signature as the original for compatibility.
    """
    # Import for dynamic system prompt
    from vmpilot.prompt import get_system_prompt

    # Compose system prompt
    base_system_prompt = get_system_prompt()
    final_system_prompt = base_system_prompt
    if prompt_suffix:  # From config.py
        final_system_prompt += f"\n\n{prompt_suffix}"
    if system_prompt_suffix:  # From argument
        final_system_prompt += f"\n\n{system_prompt_suffix}"

    system_prompt = final_system_prompt  # To be used by agent_loop

    # Compose user input (last user message)
    user_input = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_input = msg.get("content", "")
            break
    # Set up tools using the standard setup_tools function
    tools = (
        setup_tools()
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

    # Prepare messages for LiteLLM based on chat object's logic
    # The lllm agent_loop expects a list of messages in OpenAI format.
    # The original agent.py has complex logic for new vs. continued chats and memory.
    # For now, we'll use the chat object to get potentially truncated messages.
    # This part will need to align with how unified_memory is integrated later.

    # The current `messages` variable holds the input from the vmpilot.py level.
    # The `chat` object's `get_formatted_messages` can be used if we decide to truncate.
    # However, the existing `agent_loop` in lllm builds its own message history internally
    # starting from the initial system prompt and user_input.
    # For now, we will pass the *original* `messages` to `agent_loop` and let it manage its own history.
    # The `chat` object created above is mostly for `chat_id` and project checks at this stage.

    # Call agent_loop and stream outputs through the correct callback
    try:
        # agent_loop now uses MAX_TOKENS, TEMPERATURE, and current_provider.api_key from config
        for item in agent_loop(
            user_input=user_input,  # Still needed for the first turn in agent_loop's internal history
            initial_messages=messages,  # Pass original messages for context if needed by agent_loop
            chat_object=chat,  # Pass the chat object for potential future use or context
            system_prompt=system_prompt,  # Now using the dynamically constructed prompt
            tools=tools,
            model=model,  # model is passed correctly
        ):
            # Heuristic: if item looks like tool output, call tool_output_callback; else output_callback
            if isinstance(item, dict) and ("output" in item or "error" in item):
                if tool_output_callback:
                    tool_output_callback(item, None)
            else:
                if output_callback:
                    output_callback({"type": "text", "text": item})
            await asyncio.sleep(0)  # Yield control to event loop for streaming
    except Exception as e:
        if output_callback:
            output_callback({"type": "text", "text": f"Error: {str(e)}"})
        raise


def agent_loop(
    user_input: str,
    system_prompt: str,
    tools: List[Dict[str, Any]],
    model: str = "gpt-4o",
    initial_messages: Optional[List[Dict[str, Any]]] = None,  # Added
    chat_object: Optional[Any] = None,  # Added (using Any for now for Chat type)
) -> Generator[str, None, None]:
    """
    Simple agent loop that processes user input, sends it to the LLM,
    executes tools when requested, and yields responses and tool outputs as they are generated.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    # API key, provider, max_tokens, and temperature are now sourced from config.py
    # (current_provider.api_key, current_provider.name, MAX_TOKENS, TEMPERATURE)
    # The 'model' variable is passed as an argument to this function.
    # The 'api_key' for litellm.completion will use current_provider.api_key.

    # Main agent loop
    max_iterations = 20  # Safety limit to prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Agent loop iteration {iteration}")

        try:
            # Call LLM via LiteLLM
            # Extract just the schema part for LiteLLM
            tool_schemas = [t.get("schema") for t in tools]

            # Debug logging
            logger.info(
                f"Using tools: {[t.get('schema', {}).get('function', {}).get('name') for t in tools]}"
            )

            response = litellm.completion(
                model=model,
                messages=messages,
                tools=tool_schemas,  # Pass only the schemas
                temperature=TEMPERATURE,  # This is a float, not a ContextVar
                api_key=config.get_api_key(
                    current_provider.get()
                ),  # Fetch API key correctly
                max_tokens=MAX_TOKENS,  # This is an int, not a ContextVar
            )

            # Parse tool calls and content from response
            tool_calls, content = parse_tool_calls(response)

            # Yield LLM's textual response if present
            if content:
                yield content

            # If no tool calls, we've reached the final response from the LLM for this turn
            if not tool_calls:
                # If there was no textual content, but the LLM didn't call a tool,
                # it might be an empty response or an implicit end of operation.
                # The original code had: final_response = content or response.choices[0].message.content
                # If content was None, but there was a message, yield that.
                # However, parse_tool_calls should already put message.content into `content`.
                # If content is still None and no tools, it's likely the end.
                if (
                    not content and response.choices[0].message.content
                ):  # Ensure full message is out
                    yield response.choices[0].message.content
                return  # End of this agent interaction or loop

            # Append the assistant's message with tool calls to history
            assistant_msg_obj = response.choices[
                0
            ].message  # This is a litellm.Message object

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

            # Execute each tool call and add results to messages
            for (
                tool_call
            ) in (
                tool_calls
            ):  # tool_calls here is from parse_tool_calls(), a list of dicts
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                logger.info(f"Executing tool: {tool_name}")
                tool_result_for_history = ""

                # General tool execution: find the tool by name and call its executor
                matched_tool = None
                for tool in tools:
                    schema = tool.get("schema")
                    logger.info(f"Checking tool: {schema}")

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
                    elif hasattr(schema, "name"):
                        schema_name = schema.name
                    else:
                        schema_name = None

                    logger.info(f"Tool name from schema: {schema_name}")

                    if schema_name == tool_name:
                        matched_tool = tool
                        break
                if matched_tool is not None:
                    try:
                        # Optionally, special handling if you want to yield the command first for shell
                        if (
                            tool_name == "shell_tool" or tool_name == "shell"
                        ) and tool_args.get("command"):
                            yield f"**$ {tool_args['command']}**\n"

                        # Ensure the executor exists
                        if "executor" not in matched_tool:
                            error_msg = f"Error: Tool '{tool_name}' found but has no executor function"
                            logger.error(error_msg)
                            yield error_msg
                        else:
                            tool_output = matched_tool["executor"](tool_args)
                            yield (
                                tool_output
                                if isinstance(tool_output, str)
                                else str(tool_output)
                            )
                        tool_result_for_history = (
                            tool_output
                            if isinstance(tool_output, str)
                            else str(tool_output)
                        )
                    except Exception as e:
                        error_msg = f"Error executing {tool_name} tool: {str(e)}"
                        logger.error(error_msg)
                        logger.error(traceback.format_exc())
                        yield error_msg + "\n"
                        tool_result_for_history = error_msg
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
                        elif hasattr(schema, "name"):
                            available_tools.append(schema.name)

                    error_msg = f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(available_tools) if available_tools else 'None'}"
                    logger.error(error_msg)
                    yield error_msg + "\n"
                    tool_result_for_history = error_msg

                # Add the tool result to messages for the next LLM call
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
            return

    # If we've reached max iterations
    yield "Error: Maximum iterations reached without a final response"

    if all_tool_results:
        return (
            "\n".join(all_tool_results)
            + "\n\nError: Maximum iterations reached without a final response"
        )

    return "Error: Maximum iterations reached without a final response"
