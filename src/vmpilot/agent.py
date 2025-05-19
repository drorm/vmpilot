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
from typing import Any, Dict, Generator, List

import litellm

# Import shell tool from lllm implementation
# TODO: This will need to be updated to use the main tools system later
from vmpilot.lllm.shelltool import SHELL_TOOL, ShellToolResult, execute_tool

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


def generate_responses(
    body: Dict[str, Any],
    pipeline_self: Any,
    messages: list,  # Original messages, potentially for history
    system_prompt_suffix: str,
    formatted_messages: list,  # Messages formatted for the current LLM call
) -> Generator[str, None, None]:
    """
    LiteLLM version of generate_responses that uses agent_loop.
    This function is intended to be called from vmpilot.response.py.

    Args:
        body: Request body from the pipeline/caller.
        pipeline_self: Reference to the pipeline object (for model, API key access).
        messages: The original list of messages (potentially for chat history context).
        system_prompt_suffix: Additional text to append to the system prompt.
        formatted_messages: Messages specifically formatted for the current LLM call (usually the latest user message + context).

    Yields:
        Response chunks as they become available from the agent_loop.
    """
    output_queue = queue.Queue()
    loop_done = threading.Event()

    # Extract the user input from formatted_messages
    # TODO: Revisit how user input is best obtained; this assumes last message is user input.
    user_input = ""
    if formatted_messages and formatted_messages[-1].get("role") == "user":
        # Content can be a list of dicts (e.g. for images) or a simple string.
        # For now, we assume text based on current agent_loop's expectation.
        content_item = formatted_messages[-1].get("content", "")
        if isinstance(content_item, list) and content_item:
            # Find the first text item if content is a list
            for item in content_item:
                if item.get("type") == "text":
                    user_input = item.get("text", "")
                    break
        elif isinstance(content_item, str):
            user_input = content_item

    if not user_input:
        logger.error("No user input found in formatted_messages or input is not text")
        yield "Error: No user text input found for the agent."
        return

    # TODO: Integrate get_system_prompt() from vmpilot.prompt here (Step 2 of Issue #88)
    system_prompt = """You are VMPilot, an AI assistant that can help with system operations.
You can execute shell commands to help users with their tasks.
Always format command outputs with proper markdown formatting.
Be concise and helpful in your responses."""

    if system_prompt_suffix:
        system_prompt += "\n\n" + system_prompt_suffix

    logger.debug(f"System prompt for agent_loop: {system_prompt}")

    # TODO: Integrate the full toolset from vmpilot.tools (Step 6 of Issue #88)
    # For now, using the MVP shell tool.
    tools = [SHELL_TOOL]

    # Get model and API key from pipeline_self (passed from vmpilot.py)
    # This replaces direct os.environ access in the original lllm/agent.py
    model = pipeline_self.valves.model
    api_key = pipeline_self._api_key  # Access the centrally managed API key
    # Determine provider for LiteLLM if needed, or rely on LiteLLM's model name parsing
    # provider = pipeline_self.valves.provider.value

    logger.info(f"LiteLLM agent using model: {model}")

    def run_loop():
        try:
            # The agent_loop in the MVP returned a single string.
            # To fit the streaming model of generate_responses, we will iterate if it's a generator,
            # or put the single string onto the queue.
            # For full LiteLLM migration, agent_loop itself will become a generator.
            # For now, let's adapt based on the current agent_loop from lllm/agent.py
            # which returns a single string. We'll modify lllm/agent.py's agent_loop
            # to be a generator as part of this refactoring.

            # MODIFICATION: agent_loop will be changed to be a generator
            result_generator = agent_loop(
                user_input=user_input,
                system_prompt=system_prompt,
                tools=tools,
                model=model,
                api_key=api_key,
                # messages_history=messages # Pass full history if agent_loop is adapted
            )
            for chunk in result_generator:  # agent_loop will now yield chunks
                output_queue.put(chunk)

        except Exception as e:
            error_msg = f"Error in agent_loop thread: {str(e)}"
            logger.error(error_msg)
            logger.error("".join(traceback.format_tb(e.__traceback__)))
            output_queue.put(f"Error: {str(e)}")
        finally:
            loop_done.set()

    thread = threading.Thread(target=run_loop)
    thread.daemon = True
    thread.start()

    response_received = False
    while not loop_done.is_set() or not output_queue.empty():
        try:
            response_chunk = output_queue.get(timeout=0.1)
            response_received = True
            yield response_chunk
        except queue.Empty:
            pass

    if not response_received and loop_done.is_set():
        logger.warning("Agent loop finished but no response was yielded to the queue.")
        yield "Agent processing complete; no explicit response generated."


def agent_loop(
    user_input: str,
    system_prompt: str,
    tools: List[Dict[str, Any]],
    model: str,
    api_key: str,  # Added api_key parameter
    # messages_history: List[Dict[str,Any]] = None # Potential future parameter for history
) -> Generator[str, None, None]:  # Changed to generator
    """
    Main agent loop that processes user input, sends it to LiteLLM,
    executes tools, and yields responses/tool outputs.
    """
    # TODO: Integrate Chat class and unified_memory for history (Steps 3 & 4 of Issue #88)
    current_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    # if messages_history:
    #     # Logic to prepend history, truncate, etc.
    #     pass

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"LiteLLM Agent loop iteration {iteration}")

        try:
            logger.debug(
                f"Sending to LiteLLM: Model={model}, Messages={current_messages}, Tools={tools is not None}"
            )
            response_stream = litellm.completion(  # Renamed for clarity
                model=model,
                messages=current_messages,
                tools=tools,
                api_key=api_key,
                temperature=0,  # TODO: Make configurable
                max_tokens=4000,  # TODO: Make configurable
                stream=True,
            )

            accumulated_content = ""
            tool_calls_aggregated = []

            # Iterate through stream chunks
            for chunk in response_stream:
                # Check if chunk itself is None, or if choices list is empty
                if not chunk or not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                # If delta is None (can happen with some model/provider end-of-stream markers)
                if delta is None:
                    continue

                if delta.content:
                    yield delta.content
                    accumulated_content += delta.content

                if delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        # This logic attempts to aggregate streamed tool calls.
                        # LiteLLM's streaming behavior for tool calls can vary.
                        # For robust handling, it's often better to get the full tool_calls array
                        # from the message once the content stream is finished, if the provider supports that.
                        # If tool calls are guaranteed to be complete in one delta chunk (or aggregated by LiteLLM already),
                        # this can be simpler.
                        # For now, assuming a basic aggregation or that they come in full.

                        # A common pattern is that `id` and `name` appear first, then `arguments` stream.
                        # We need to find by id and append to arguments or create new.
                        existing_tc = next(
                            (
                                tc
                                for tc in tool_calls_aggregated
                                if tc_chunk.id and tc["id"] == tc_chunk.id
                            ),
                            None,
                        )
                        if existing_tc:
                            if tc_chunk.function and tc_chunk.function.arguments:
                                existing_tc["function"][
                                    "arguments"
                                ] += tc_chunk.function.arguments
                        elif (
                            tc_chunk.id and tc_chunk.function and tc_chunk.function.name
                        ):  # Ensure essential fields are present
                            tool_calls_aggregated.append(
                                {
                                    "id": tc_chunk.id,
                                    "type": "function",  # Default type
                                    "function": {
                                        "name": tc_chunk.function.name,
                                        "arguments": tc_chunk.function.arguments
                                        or "",  # Ensure arguments is a string
                                    },
                                }
                            )

            # Add accumulated assistant message (if any) to history
            # This should happen *after* the streaming loop for the current LLM call concludes.
            if accumulated_content:  # If assistant said something
                current_messages.append(
                    {"role": "assistant", "content": accumulated_content}
                )

            # Process tool calls after stream is complete and content is gathered
            parsed_tool_calls = []
            if tool_calls_aggregated:
                # Add the raw tool_calls object that the assistant wanted to make
                # (before we add the actual tool results)
                assistant_message_with_tools = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls_aggregated,
                }
                current_messages.append(assistant_message_with_tools)

                for tc_data in tool_calls_aggregated:
                    try:
                        # Ensure arguments string is valid JSON before parsing
                        args_str = tc_data["function"]["arguments"]
                        if not args_str.strip():  # Handle empty arguments string
                            arguments = {}
                        else:
                            arguments = json.loads(args_str)
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Tool call argument JSON parsing error: {e} for arguments: {args_str}"
                        )
                        arguments = {
                            "error": "Failed to parse arguments",
                            "raw_arguments": args_str,
                        }

                    parsed_tool_calls.append(
                        {
                            "id": tc_data["id"],
                            "name": tc_data["function"]["name"],
                            "arguments": arguments,
                        }
                    )

            if not parsed_tool_calls:
                if (
                    not accumulated_content
                    and iteration == 1
                    and not messages[-1].get("tool_calls")
                ):  # Check if the last message has tool_calls
                    logger.info(
                        "No content or tool calls from LLM in the first iteration."
                    )
                # If there was no textual output yielded during the stream,
                # and no tool calls, this generation cycle for the agent is done.
                return

            # Execute tools
            for tool_call in parsed_tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]
                tool_call_id = tool_call["id"]

                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                # TODO: Integrate with the main tool execution system (Step 6 of Issue #88)
                if tool_name == "shell":  # Assumes SHELL_TOOL is the only one for now
                    tool_result_str = execute_tool("shell", tool_args)
                    yield f"\n--- Tool Output ({tool_name}) ---\n{tool_result_str}\n----------------------------\n"
                else:
                    tool_result_str = (
                        f"Error: Tool '{tool_name}' not implemented or recognized."
                    )
                    yield f"\n--- Tool Error ({tool_name}) ---\n{tool_result_str}\n--------------------------\n"

                current_messages.append(
                    {
                        "role": "tool",
                        "content": tool_result_str,
                        "tool_call_id": tool_call_id,
                    }
                )
            # Loop back to LLM with tool results (if any tools were called)

        except Exception as e:
            error_message = (
                f"Error in LiteLLM agent_loop: {str(e)}\n{traceback.format_exc()}"
            )
            logger.error(error_message)
            yield f"\n--- Agent Error ---\n{error_message}\n---------------------\n"
            return  # Stop generation on error

        logger.warning("Maximum iterations reached in agent_loop.")
        yield "\n--- Agent Warning ---\nMaximum iterations reached.\n----------------------\n"


# TODO (Post-MVP, during full integration):
# - Integrate vmpilot.config for model, temperature, max_tokens settings.
# - Integrate vmpilot.prompt.get_system_prompt().
# - Replace lllm.shelltool with the main tool system (vmpilot.tools and tool_execution).
# - Integrate vmpilot.chat.Chat and vmpilot.unified_memory for history.
# - Integrate vmpilot.exchange.Exchange and vmpilot.usage.Usage.
# - Robust error handling and streaming for tool calls.
# - Graceful handling of different content types in messages.
