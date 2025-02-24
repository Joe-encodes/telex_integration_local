# import asyncio
# from main import find_competitor_links, IntegrationSettings

# async def test_google_search():
# 	settings = IntegrationSettings(
# 		google_api_key="AIzaSyAAVZ9o88x-Y-7De8W17C-ED7AEtiZV4ug",
# 		search_query="telex competitors",
# 		result_limit=5,
# 		aimlapi_endpoint="http://localhost:8000/aimlapi",  # Use test endpoint if available
# 		aimlapi_key="279e7ea7f4bb4504a24d8c091aa632a7"
# 	)
# 	result = await find_competitor_links(settings)
# 	print("Google Search Results:", result)

# if __name__ == "__main__":
#   	asyncio.run(test_google_search())

import pytest
from main import load_settings, find_competitor_links, generate_outreach_email, tick_handler, TickPayload, IntegrationSettings, health_check
from unittest.mock import AsyncMock
from fastapi import HTTPException
import logging, json


logger = logging.getLogger(__name__)

# Test Priority Calculation
# def test_priority_calculation():
#     assert calculate_priority({"link": "https://example.com/article"}) == 3.6

# Test Configuration Loading
# def load_settings() -> IntegrationSettings:
#     try:
#         with open("config/integration.json") as f:
#             config = json.load(f)
#         label_to_field = {
#             "Google API Key": "google_api_key",
#             "Search Query": "search_query",
#             "Result Limit": "result_limit",
#             "AIMLAPI Endpoint": "aimlapi_endpoint",
#             "AIMLAPI API Key": "aimlapi_key"
#         }
#         settings_map = {label_to_field[item["label"]]: item["default"] for item in config if item["label"] in label_to_field}
#         return IntegrationSettings(**settings_map)
#     except Exception as e:
#         logger.error(f"Failed to load config: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Configuration error")
def mock_load_settings():
    return IntegrationSettings(
        google_api_key="dummy_key",
        search_query="dummy_query",
        result_limit=5,
        aimlapi_endpoint="http://localhost:8000/aimlapi",
        aimlapi_key="dummy_api_key"
    )

monkeypatch.setattr("main.load_settings", mock_load_settings)



# Test Google Search API
@pytest.mark.asyncio
async def test_find_competitor_links(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient.get", AsyncMock(return_value=AsyncMock(status_code=200, json=AsyncMock(return_value={"items": [{"link": "https://example.com"}]}))))
    settings = IntegrationSettings(google_api_key="", search_query="", result_limit=1, aimlapi_endpoint="", aimlapi_key="")
    results = await find_competitor_links(settings)
    assert len(results) == 1

def test_load_settings():
    settings = load_settings()
    assert isinstance(settings, IntegrationSettings)
    assert settings.google_api_key != ""


@pytest.mark.asyncio
async def test_generate_outreach_email(monkeypatch):
    async_mock_post = AsyncMock(return_value=AsyncMock(status_code=200, json=AsyncMock(return_value={"text": "Hello"})))
    monkeypatch.setattr("httpx.AsyncClient.post", async_mock_post)

    settings = IntegrationSettings(
    google_api_key="dummy_key",
    search_query="dummy_query",
    result_limit=5,
    aimlapi_endpoint="http://localhost:8000/aimlapi",
    aimlapi_key="dummy_api_key"
)
    result = await generate_outreach_email(settings, {"title": "Example"}, "Telex")
    assert result == "Hello"



# Test `/tick` Endpoint
@pytest.mark.asyncio
async def test_tick_handler(monkeypatch):
    async_mock_get = AsyncMock(return_value=AsyncMock(status_code=200, json=AsyncMock(return_value={"items": [{"title": "Test", "link": "https://example.com"}]})))
    async_mock_post = AsyncMock(return_value=AsyncMock(status_code=200))

    monkeypatch.setattr("httpx.AsyncClient.get", async_mock_get)
    monkeypatch.setattr("httpx.AsyncClient.post", async_mock_post)

    response = await tick_handler(TickPayload(return_url="https://telex.example.com/webhook", channel_id="test_channel"))
    assert response["status"] == "Report sent successfully"


# Test `/health` Endpoint
@pytest.mark.asyncio
async def test_health_check():
    assert health_check() == {"status": "operational"}