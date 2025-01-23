from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from typing import Dict, Generator, Iterator, List, Union, Optional, Any, Sequence, Type
import anthropic
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


"""Custom chat model implementation with caching support."""


class CachingChatAnthropic(BaseChatModel):
    model_name: str = ("claude-3-5-sonnet-20241022",)
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: int = 30
    anthropic_api_key: Optional[str] = None
    model_kwargs: Dict[str, Any] = {}
    tools: List[BaseTool] = []
    tool_schemas: List[Dict[str, Any]] = []

    """Direct Anthropic implementation that bypasses LangChain's Anthropic wrapper."""

    def bind_tools(self, tools: Sequence[Type[BaseTool]]) -> "CachingChatAnthropic":
        """Bind tools to the model and prepare them for use with Anthropic API.

        Args:
            tools: Sequence of BaseTool classes to bind

        Returns:
            self: Returns the model instance for chaining
        """
        self.tools = [
            {
                "name": "bash",
                "description": """Execute bash commands in the system. Input should be a single command string. Examples:
                            - ls /path
                            - cat file.txt
                            - head -n 10 file.md
                            - grep pattern file
                            The output will be automatically formatted with appropriate markdown syntax.""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute",
                        }
                    },
                    "required": ["command"],
                },
            }
        ]

        """
        self.tool_schemas = []
        for tool_class in tools:
            try:
                # Handle both class and instance inputs
                tool = tool_class() if isinstance(tool_class, type) else tool_class

                # Get the tool's schema
                if hasattr(tool, "args"):
                    parameters = tool.args
                elif hasattr(tool, "args_schema"):
                    parameters = tool.args_schema.schema()
                else:
                    parameters = {}

                # Format tool schema according to Claude-3's expectations
                schema = {
                    "name": tool.name,  # Required at top level
                                        "function": {
                                                "name": tool.name,
                                                "description": tool.description,
                                                "input_schema": 
                                                "type": "object",
                                                "properties": {
                                                        "command": {
                                                                "type": "string",
                                                                "description": "The shell command to execute"
                                                                }
                                                        },
                                                "required": ["command"]
                                                },
                }

                self.tools.append(tool)
                self.tool_schemas.append(schema)

            except Exception as e:
                logger.error(f"Error instantiating tool {tool_class}: {e}")
                continue
            """

        # Store schemas in model kwargs for API calls
        self.model_kwargs["tools"] = self.tool_schemas
        return self

    def _llm_type(self) -> str:
        """Return identifier for this LLM."""
        return "anthropic_direct"

    def __init__(
        self,
        model: str = model_name,
        temperature: float = temperature,
        max_tokens: int = max_tokens,
        anthropic_api_key: Optional[str] = None,
        timeout: int = 30,
        model_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Initialize with Anthropic-specific parameters."""
        super().__init__(
            model_name=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"),
            **kwargs,
            model_kwargs=model_kwargs or {},
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override _generate to use direct Anthropic API calls."""

        client = anthropic.Anthropic(api_key=self.anthropic_api_key)

        # Convert LangChain messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            if msg.type == "system":
                # System messages go into the system parameter
                system = [
                    {
                        "type": "text",
                        "text": msg.content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                role = "assistant" if msg.type == "ai" else "user"
                anthropic_messages.append(
                    {
                        "role": role,
                        "content": [
                            {
                                "type": "text",
                                "text": msg.content,
                            }
                        ],
                    }
                )
                # if it's the last message add cache cache control
                if msg == messages[-1]:
                    anthropic_messages[-1]["content"][0]["cache_control"] = {
                        "type": "ephemeral"
                    }
        # Make direct API call
        # logger.info(f"Making API call with {system} ")
        # logger.info(f"Making API call with {anthropic_messages} ")
        response = client.messages.create(
            model=self.model_name,
            messages=anthropic_messages,
            system=system,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            tools=self.tools,
        )

        # response = client.messages.create(**create_params)

        # logger.info(f"API call complete with {response}")
        logger.info(f"usage: {response.usage}")
        # INFO:vmpilot.custom_chat:API call complete with Message(id='msg_01UPmJbxzjV45ddVZuKFSAAM',
        # logger.info(f"Response content: {response.content}")

        content = []
        tool_calls = []

        # Process text content and tool calls
        if response.content:
            for block in response.content:
                logger.debug(f"Block content: {block}")
                if block.type == "text":
                    content.append(block.text)
                elif block.type == "tool_use":
                    logger.debug(f"Tool use: {block.name}")
                    tool_calls.append(
                        {
                            "type": "function",
                            "id": block.id,
                            "function": {"name": block.name, "arguments": block.input},
                        }
                    )

        # Create the message content
        message_content = "\n".join(content)

        # Create the message with both content and tool calls
        message = AIMessage(
            content=message_content,
            additional_kwargs={"tool_calls": tool_calls} if tool_calls else {},
        )

        generation = ChatGeneration(
            message=message,
            generation_info={"finish_reason": response.stop_reason},
        )

        return ChatResult(generations=[generation])
