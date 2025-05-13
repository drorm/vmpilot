import asyncio
import logging
from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from vmpilot.config import web_fetch_config
from vmpilot.tools.web_fetcher import get_page_content


class Input(BaseModel):
    """Input schema for web content fetch."""

    url: str = Field(description="The URL to fetch content from.")
    max_lines: int = Field(
        description="Number of lines to return (optional, defaults from config)",
        default=None,
    )


class WebContentTool(BaseTool):
    name: str = "web_content_fetch"
    description: str = (
        "Fetch the full readable content of a web page. Input is a URL. Output is clean text up to max_lines. "
        "Typically, Use this after a search to get the content from a result."
    )
    args_schema: Type[BaseModel] = Input

    def _run(
        self,
        url: str,
        max_lines: int = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Synchronous version - not used, we use _arun instead."""
        raise NotImplementedError("Use the async _arun method instead")

    async def _arun(
        self,
        url: str,
        max_lines: int = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        if not web_fetch_config.enabled:
            return "Web content fetching is disabled in configuration."
        try:
            # Send initial progress update
            if run_manager:
                await run_manager.on_text(f"Starting web content fetch from {url}...\n")
            else:
                logging.warning(
                    "No run_manager provided, progress updates will not be streamed."
                )

            # Run the content fetching process - now we can use await directly
            content = await get_page_content(url, run_manager=run_manager)

            if not content:
                return f"[✗] Unable to fetch web content for URL: {url}"

            # Process the content
            lines = content.strip().splitlines()
            maxl = max_lines or getattr(web_fetch_config, "max_lines", 100)
            display = "\n".join(lines[:maxl])
            if len(lines) > maxl:
                display += f"\n...\n(Truncated, {len(lines) - maxl} more lines)"

            # Send completion update
            if run_manager:
                await run_manager.on_text(
                    f"Content fetch complete. Retrieved {len(lines)} lines.\n"
                )

            formatted_result = f"\n````\n{display}\n````\n\n"
            return formatted_result
        except Exception as e:
            error_msg = f"Error fetching web content: {str(e)}"
            if run_manager:
                await run_manager.on_text(f"Error: {error_msg}\n")
            return error_msg

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Web page URL to fetch"},
                    "max_lines": {
                        "type": "integer",
                        "description": "Max lines to return (optional)",
                    },
                },
                "required": ["url"],
            },
        }
