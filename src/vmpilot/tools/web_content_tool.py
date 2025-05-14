import asyncio
import logging
from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

import vmpilot.worker_llm as worker_llm
from vmpilot.config import config, web_fetch_config
from vmpilot.tools.web_fetcher import get_page_content

logger = logging.getLogger(__name__)

WEB_CONTENT_CLEAN_SYSTEM_PROMPT = """
You are a web content cleaning agent for a search assistant. Your job is to remove ALL navigation, cookie messages, ads, unrelated links, headers, footers, and any repeated boilerplate from the input web page text. 
Keep only the main content of the page, which is usually the article or main text, but could also be a product description or similar.
Do NOT summarize or rewrite—just return the cleaned content, preserving details and markdown/code formatting.
"""


async def clean_web_content(
    raw_content: str, url: str, search_query: Optional[str] = None
) -> str:
    """Clean raw web content using the LLM worker with a focused system prompt."""
    if not raw_content or not raw_content.strip():
        return ""
    if not url:
        url = "(unknown)"
    prompt = f"""Clean the following web page content from {url}.

Search query (if relevant): {search_query or ''}

Raw Content:
----------------
{raw_content}
----------------
"""
    try:
        logger.info(f"Cleaning content from {url} with LLM worker...")
        cleaned = await worker_llm.run_worker_async(
            prompt=prompt,
            system_prompt=WEB_CONTENT_CLEAN_SYSTEM_PROMPT,
            temperature=getattr(config, "temperature", 0.2),
        )
        logger.info(f"Cleaned content from {url}:\n{cleaned}")
        return cleaned.strip()
    except Exception as e:
        logging.error(f"Web content cleaning failed: {e}")
        return raw_content  # fallback to uncleaned


class Input(BaseModel):
    """Input schema for web content fetch."""

    url: str = Field(description="The URL to fetch content from.")
    max_lines: Optional[int] = Field(
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
        max_lines: Optional[int] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Synchronous version - not used, we use _arun instead."""
        raise NotImplementedError("Use the async _arun method instead")

    async def _arun(
        self,
        url: str,
        max_lines: Optional[int] = None,
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
            raw_content = await get_page_content(url, run_manager=run_manager)

            if not raw_content:
                return f"[✗] Unable to fetch web content for URL: {url}"

            # Always apply formatting and truncation, even if skipping LLM cleaning
            show_raw = getattr(config, "web_content_show_raw", False)
            maxl = max_lines or getattr(web_fetch_config, "max_lines", 100)

            def trim(text):
                lines = text.strip().splitlines()
                display = "\n".join(lines[:maxl])
                if len(lines) > maxl:
                    display += f"\n...\n(Truncated, {len(lines)-maxl} more lines)"
                return display

            if len(raw_content.splitlines()) < 100:
                cleaned_content = raw_content
            else:
                if run_manager:
                    await run_manager.on_text("Cleaning web content...\n")
                cleaned_content = await clean_web_content(raw_content, url)

            if show_raw:
                formatted_result = (
                    "\n[Raw fetched content]\n````\n" + trim(raw_content) + "\n````\n\n"
                    "[Cleaned content]\n````\n" + trim(cleaned_content) + "\n````\n"
                )
            else:
                formatted_result = "\n````\n" + trim(cleaned_content) + "\n````\n"

            if run_manager:
                await run_manager.on_text("Content cleaning complete.\n")
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
