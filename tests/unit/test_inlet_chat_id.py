import asyncio

import pytest

from vmpilot.vmpilot import Pipeline


class TestInletChatID:
    @pytest.fixture
    def pipeline(self):
        """Create a fresh Pipeline instance for each test."""
        return Pipeline()

    @pytest.mark.asyncio(scope="function")
    async def test_inlet_stores_chat_id(self, pipeline):
        """Test that inlet stores chat_id from the request body."""
        test_chat_id = "test123"
        request_body = {"chat_id": test_chat_id, "other_field": "value"}

        result = await pipeline.inlet(request_body)

        # Verify that chat_id is stored on the pipeline instance
        assert pipeline.chat_id == test_chat_id
        # Verify that inlet returns the original body
        assert result == request_body

    @pytest.mark.asyncio(scope="function")
    async def test_inlet_no_chat_id(self, pipeline):
        """Test inlet behavior when no chat_id is provided."""
        request_body = {"other_field": "value"}

        result = await pipeline.inlet(request_body)

        # Verify that chat_id is None
        assert pipeline.chat_id is None
        # Verify that inlet returns the original body
        assert result == request_body

    @pytest.mark.asyncio(scope="function")
    async def test_inlet_empty_chat_id(self, pipeline):
        """Test inlet behavior with empty chat_id."""
        request_body = {"chat_id": "", "other_field": "value"}

        result = await pipeline.inlet(request_body)

        # Verify that empty chat_id is stored
        assert pipeline.chat_id == ""
        # Verify that inlet returns the original body
        assert result == request_body

    @pytest.mark.asyncio(scope="function")
    async def test_inlet_with_user_info(self, pipeline):
        """Test inlet with user information provided."""
        test_chat_id = "test123"
        request_body = {"chat_id": test_chat_id, "other_field": "value"}
        user_info = {"id": "user123", "name": "Test User"}

        result = await pipeline.inlet(request_body, user_info)

        # Verify that chat_id is stored
        assert pipeline.chat_id == test_chat_id
        # Verify that inlet returns the original body
        assert result == request_body

    @pytest.mark.asyncio(scope="function")
    async def test_inlet_overrides_existing_chat_id(self, pipeline):
        """Test that inlet overrides existing chat_id."""
        # Set an initial chat_id
        pipeline.chat_id = "initial123"

        # New chat_id in request
        test_chat_id = "override456"
        request_body = {"chat_id": test_chat_id}

        result = await pipeline.inlet(request_body)

        # Verify that chat_id is overridden
        assert pipeline.chat_id == test_chat_id
