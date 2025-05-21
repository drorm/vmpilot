"""
response.py for LiteLLM implementation
Handles generating responses from the LLM and tools, managing streaming, and output.
This module calls the agent_loop from lllm_agent.py.
"""

import asyncio
import logging
import queue
import threading
import traceback
from typing import Generator

from vmpilot.config import MAX_TOKENS, RECURSION_LIMIT, TEMPERATURE, TOOL_OUTPUT_LINES
from vmpilot.lllm.agent import process_messages

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

    # Prepare system prompt with more context from VMPilot
    system_prompt = """You are VMPilot, an AI assistant that can help with system operations.\nYou can execute shell commands to help users with their tasks.\nAlways format command outputs with proper markdown formatting.\nBe concise and helpful in your responses."""

    # Add system prompt suffix if provided
    if system_prompt_suffix:
        system_prompt += "\n\n" + system_prompt_suffix

    # Log system prompt at debug level
    logger.debug(f"System prompt: {system_prompt}")

    # Import config dynamically to avoid circular imports
    from vmpilot.config import TOOL_OUTPUT_LINES

    def handle_exception(e):
        logger.error(f"Error: {e}")
        logger.error("".join(traceback.format_tb(e.__traceback__)))
        output_queue.put(f"Error: {str(e)}")

    # Callbacks for LLM and tool outputs
    def output_callback(content):
        logger.debug(f"Received content: {content}")
        if isinstance(content, dict) and content.get("type") == "text":
            logger.debug(f"Assistant: {content['text']}")
            output_queue.put(content["text"])
        elif isinstance(content, str):
            output_queue.put(content)

    def tool_callback(result, tool_id=None):
        logger.debug(f"Tool callback received result: {result}")
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
        logger.debug("Tool callback queueing outputs:")
        for output in outputs:
            output_lines = str(output).splitlines()
            truncated_output = "\n".join(output_lines[:TOOL_OUTPUT_LINES])
            if len(output_lines) > (TOOL_OUTPUT_LINES + 1):
                truncated_output += f"\n...\n````\n(and {len(output_lines) - TOOL_OUTPUT_LINES} more lines)\n"
            else:
                truncated_output += "\n"
            output_queue.put(truncated_output)

    def run_loop():
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Set exception handler for the loop to catch unhandled exceptions
            def asyncio_exception_handler(loop, context):
                exception = context.get("exception")
                if exception:
                    logger.error(f"Caught asyncio exception: {exception}")
                    logger.error("".join(traceback.format_tb(exception.__traceback__)))
                else:
                    logger.error(f"Asyncio error: {context['message']}")

            loop.set_exception_handler(asyncio_exception_handler)

            model = pipeline_self.valves.model
            provider = getattr(pipeline_self.valves.provider, "value", None)
            api_key = getattr(pipeline_self, "_api_key", None)
            # Build messages and params for process_messages
            coroutine = process_messages(
                model=model,
                provider=provider,
                system_prompt_suffix=system_prompt_suffix,
                messages=formatted_messages,
                output_callback=output_callback,
                tool_output_callback=tool_callback,
                api_key=api_key,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                disable_logging=body.get("disable_logging", False),
                recursion_limit=None,
            )
            loop.run_until_complete(coroutine)
        except Exception as e:
            handle_exception(e)
        finally:
            loop_done.set()
            if loop:
                try:
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                    loop.close()
                except Exception as e:
                    logger.warning(f"Error during loop cleanup: {e}")

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
            handle_exception(e)
            break

    # If no response was received and the loop is done, yield a default message
    if not response_received and loop_done.is_set():
        yield "Command executed but no response was generated."
