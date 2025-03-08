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
from datetime import datetime
from typing import Dict, Generator, Iterator, List, Optional, Union

from pydantic import BaseModel

# Import tool output truncation setting
from vmpilot.config import (
    DEFAULT_PROVIDER,
    MAX_TOKENS,
    RECURSION_LIMIT,
    TEMPERATURE,
    TOOL_OUTPUT_LINES,
    Provider,
    config,
    parser,
)

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


class Pipeline:
    # Provider management at Pipeline level
    _provider: Provider = Provider(DEFAULT_PROVIDER)
    _api_key: str = ""  # Set based on active provider

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # Store chat_id as instance variable for use in pipe
        self.chat_id = body.get("chat_id")
        return body

    class Valves(BaseModel):
        # Private storage for properties
        anthropic_api_key: str = ""
        openai_api_key: str = ""
        _provider: Provider = Provider(DEFAULT_PROVIDER)

        # Model configuration (inherited from config)
        model: str = ""  # Set based on provider's default

        # Property for provider with setter that updates state
        @property
        def provider(self) -> Provider:
            return self._provider

        @provider.setter
        def provider(self, value: Provider):
            self._provider = value
            self._sync_with_config()

        # Property for anthropic_api_key with setter that updates state
        @property
        def anthropic_api_key(self) -> str:
            return self.anthropic_api_key

        @anthropic_api_key.setter
        def anthropic_api_key(self, value: str):
            self.anthropic_api_key = value
            if self.provider == Provider.ANTHROPIC:
                self._update_api_key()

        # Property for openai_api_key with setter that updates state
        @property
        def openai_api_key(self) -> str:
            return self.openai_api_key

        @openai_api_key.setter
        def openai_api_key(self, value: str):
            self.openai_api_key = value
            if self.provider == Provider.OPENAI:
                self._update_api_key()

        def __init__(self, **data):
            super().__init__(**data)
            # Handle direct setting of API keys from initialization
            if "anthropic_api_key" in data:
                self.anthropic_api_key = data["anthropic_api_key"]
            if "openai_api_key" in data:
                self.openai_api_key = data["openai_api_key"]
            if "provider" in data:
                self._provider = data["provider"]
            self._sync_with_config()

        def _sync_with_config(self):
            """Synchronize valve state with config defaults"""
            # Get default model if not set
            if not self.model:
                self.model = config.get_default_model(self.provider)

            # Update API key based on provider
            self._update_api_key()

        def _update_api_key(self):
            """Update API key based on current provider"""
            Pipeline._provider = self.provider
            Pipeline._api_key = (
                self.anthropic_api_key
                if self.provider == Provider.ANTHROPIC
                else self.openai_api_key
            )

    def __init__(self):
        self.name = parser.get("pipeline", "name")
        self.type = "manifold"
        self.id = parser.get("pipeline", "id")

        # Initialize valves with environment variables and defaults
        self.valves = self.Valves(
            anthropic_api_key=os.getenv(
                "ANTHROPIC_API_KEY", "To use Anthropic, enter your API key here"
            ),
            openai_api_key=os.getenv(
                "OPENAI_API_KEY", "To use OpenAI, enter your API key here"
            ),
            provider=Provider(DEFAULT_PROVIDER),
        )

    async def on_startup(self):
        logger.debug(f"on_startup:{__name__}")

    async def on_shutdown(self):
        logger.debug(f"on_shutdown:{__name__}")

    async def on_valves_updated(self):
        """Handle valve updates by re-syncing configuration"""
        # This will be called when the web UI updates valves
        # Make sure we re-sync configuration to ensure _api_key is updated
        self.valves._sync_with_config()
        logger.debug("Valves updated and synced with config")

    def set_provider(self, provider: str):
        """Set the provider and update configuration"""
        try:
            self.valves.provider = Provider(provider.lower())
            self.valves.model = ""  # Reset model to use provider default
            self.valves._sync_with_config()
        except ValueError as e:
            raise ValueError(f"Invalid provider: {provider}")

    def set_model(self, model: str):
        """Set the model and validate against current provider"""
        if config.validate_model(model, self.valves.provider):
            self.valves.model = model
        else:
            raise ValueError(f"Unsupported model: {model}")

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
        return [model for model in models if len(self._api_key) >= 32]

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Execute bash commands through an LLM with tool integration."""
        logger.debug(f"Full body keys: {list(body.keys())}")
        # Disable logging if requested (e.g. when running from CLI)
        if body.get("disable_logging"):
            # Disable all logging at the root level
            logging.getLogger().setLevel(logging.ERROR)
            logger.disabled = True

        # Validate API key
        if not self._api_key or len(self._api_key) < 32:
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
            return "VMPilot Pipeline "

        # Handle provider selection and model validation
        try:
            # Set provider or model based on model_id
            try:
                if model_id and model_id.lower() in [p.value for p in Provider]:
                    self.set_provider(model_id)
                elif model_id:
                    self.set_model(model_id)
            except ValueError as e:
                error_msg = str(e)
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
                formatted_messages[-1]["content"][-1]["cache_control"] = {
                    "type": "ephemeral"
                }
            formatted_messages = formatted_messages[-1:]

            """ Set up the params for the process_messages function and run it in a separate thread. """

            def generate_responses():
                output_queue = queue.Queue()
                loop_done = threading.Event()

                """ Output callback to handle messages from the LLM """

                def output_callback(content: Dict):
                    logger.debug(f"Received content: {content}")
                    if content["type"] == "text":
                        logger.debug(f"Assistant: {content['text']}")
                        output_queue.put(content["text"])

                """ Output callback to handle tool messages: output from commands """

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
                            # we use 4 backticks to escape the 3 backticks that might be in the markdown
                            truncated_output += f"\n...\n````\n(and {len(output_lines) - TOOL_OUTPUT_LINES} more lines)\n"
                        output_queue.put(truncated_output)

                """ Run the sampling loop in a separate thread while waiting for responses """

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
                                api_key=self._api_key,
                                max_tokens=MAX_TOKENS,
                                temperature=TEMPERATURE,
                                disable_logging=body.get("disable_logging", False),
                                recursion_limit=RECURSION_LIMIT,
                                thread_id=getattr(self, "chat_id", None),
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

            """
            In a typical llm chat streaming means that the output is sent to the user as it is generated.
            In our case, we don't stream the individual tokens in the output, but we do stream the messages as they come.
            1. The llm's initial response.
            2. Tools' output.
            3. The llm's response to the tools' output.
            4. Etc.
            """
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
