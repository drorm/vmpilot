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
logger.setLevel(logging.INFO)

# Create handlers
stream_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(stream_handler)
logger.propagate = False

# Import tool output truncation setting
from vmpilot.config import TOOL_OUTPUT_LINES, Provider, config


class Pipeline:
    class Valves(BaseModel):
        # Required runtime parameters
        anthropic_api_key: str = ""
        openai_api_key: str = ""
        api_key: str = ""  # Will be set based on active provider
        pipelines_dir: str = ""

        # Model configuration
        provider: Provider = config.default_provider
        model: str = ""  # Will be set based on provider's default
        recursion_limit: int = 25  # Will be set based on provider's config

        # Inference parameters with OpenWebUI-compatible defaults
        temperature: float = 0.8
        max_tokens: int = 2048

        def __init__(self, **data):
            super().__init__(**data)
            if not self.model:
                self.model = config.get_default_model(self.provider)
            if self.recursion_limit is None:
                provider_config = config.get_provider_config(self.provider)
                self.recursion_limit = provider_config.recursion_limit
            # Set initial API key based on provider
            if self.provider == Provider.ANTHROPIC:
                self.api_key = self.anthropic_api_key
            else:
                self.api_key = self.openai_api_key

    def __init__(self):
        self.name = "VMPilot Pipeline"
        self.type = "manifold"
        self.id = "vmpilot"

        # Initialize valves with environment variables and defaults
        self.valves = self.Valves(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            pipelines_dir=os.getenv("PIPELINES_DIR", ""),
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
                "name": "OpenAI (GPT-4o)",
                "description": "Execute commands using OpenAI's GPT-4o model",
            },
        ]

        # Only show models with valid API keys
        return [model for model in models if len(self.valves.api_key) >= 32]

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
        if self.valves.provider == Provider.ANTHROPIC:
            if not self.valves.api_key or len(self.valves.api_key) < 32:
                error_msg = "Error: Invalid or missing Anthropic API key"
                logger.error(error_msg)
                if body.get("stream", False):

                    def error_generator():
                        yield {"type": "text", "text": error_msg}

                    return error_generator()
                return error_msg
            api_key = self.valves.api_key
        elif self.valves.provider == Provider.OPENAI:
            if not self.valves.api_key or len(self.valves.api_key) < 32:
                error_msg = "Error: Invalid or missing OpenAI API key"
                logger.error(error_msg)
                if body.get("stream", False):

                    def error_generator():
                        yield {"type": "text", "text": error_msg}

                    return error_generator()
                return error_msg
            api_key = self.valves.api_key
        else:
            error_msg = f"Error: Unsupported provider {self.valves.provider}"
            logger.error(error_msg)
            if body.get("stream", False):

                def error_generator():
                    yield {"type": "text", "text": error_msg}

                return error_generator()
            return error_msg

        from vmpilot.agent import APIProvider, process_messages

        # Handle title request
        if body.get("title", False):
            return "VMPilot Pipeline"

        # Set provider and model based on selected model_id
        if model_id == "anthropic":
            self.valves.provider = Provider.ANTHROPIC
            self.valves.api_key = self.valves.anthropic_api_key
            self.valves.model = config.get_default_model(Provider.ANTHROPIC)
        elif model_id == "openai":
            self.valves.provider = Provider.OPENAI
            self.valves.api_key = self.valves.openai_api_key
            self.valves.model = config.get_default_model(Provider.OPENAI)
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
                    logger.debug(f"System message: {system_prompt_suffix}")
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
                    logger.debug(f"Received content: {content}")
                    if content["type"] == "text":
                        logger.debug(f"Assistant: {content['text']}")
                        output_queue.put(content["text"])

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
                        if len(output_lines) > TOOL_OUTPUT_LINES:
                            truncated_output += f"\n...\n```\n(and {len(output_lines) - TOOL_OUTPUT_LINES} more lines)\n"
                        output_queue.put(truncated_output)

                def run_loop():
                    try:
                        api_key = (
                            self.valves.api_key
                            if self.valves.provider == Provider.OPENAI
                            else self.valves.api_key
                        )
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        logger.debug(f"body: {body}")
                        loop.run_until_complete(
                            process_messages(
                                model=(
                                    self.valves.model
                                    if self.valves.provider == Provider.OPENAI
                                    else self.valves.model
                                ),
                                provider=(
                                    APIProvider.OPENAI
                                    if self.valves.provider == Provider.OPENAI
                                    else APIProvider.ANTHROPIC
                                ),
                                system_prompt_suffix=system_prompt_suffix,
                                messages=formatted_messages,
                                output_callback=output_callback,
                                tool_output_callback=tool_callback,
                                api_key=api_key,
                                max_tokens=1024,
                                temperature=body.get(
                                    "temperature", self.valves.temperature
                                ),
                                disable_logging=body.get("disable_logging", False),
                                recursion_limit=body.get(
                                    "recursion_limit", self.valves.recursion_limit
                                ),
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
