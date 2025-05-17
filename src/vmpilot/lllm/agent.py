"""
Agent implementation for LiteLLM Migration MVP.
Provides a simple agent loop with tool support using LiteLLM.
"""

import json
import logging
import os
import queue
import threading
from typing import Any, Dict, Generator, List

import litellm

from vmpilot.lllm.shelltool import SHELL_TOOL, execute_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress LiteLLM info/debug logs
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def parse_tool_calls(response) -> List[Dict[str, Any]]:
    """Extract tool calls from the LLM response."""
    tool_calls = []

    try:
        # Extract tool calls from the response
        message = response.choices[0].message
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

    return tool_calls


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

    # Prepare system prompt
    system_prompt = (
        "You are VMPilot, an AI assistant that can help with system operations."
    )
    if system_prompt_suffix:
        system_prompt += "\n\n" + system_prompt_suffix

    # Run agent_loop in a separate thread
    def run_loop():
        try:
            # Get model from pipeline
            model = pipeline_self.valves.model

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
            logger.error(f"Error in agent loop: {str(e)}")
            output_queue.put(f"Error: {str(e)}")
        finally:
            loop_done.set()

    # Start the thread
    thread = threading.Thread(target=run_loop)
    thread.daemon = True
    thread.start()

    # Yield responses from the queue
    while not loop_done.is_set() or not output_queue.empty():
        try:
            response = output_queue.get(timeout=0.1)
            yield response
        except queue.Empty:
            pass


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
    if "openai" in model or "gpt" in model:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY environment variable not set"
    elif "anthropic" in model or "claude" in model:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Error: ANTHROPIC_API_KEY environment variable not set"
    else:
        return f"Error: Unsupported model {model}"

    # Main agent loop
    max_iterations = 10  # Safety limit to prevent infinite loops
    iteration = 0

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

            # Parse tool calls from response
            tool_calls = parse_tool_calls(response)

            # If no tool calls, return the final response
            if not tool_calls:
                return response.choices[0].message.content

            # Execute each tool call and add results to messages
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                logger.info(f"Executing tool: {tool_name}")
                tool_result = execute_tool(tool_name, tool_args)

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

    return "Error: Maximum iterations reached without a final response"
