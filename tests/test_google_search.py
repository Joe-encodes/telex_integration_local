import pytest
from main import find_competitor_links, IntegrationSettings
import logging

@pytest.mark.asyncio
async def test_logging(monkeypatch, caplog):
    logger = logging.getLogger("main")
    
    with caplog.at_level(logging.ERROR, logger="main"):
        monkeypatch.setattr(
            "main.find_competitor_links",
            lambda settings: (_ for _ in ()).throw(Exception("Google API error"))
        )
        
        # Call the function
        settings = IntegrationSettings(
            google_api_key="test_key",
            search_query="test_query",
            result_limit=5,
            aimlapi_endpoint="http://test.endpoint",
            aimlapi_key="test_aiml_key"
        )
        
        await find_competitor_links(settings)
        
        # Assert logging output
        assert any("Google API error" in message for message in caplog.messages)
