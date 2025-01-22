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
    """Direct Anthropic implementation that bypasses LangChain's Anthropic wrapper."""

    def bind_tools(self, tools: Sequence[Type[BaseTool]]) -> "CachingChatAnthropic":
        """Bind tools to the model.

        Args:
            tools: List of tool classes to bind to the model.

        Returns:
            The model with bound tools.
        """
        # For Anthropic models, we don't need to do anything special with the tools
        # They are handled by the agent framework
        return self

    model_name: str = ("claude-3-5-sonnet-20241022",)
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: int = 30
    anthropic_api_key: Optional[str] = None
    model_kwargs: Dict[str, Any] = {}

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
    ) -> str:
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
                                "cache_control": {"type": "ephemeral"},
                            }
                        ],
                    }
                )
        # Make direct API call
        logger.info(f"Making API call with {system} ")
        logger.info(f"Making API call with {anthropic_messages} ")
        response = client.messages.create(
            model=self.model_name,
            messages=anthropic_messages,
            system=system,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        logger.info(f"API call complete with {response} ")
        generation = ChatGeneration(
            message=AIMessage(content=response.content[0].text),
            generation_info={"finish_reason": response.stop_reason},
        )

        return ChatResult(generations=[generation])
