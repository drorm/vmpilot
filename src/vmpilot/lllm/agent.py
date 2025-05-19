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
    body, pipeline_self, messages, system_prompt_suffix, formatted_messages
) -> Generator[str, None, None]:
    """
    LiteLLM version of generate_responses that uses agent_loop instead of process_messages.
    This function is intended to be called from within the pipeline logic.

    Args:
        body: Request body
        pipeline_self: Reference to the pipeline object
        messages: List of messages
        system_prompt_suffix: Additional text to append to the system prompt
        formatted_messages: Formatted messages for the LLM

    Yields:
        Response chunks as they become available
    """
    output_queue = queue.Queue()
    loop_done = threading.Event()

    # Extract the user input from formatted_messages
    user_input = ""
    for msg in formatted_messages:
        if msg.get("role") == "user":
            user_input = msg.get("content", "")
            break

    if not user_input:
        logger.error("No user input found in formatted_messages")
        yield "Error: No user input found"
        return

    # Set up tools - initially just the shell tool
    tools = [SHELL_TOOL]

    # Prepare system prompt with more context from VMPilot
    system_prompt = """You are VMPilot, an AI assistant that can help with system operations.
You can execute shell commands to help users with their tasks.
Always format command outputs with proper markdown formatting.
Be concise and helpful in your responses."""

    # Add system prompt suffix if provided
    if system_prompt_suffix:
        system_prompt += "\n\n" + system_prompt_suffix

    # Log system prompt at debug level
    logger.debug(f"System prompt: {system_prompt}")

    # Run agent_loop in a separate thread
    def run_loop():
        try:
            # Get model from pipeline
            model = pipeline_self.valves.model
            logger.info(f"Using model: {model}")

            # Run the agent loop
            result = agent_loop(
                user_input=user_input,
                system_prompt=system_prompt,
                tools=tools,
                model=model,
            )

            # Put the result in the output queue
            output_queue.put(result)
        except Exception as e:
            error_msg = f"Error in agent loop: {str(e)}"
            logger.error(error_msg)
            import traceback

            logger.error("".join(traceback.format_tb(e.__traceback__)))
            output_queue.put(f"Error: {str(e)}")
        finally:
            loop_done.set()

    # Start the thread
    thread = threading.Thread(target=run_loop)
    thread.daemon = True
    thread.start()

    # Yield responses from the queue
    response_received = False
    while not loop_done.is_set() or not output_queue.empty():
        try:
            response = output_queue.get(timeout=0.1)
            response_received = True
            yield response
        except queue.Empty:
            pass

    # If no response was received and the loop is done, yield a default message
    if not response_received and loop_done.is_set():
        yield "Command executed but no response was generated."


def agent_loop(
    user_input: str,
    system_prompt: str,
    tools: List[Dict[str, Any]],
    model: str = "gpt-4o",
) -> str:
    """
    Simple agent loop that processes user input, sends it to the LLM,
    executes tools when requested, and returns the final response.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    # Set up configuration from environment variables
    api_key = None

    # Get provider from model string
    if "openai" in model.lower() or "gpt" in model.lower():
        provider = "openai"
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY environment variable not set"
    elif "anthropic" in model.lower() or "claude" in model.lower():
        provider = "anthropic"
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Error: ANTHROPIC_API_KEY environment variable not set"
    elif "google" in model.lower() or "gemini" in model.lower():
        provider = "google"
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "Error: GOOGLE_API_KEY environment variable not set"

    # Main agent loop
    max_iterations = 10  # Safety limit to prevent infinite loops
    iteration = 0

    # Track all tool results for final output
    all_tool_results = []
    final_response = ""

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Agent loop iteration {iteration}")

        try:
            # Call LLM via LiteLLM
            response = litellm.completion(
                model=model,
                messages=messages,
                tools=tools,
                temperature=0,
                api_key=api_key,
                max_tokens=4000,
            )

            # Parse tool calls and content from response
            tool_calls, content = parse_tool_calls(response)

            # Store initial message from LLM if present
            if content and iteration == 1:
                all_tool_results.append(content)

            # If no tool calls, we've reached the final response
            if not tool_calls:
                final_response = content or response.choices[0].message.content
                # If we have tool results, include them before the final response
                if all_tool_results and all_tool_results[-1] != final_response:
                    # Don't duplicate the final response if it's already the last item
                    combined_output = (
                        "\n".join(all_tool_results) + "\n" + final_response
                    )
                    return combined_output
                else:
                    return final_response

            # Execute each tool call and add results to messages
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                logger.info(f"Executing tool: {tool_name}")
                # Execute tool using our lllm implementation
                if tool_name == "shell":
                    tool_result = execute_tool("shell", tool_args)
                    # Add to our tracked results
                    all_tool_results.append(tool_result)
                else:
                    tool_result = f"Error: Tool '{tool_name}' not implemented"
                    all_tool_results.append(tool_result)

                # Add the tool call and result to messages
                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_args),
                                },
                            }
                        ],
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call["id"],
                    }
                )

        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}")
            return f"Error: {str(e)}"

    # If we've reached max iterations but have tool results, return those with an error message
    if all_tool_results:
        return (
            "\n".join(all_tool_results)
            + "\n\nError: Maximum iterations reached without a final response"
        )

    return "Error: Maximum iterations reached without a final response"
