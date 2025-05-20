"""
response.py for LiteLLM implementation
Handles generating responses from the LLM and tools, managing streaming, and output.
This module calls the agent_loop from lllm_agent.py.
"""

import logging
import queue
import threading
import traceback
from typing import Generator

from vmpilot.lllm.agent import SHELL_TOOL, agent_loop

logger = logging.getLogger(__name__)


def generate_responses(
    body, pipeline_self, messages, system_prompt_suffix, formatted_messages
) -> Generator[str, None, None]:
    """
    Generates responses from the LLM and tools, handling streaming and output callbacks.
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

            # Run the agent loop and stream results to the queue
            for item in agent_loop(
                user_input=user_input,
                system_prompt=system_prompt,
                tools=tools,  # tools are passed to litellm.completion inside agent_loop
                model=model,
            ):
                output_queue.put(item)
        except Exception as e:
            # This top-level exception catch in run_loop might be redundant if agent_loop handles its errors by yielding them
            # However, it can catch errors from agent_loop's setup or if agent_loop itself fails to instantiate/run
            error_msg = f"Error in agent_loop dispatcher: {str(e)}"
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
            output = output_queue.get(timeout=0.1)
            response_received = True
            yield output
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error getting output: {e}")
            break

    # If no response was received and the loop is done, yield a default message
    if not response_received and loop_done.is_set():
        yield "Command executed but no response was generated."
