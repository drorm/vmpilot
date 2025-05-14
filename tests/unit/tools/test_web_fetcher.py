import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

import vmpilot.tools.web_fetcher as web_fetcher


# --- Improved aiohttp mock ---
class DummyResponse:
    def __init__(self, status=200, text="some content"):
        self.status = status
        self._text = text

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class DummyClientSession:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def get(self, url, timeout=None):
        return self._response


# --- End improved aiohttp mock ---


def test_module_exists():
    assert hasattr(web_fetcher, "fetch_with_jina")


@pytest.mark.asyncio
async def test_fetch_with_jina_success(monkeypatch):
    class DummyResponse:
        def __init__(self, status=200, text="good content without captcha"):
            self.status = status
            self._text = text

        async def text(self):
            return self._text

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class DummyGetCM:
        def __init__(self, resp):
            self.resp = resp

        async def __aenter__(self):
            return self.resp

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, timeout=None):
            return DummyGetCM(
                DummyResponse(status=200, text="good content without captcha")
            )

    monkeypatch.setattr(
        aiohttp, "ClientSession", lambda *args, **kwargs: DummySession()
    )
    monkeypatch.setattr(aiohttp, "ClientTimeout", lambda total=None: None)
    result = await web_fetcher.fetch_with_jina("sometesturl.com")
    assert result == "good content without captcha"


@pytest.mark.asyncio
async def test_fetch_with_jina_captcha(monkeypatch):
    resp = DummyResponse(status=200, text="captcha challenge here!")

    class SessionCM:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        def get(self, url, timeout=None):
            class GetCM:
                async def __aenter__(self2):
                    return resp

                async def __aexit__(self2, *a):
                    pass

            return GetCM()

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: SessionCM())
    result = await web_fetcher.fetch_with_jina("sometesturl.com")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_with_jina_non_200(monkeypatch):
    resp = DummyResponse(status=404, text="not found")

    class SessionCM:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        def get(self, url, timeout=None):
            class GetCM:
                async def __aenter__(self2):
                    return resp

                async def __aexit__(self2, *a):
                    pass

            return GetCM()

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: SessionCM())
    result = await web_fetcher.fetch_with_jina("sometesturl.com")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_with_jina_exception(monkeypatch):
    class BoomSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, timeout=None):
            class GetCM:
                async def __aenter__(self2):
                    raise Exception("boom")

                async def __aexit__(self2, *a):
                    pass

            return GetCM()

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: BoomSession())
    result = await web_fetcher.fetch_with_jina("sometesturl.com")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_with_diffbot(monkeypatch):
    dummy_json = {"objects": [{"text": "diffbot says hi"}]}

    class DummyResp:
        status = 200

        async def json(self):
            return dummy_json

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, params=None, timeout=None):
            return DummyResp()

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: DummySession())
    result = await web_fetcher.fetch_with_diffbot("http://test.com")
    assert result == "diffbot says hi"


@pytest.mark.asyncio
async def test_fetch_with_diffbot_no_objects(monkeypatch):
    dummy_json = {"objects": []}

    class DummyResp:
        status = 200

        async def json(self):
            return dummy_json

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, params=None, timeout=None):
            return DummyResp()

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: DummySession())
    result = await web_fetcher.fetch_with_diffbot("http://test.com")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_with_diffbot_exception(monkeypatch):
    class BoomSession:
        async def __aenter__(self):
            raise Exception("boom")

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: BoomSession())
    result = await web_fetcher.fetch_with_diffbot("http://test.com")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_with_playwright_success(monkeypatch):
    # Simulate a successful playwright fetch matching exact async context
    class DummyPage:
        async def goto(self, url, timeout):
            return None

        async def content(self):
            return "<html>main content</html>"

        async def close(self):
            pass

    class DummyContext:
        async def new_page(self):
            return DummyPage()

        async def close(self):
            pass

    class DummyBrowser:
        async def new_context(self):
            return DummyContext()

        async def close(self):
            pass

    class DummyChromium:
        async def launch(self):
            return DummyBrowser()

    class DummyP:
        @property
        def chromium(self):
            return DummyChromium()

    class AsyncPlaywrightCM:
        async def __aenter__(self):
            return DummyP()

        async def __aexit__(self, exc_type, exc, tb):
            pass

    def fake_async_playwright():
        return AsyncPlaywrightCM()

    monkeypatch.setattr(web_fetcher, "async_playwright", fake_async_playwright)
    result = await web_fetcher.fetch_with_playwright("http://test.com")
    assert result is not None and "main content" in result


@pytest.mark.asyncio
async def test_fetch_with_playwright_fail(monkeypatch):
    class DummyPW:
        async def __aenter__(self):
            raise Exception("fail to launch")

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(web_fetcher, "async_playwright", lambda: DummyPW())
    result = await web_fetcher.fetch_with_playwright("http://test.com")
    assert result is None
