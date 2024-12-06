"""
title: VMPilot Pipeline
author: Assistant
date: 2024-12-02
version: 0.2
license: MIT
description: A pipeline that enables using an LLM to execute commands via LangChain
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
logger.setLevel(logging.DEBUG)

# Create handlers
stream_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(stream_handler)
logger.propagate = False

# Number of lines to show in tool output before truncating
TOOL_OUTPUT_LINES = 7


class Pipeline:
    class Valves(BaseModel):
        # Required runtime parameters
        ANTHROPIC_API_KEY: str = ""
        OPENAI_API_KEY: str = ""
        PIPELINES_DIR: str = ""

        # Model configuration
        MODEL_ID: str = "claude-3-5-sonnet-20241022"
        PROVIDER: str = "openai"  # Maps to APIProvider.ANTHROPIC or APIProvider.OPENAI

        # OpenAI model options
        OPENAI_MODEL_ID: str = "gpt-4"

        # Inference parameters with OpenWebUI-compatible defaults
        TEMPERATURE: float = 0.8
        MAX_TOKENS: int = 2048

    def __init__(self):
        self.name = "VMPilot Pipeline"
        self.type = "manifold"
        self.id = "vmpilot"

        # Initialize valves with environment variables and defaults
        self.valves = self.Valves(
            ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY", ""),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
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
        models = [
            {
                "id": "anthropic",
                "name": "Anthropic (Claude)",
                "description": "Execute commands using Anthropic's Claude model",
            },
            {
                "id": "openai",
                "name": "OpenAI (GPT-4)",
                "description": "Execute commands using OpenAI's GPT-4 model",
            },
        ]

        # Only show models with valid API keys
        return [
            model
            for model in models
            if (model["id"] == "anthropic" and len(self.valves.ANTHROPIC_API_KEY) >= 32)
            or (model["id"] == "openai" and len(self.valves.OPENAI_API_KEY) >= 32)
        ]

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Execute bash commands through an LLM with tool integration."""
        logger.debug(f"DEBUG: Starting pipe with message: {user_message}")
        # Disable logging if requested (e.g. when running from CLI)
        if body.get("disable_logging"):
            # Disable all logging at the root level
            logging.getLogger().setLevel(logging.ERROR)
            logger.disabled = True

        # Validate API key based on provider
        if self.valves.PROVIDER == "anthropic":
            if (
                not self.valves.ANTHROPIC_API_KEY
                or len(self.valves.ANTHROPIC_API_KEY) < 32
            ):
                error_msg = "Error: Invalid or missing Anthropic API key"
                logger.error(error_msg)
                return error_msg
            api_key = self.valves.ANTHROPIC_API_KEY
        elif self.valves.PROVIDER == "openai":
            if not self.valves.OPENAI_API_KEY or len(self.valves.OPENAI_API_KEY) < 32:
                error_msg = "Error: Invalid or missing OpenAI API key"
                logger.error(error_msg)
                return error_msg
            api_key = self.valves.OPENAI_API_KEY
        else:
            error_msg = f"Error: Unsupported provider {self.valves.PROVIDER}"
            logger.error(error_msg)
            return error_msg

        from vmpilot.lang import process_messages, APIProvider

        # Handle title request
        if body.get("title", False):
            return "VMPilot Pipeline"

        # Set provider based on selected model
        if model_id == "anthropic":
            self.valves.PROVIDER = "anthropic"
        elif model_id == "openai":
            self.valves.PROVIDER = "openai"
        else:
            error_msg = f"Unsupported model: {model_id}"
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
                    logger.debug(f"DEBUG: Received content: {content}")
                    if content["type"] == "text":
                        logger.info(f"Assistant: {content['text']}")
                        output_queue.put(content["text"])

                def tool_callback(result, tool_id):
                    logger.debug(
                        f"DEBUG: Tool callback received result: {result}"
                    )
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
                        if hasattr(result, "output") and result.output:
                            outputs.append(f"\n```plain\n{result.output}\n```\n")

                    logger.debug("Tool callback queueing outputs:")
                    for output in outputs:
                        output_lines = str(output).splitlines()
                        truncated_output = "\n".join(output_lines[:TOOL_OUTPUT_LINES])
                        if len(output_lines) > TOOL_OUTPUT_LINES:
                            truncated_output += f"\n... (and {len(output_lines) - TOOL_OUTPUT_LINES} more lines)"
                        logger.info(f"{truncated_output}")
                        output_queue.put(output)

                def run_loop():
                    try:
                        api_key = (
                            self.valves.OPENAI_API_KEY
                            if self.valves.PROVIDER == "openai"
                            else self.valves.ANTHROPIC_API_KEY
                        )
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        logger.debug(f"body: {body}")
                        loop.run_until_complete(
                            process_messages(
                                model=(
                                    self.valves.OPENAI_MODEL_ID
                                    if self.valves.PROVIDER == "openai"
                                    else self.valves.MODEL_ID
                                ),
                                provider=(
                                    APIProvider.OPENAI
                                    if self.valves.PROVIDER == "openai"
                                    else APIProvider.ANTHROPIC
                                ),
                                system_prompt_suffix=system_prompt_suffix,
                                messages=formatted_messages,
                                output_callback=output_callback,
                                tool_output_callback=tool_callback,
                                api_key=api_key,
                                max_tokens=1024,
                                temperature=body.get(
                                    "temperature", self.valves.TEMPERATURE
                                ),
                                disable_logging=body.get("disable_logging", False),
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
                    "\n\n".join(part.strip() for part in output_parts)
                    if output_parts
                    else "Command executed successfully"
                )
                logger.debug(f"Non-streaming result: {result}")
                return result

        except Exception as e:
            error_msg = f"Error in pipe: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
