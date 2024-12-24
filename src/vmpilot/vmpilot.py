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
import traceback
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
from vmpilot.config import (
    DEFAULT_PROVIDER,
    MAX_TOKENS,
    RECURSION_LIMIT,
    TEMPERATURE,
    TOOL_OUTPUT_LINES,
    Provider,
    config,
)


class Pipeline:
    api_key: str = ""  # Set based on active provider

    class Valves(BaseModel):
        # Runtime parameters
        anthropic_api_key: str = ""
        openai_api_key: str = ""

        # Model configuration (inherited from config)
        provider: Provider = Provider(DEFAULT_PROVIDER)
        model: str = ""  # Set based on provider's default
        recursion_limit: int = RECURSION_LIMIT

        # Inference parameters from config
        temperature: float = TEMPERATURE
        max_tokens: int = MAX_TOKENS

        def __init__(self, **data):
            super().__init__(**data)
            self._sync_with_config()

        def _sync_with_config(self):
            """Synchronize valve state with config defaults"""
            if not self.model:
                self.model = config.get_default_model(self.provider)

            provider_config = config.get_provider_config(self.provider)
            if self.recursion_limit is None:
                self.recursion_limit = provider_config.recursion_limit

            # Update API key based on provider
            self._update_api_key()

        def _update_api_key(self):
            """Update api_key based on current provider"""
            Pipeline.api_key = (
                self.anthropic_api_key
                if self.provider == Provider.ANTHROPIC
                else self.openai_api_key
            )

    def __init__(self):
        self.name = "VMPilot Pipeline"
        self.type = "manifold"
        self.id = "vmpilot"

        # Initialize valves with environment variables and defaults
        self.valves = self.Valves(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )

    async def on_startup(self):
        logger.debug(f"on_startup:{__name__}")

    async def on_shutdown(self):
        logger.debug(f"on_shutdown:{__name__}")

    async def on_valves_updated(self):
        """Handle valve updates by re-syncing configuration"""
        self.valves._sync_with_config()
        logger.debug(f"Valves updated and synced with config")

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
        return [model for model in models if len(self.api_key) >= 32]

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Execute bash commands through an LLM with tool integration."""
        logger.debug(f"Starting pipe with message: {user_message}")
        # Disable logging if requested (e.g. when running from CLI)
        if body.get("disable_logging"):
            # Disable all logging at the root level
            logging.getLogger().setLevel(logging.ERROR)
            logger.disabled = True
        if body.get("model"):
            self.valves.model = body.get("model")
        else:
            self.valves.model = ""

        # Validate API key
        if not self.api_key or len(self.api_key) < 32:
            error_msg = (
                f"Error: Invalid or missing {self.valves.provider.value} API key"
            )
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

        # Update provider and related configuration based on model ID
        try:
            # Handle provider change if model_id matches a provider name
            try:
                if model_id.lower() in [p.value for p in Provider]:
                    new_provider = Provider(model_id.lower())
                    self.valves.provider = new_provider
                    self.valves._sync_with_config()
                else:
                    # Treat as actual model name
                    if not config.validate_model(model_id, self.valves.provider):
                        error_msg = f"Unsupported model: {model_id}"
                        logger.error(error_msg)
                        return error_msg
                    self.valves.model = model_id
            except ValueError:
                error_msg = f"Unsupported model: {model_id}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"Error updating provider: {str(e)}"
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
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        logger.debug(f"body: {body}")
                        loop.run_until_complete(
                            process_messages(
                                model=self.valves.model,
                                provider=APIProvider(self.valves.provider.value),
                                system_prompt_suffix=system_prompt_suffix,
                                messages=formatted_messages,
                                output_callback=output_callback,
                                tool_output_callback=tool_callback,
                                api_key=self.api_key,
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
                        logger.error("".join(traceback.format_tb(e.__traceback__)))
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
