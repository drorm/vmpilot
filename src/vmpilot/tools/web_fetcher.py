import asyncio
import logging
from typing import Optional

import aiohttp
from langchain.callbacks.manager import CallbackManagerForToolRun
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from vmpilot.config import diffbot_config

logger = logging.getLogger(__name__)

JINA_PROXY = "https://r.jina.ai/"
DIFFBOT_URL = "https://api.diffbot.com/v3/article"


async def fetch_with_jina(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                JINA_PROXY + url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "Verify you are human" in text or "captcha" in text.lower():
                        logger.info("[Jina] Blocked by captcha or anti-bot.")
                        return None
                    return text
                logger.debug(f"[Jina] Failed with status {resp.status}")
                return None
    except aiohttp.ClientError as e:
        logger.warning(f"[Jina] Network error: {e}")
        return None
    except asyncio.TimeoutError:
        logger.debug("[Jina] Request timed out.")
        return None
    except Exception as e:
        logger.warning(f"[Jina] Unexpected error: {e}")
        return None


async def fetch_with_diffbot(url):
    token = diffbot_config.get_token()
    if not token:
        logger.warning(
            "[Diffbot] No API token configured (set DIFFBOT_API_KEY in environment). Skipping Diffbot."
        )
        return None
    api_url = f"{DIFFBOT_URL}?token={token}&url={url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                api_url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "objects" in data and data["objects"]:
                        return data["objects"][0].get("text", "")
                    logger.info(f"[Diffbot] No article object found in response: {url}")
                    return None
                logger.warning(
                    f"[Diffbot] Failed with status {resp.status} and response: {await resp.text()}"
                )
                return None
    except aiohttp.ClientError as e:
        logger.warning(f"[Diffbot] Network error: {e}")
        return None
    except asyncio.TimeoutError:
        logger.warning("[Diffbot] Request timed out.")
        return None
    except Exception as e:
        logger.error(f"[Diffbot] Unexpected error: {e}")
        return None


async def fetch_with_playwright(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=10000)
            content = await page.inner_text("body")
            await browser.close()
            return content
    except PlaywrightTimeout:
        logger.info("[Playwright] Timeout loading page.")
        return None
    except Exception as e:
        logger.info(f"[Playwright error] {e}")
        return None


async def get_page_content(
    url, run_manager: Optional[CallbackManagerForToolRun] = None
):
    logger.info(f"get_page_content called with url: {url}, run_manager: {run_manager}")
    # Instead of using ContextVar directly, we'll use the run_manager to send updates

    async def send_progress(msg):
        logger.info(msg)
        if run_manager:
            logger.info(f"Sending progress update via run_manager for URL: {url}")
            await run_manager.on_text(msg + "\n")

    # Try Jina first (fastest)
    await send_progress(f"Attempting to fetch content from {url} using Jina...")
    content = await fetch_with_jina(url)
    if content:
        if "Verify you are human" in content or "captcha" in content.lower():
            await send_progress(
                "[!] Jina encountered a captcha, trying alternate methods..."
            )
            content = None
        else:
            await send_progress("[✓] Successfully retrieved content via Jina.")
            return content

    # Try Playwright next (handles JavaScript)
    await send_progress(
        "Jina failed or encountered captcha. Trying Playwright with JavaScript rendering..."
    )
    content = await fetch_with_playwright(url)
    if content:
        await send_progress("[✓] Successfully retrieved content via Playwright.")
        return content

    # Try Diffbot as a last resort (structured extraction)
    await send_progress(
        "Playwright failed. Trying Diffbot for structured content extraction..."
    )
    content = await fetch_with_diffbot(url)
    if content:
        await send_progress("[✓] Successfully retrieved content via Diffbot.")
        return content

    # All methods failed
    await send_progress(
        "[✗] All web content extraction methods failed. Unable to retrieve content."
    )
    return None
