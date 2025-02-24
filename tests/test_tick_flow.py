import pytest
from unittest.mock import AsyncMock
from main import tick_handler, TickPayload

@pytest.mark.asyncio
async def test_tick_flow(monkeypatch):
    test_payload = TickPayload(return_url="https://telex.example.com/webhook", channel_id="01951917-8a60-7fd7-bec2-9c2639d0f806")
    mock_get = AsyncMock(return_value=AsyncMock(status_code=200, json=AsyncMock(return_value={"items": [{"title": "Test", "link": "https://example.com"}]})))
    mock_post = AsyncMock(return_value=AsyncMock(status_code=200, json=AsyncMock(return_value={"status": "success"})))
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    response = await tick_handler(test_payload)
    assert response["status"] == "Report sent successfully"
