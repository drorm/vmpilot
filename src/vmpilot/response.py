"""
response.py
Generates responses from the LLM and tools, handling streaming and output callbacks.
This module is designed to be used within a pipeline, where it can process process_messages
from the LLM and tools, and yield responses as they come in.

"""

import asyncio
import logging
import queue
import threading
import traceback
from typing import Dict

from vmpilot.agent import APIProvider, process_messages
from vmpilot.config import MAX_TOKENS, RECURSION_LIMIT, TEMPERATURE, TOOL_OUTPUT_LINES

logger = logging.getLogger(__name__)


def generate_responses(
    body, pipeline_self, messages, system_prompt_suffix, formatted_messages
):
    """
    Generates responses from the LLM and tools, handling streaming and output callbacks.
    This function is intended to be called from within the pipeline logic.
    """
    output_queue = queue.Queue()
    loop_done = threading.Event()

    # Output callback to handle messages from the LLM
    def output_callback(content: Dict):
        logger.debug(f"Received content: {content}")
        if content["type"] == "text":
            logger.debug(f"Assistant: {content['text']}")
            output_queue.put(content["text"])

    # Output callback to handle tool messages: output from commands
    def tool_callback(result, tool_id):
        logger.debug(f"Tool callback received result: {result}")
        outputs = []
        # Handle dictionary results (from FileEditTool)
        if isinstance(result, dict):
            if "error" in result and result["error"]:
                outputs.append(result["error"])
            if "output" in result and result["output"]:
                outputs.append(result["output"])
        # Handle object results (from shell tool)
        else:
            if hasattr(result, "error") and result.error:
                if hasattr(result, "exit_code") and result.exit_code:
                    outputs.append(f"Exit code: {result.exit_code}")
                outputs.append(result.error)

        logger.debug("Tool callback queueing outputs:")
        for output in outputs:
            output_lines = str(output).splitlines()
            truncated_output = "\n".join(output_lines[:TOOL_OUTPUT_LINES])
            if len(output_lines) > (TOOL_OUTPUT_LINES + 1):
                truncated_output += f"\n...\n````\n(and {len(output_lines) - TOOL_OUTPUT_LINES} more lines)\n"
            else:
                truncated_output += "\n"
            output_queue.put(truncated_output)

    # Run the sampling loop in a separate thread while waiting for responses
    def run_loop():
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Set exception handler for the loop to catch unhandled exceptions
            def handle_exception(loop, context):
                exception = context.get("exception")
                if exception:
                    if "TCPTransport closed=True" in str(
                        exception
                    ) or "unable to perform operation" in str(exception):
                        logger.info(
                            "Ignoring expected httpx connection cleanup exception. This is OK. For more info: https://github.com/drorm/vmpilot/issues/35"
                        )
                    else:
                        message = f"Caught asyncio exception: {exception}"
                        logger.error(message)
                        logger.error(
                            "".join(traceback.format_tb(exception.__traceback__))
                        )
                else:
                    logger.error(f"Asyncio error: {context['message']}")

            loop.set_exception_handler(handle_exception)

            logger.debug(f"body: {body}")
            loop.run_until_complete(
                process_messages(
                    model=pipeline_self.valves.model,
                    provider=APIProvider(pipeline_self.valves.provider.value),
                    system_prompt_suffix=system_prompt_suffix,
                    messages=formatted_messages,
                    output_callback=output_callback,
                    tool_output_callback=tool_callback,
                    api_key=pipeline_self._api_key,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    disable_logging=body.get("disable_logging", False),
                    recursion_limit=RECURSION_LIMIT,
                )
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error("".join(traceback.format_tb(e.__traceback__)))
        finally:
            loop_done.set()
            # Safely close the loop
            if loop:
                try:
                    # Cancel all running tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    # Allow tasks to respond to cancellation
                    if pending:
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                    loop.close()
                except Exception as e:
                    logger.warning(f"Error during loop cleanup: {e}")

    # Start the sampling loop in a separate thread
    thread = threading.Thread(target=run_loop)
    thread.start()

    # Yield responses as they come in
    while not loop_done.is_set() or not output_queue.empty():
        try:
            output = output_queue.get(timeout=0.1)
            yield output
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error getting output: {e}")
            break

    thread.join()
