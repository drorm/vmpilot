"""
title: VMPilot Pipeline
author: Assistant
date: 2024-11-20
version: 0.1
license: MIT
description: A pipeline that enables using an LLM to execute commands
environment_variables: ANTHROPIC_API_KEY
"""

import asyncio
import logging
import os
import queue
import threading
from typing import Dict, Generator, Iterator, List, Union

from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
stream_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(stream_handler)
logger.propagate = False

# Number of lines to show in tool output before truncating
TOLL_OUTPUT_LINES = 7


class Pipeline:
    class Valves(BaseModel):
        # Required runtime parameters
        ANTHROPIC_API_KEY: str = ""
        PIPELINES_DIR: str = ""

        # Model configuration
        MODEL_ID: str = "claude-3-5-sonnet-20241022"
        PROVIDER: str = "anthropic"  # Maps to APIProvider.ANTHROPIC

        # Inference parameters with OpenWebUI-compatible defaults
        TEMPERATURE: float = 0.8

        MAX_TOKENS: int = 4096

    def __init__(self):
        self.name = "VMPilot Pipeline"
        self.type = "manifold"
        self.id = "vmpilot"

        # Initialize valves with environment variables and defaults
        self.valves = self.Valves(
            ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY", ""),
            PIPELINES_DIR=os.getenv("PIPELINES_DIR", ""),
        )

    async def on_startup(self):
        logger.debug(f"on_startup:{__name__}")

    async def on_shutdown(self):
        logger.debug(f"on_shutdown:{__name__}")

    async def on_valves_updated(self):
        logger.debug(f"on_valves_updated:{__name__}")

    def pipelines(self) -> List[dict]:
        """Return list of supported models/pipelines"""
        return [
            {
                "id": "VMPilot",
                "name": "VMPilot Pipeline",
                "description": "Execute bash commands via pipeline",
            }
        ]

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Execute bash commands through an LLM with tool integration."""
        # Disable logging if requested (e.g. when running from CLI)
        if body.get("disable_logging"):
            logger.disabled = True

        # Validate API key
        if not self.valves.ANTHROPIC_API_KEY or len(self.valves.ANTHROPIC_API_KEY) < 32:
            error_msg = "Error: Invalid or missing API key"
            logger.error(error_msg)
            return error_msg

        logger.info(f"User: {user_message}")

        from vmpilot.loop import APIProvider, sampling_loop

        # Handle title request
        if body.get("title", False):
            return "VMPilot Pipeline"

        # Verify the model is supported
        if model_id != "VMPilot":
            error_msg = f"Unsupported model"
            logger.error(error_msg)
            return error_msg

        try:
            # Extract system message and format messages
            formatted_messages = []
            system_prompt_suffix = ""

            for msg in messages:
                role = msg["role"]
                content = msg["content"]

                # Extract system message
                if role == "system" and isinstance(content, str):
                    system_prompt_suffix = content
                    continue

                if isinstance(content, str):
                    formatted_messages.append(
                        {
                            "role": role,
                            "content": [{"type": "text", "text": content}],
                        }
                    )
                else:
                    formatted_messages.append({"role": role, "content": content})

            # Add current user message
            formatted_messages.append(
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_message}],
                }
            )

            def generate_responses():
                output_queue = queue.Queue()
                loop_done = threading.Event()

                def output_callback(content: Dict):
                    if content["type"] == "text":
                        logger.info(f"Assistant: {content['text']}")
                        output_queue.put(content["text"])

                def tool_callback(result, tool_id):
                    outputs = []
                    if hasattr(result, "error") and result.error:
                        if hasattr(result, "exit_code") and result.exit_code:
                            outputs.append(f"Exit code: {result.exit_code}")
                        outputs.append(result.error)
                    if hasattr(result, "output") and result.output:
                        outputs.append(f"\n```plain\n{result.output}\n```\n")

                    logger.debug("Tool callback queueing outputs:")
                    for i, output in enumerate(outputs, 1):
                        # Show first n lines of output (default 5 lines)
                        output_lines = output.splitlines()
                        truncated_output = "\n".join(output_lines[:TOLL_OUTPUT_LINES])
                        if len(output_lines) > TOLL_OUTPUT_LINES:
                            truncated_output += f"\n... (and {len(output_lines) - TOLL_OUTPUT_LINES} more lines)"
                        logger.info(f"{truncated_output}")
                    for output in outputs:
                        output_queue.put(output)

                def run_loop():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        logger.debug(f"body: {body}")
                        loop.run_until_complete(
                            sampling_loop(
                                model=self.valves.MODEL_ID,
                                provider=APIProvider.ANTHROPIC,
                                system_prompt_suffix=system_prompt_suffix,
                                messages=formatted_messages,
                                output_callback=output_callback,
                                tool_output_callback=tool_callback,
                                api_response_callback=lambda req, res, exc: None,
                                api_key=self.valves.ANTHROPIC_API_KEY,
                                max_tokens=body.get(
                                    "max_tokens", self.valves.MAX_TOKENS
                                ),
                                temperature=body.get(
                                    "temperature", self.valves.TEMPERATURE
                                ),
                                # top_k=body.get("top_k", self.valves.TOP_K),
                                # top_p=body.get("top_p", self.valves.TOP_P),
                                # stop_sequences=body.get("stop", self.valves.STOP_SEQUENCES),
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error in sampling loop: {e}")
                    finally:
                        loop_done.set()
                        loop.close()

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

            if body.get("stream", False):
                logger.debug("Streaming mode enabled")
                return generate_responses()
            else:
                # For non-streaming, collect all output and return as string
                logger.debug("Non-streaming mode")
                output_parts = []
                for msg in generate_responses():
                    output_parts.append(msg)
                result = (
                    "\n".join(output_parts)
                    if output_parts
                    else "Command executed successfully"
                )
                logger.debug(f"Non-streaming result: {result}")
                return result

        except Exception as e:
            error_msg = f"Error in pipe: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
