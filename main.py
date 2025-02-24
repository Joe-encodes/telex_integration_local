from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import httpx
import json
import logging
from typing import Dict, Any

app = FastAPI()
security = HTTPBearer()

# Logging Configuration
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Data Models
class TickPayload(BaseModel):
    return_url: str
    channel_id: str

class IntegrationSettings(BaseModel):
    google_api_key: str
    search_query: str
    result_limit: int
    aimlapi_endpoint: str
    aimlapi_key: str

# Load Configuration
def load_settings() -> IntegrationSettings:
    try:
        with open("config/integration.json") as f:
            config = json.load(f)
        settings_map = {item["label"]: item["default"] for item in config}
        return IntegrationSettings(**settings_map)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Configuration error")

# Google Search
async def find_competitor_links(settings: IntegrationSettings):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.google_api_key,
                    "cx": "b6df5883a068940c8",
                    "q": settings.search_query,
                    "num": settings.result_limit
                }
            )
            response.raise_for_status()
            return (await response.json()).get("items", [])
    except httpx.HTTPStatusError as e:
        logger.error(f"Google API error: {e.response.text}", exc_info=True)
        return []

# Priority Calculation
def calculate_priority(item: Dict[str, Any]) -> float:
    return len(item.get("link", "")) * 0.1

# AIMLAPI Email Generation
async def generate_outreach_email(settings: IntegrationSettings, site: Dict, competitor: str) -> str:
    try:
        prompt = f"Write a short outreach email to {site.get('title', 'the website')} about using an alternative to {competitor}. Page: {site.get('link')}."
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.aimlapi_endpoint,
                headers={"Authorization": f"Bearer {settings.aimlapi_key}"},
                json={"prompt": prompt, "max_tokens": 300}
            )
            response.raise_for_status()
            return response.json().get("text", "").strip()
    except Exception as e:
        logger.error(f"Email generation error: {str(e)}", exc_info=True)
        return ""

# API Endpoints
@app.post("/tick")
async def tick_handler(payload: TickPayload, token: str = Depends(security)):
    try:
        settings = load_settings()
        results = await find_competitor_links(settings)
        if not results:
            return {"status": "No links found"}

        prioritized = sorted([
            {"item": r, "priority": calculate_priority(r)} for r in results
        ], key=lambda x: x["priority"], reverse=True)[:settings.result_limit]

        outreach_data = []
        for item in prioritized:
            competitor = "Datadog" if "datadoghq" in item["item"].get("link", "") else "New Relic"
            email_content = await generate_outreach_email(settings, item["item"], competitor)
            outreach_data.append({
                "site": item["item"].get("title"),
                "url": item["item"].get("link"),
                "email": email_content,
                "priority": item["priority"],
                "actions": [{"type": "button", "text": "📨 Send Email", "value": email_content}]
            })

        async with httpx.AsyncClient() as client:
            response = await client.post(payload.return_url, json={
                "event_name": "Daily Backlink Report",
                "message": f"Found {len(outreach_data)} prospects",
                "status": "success",
                "username": "Backlink Bot",
                "data": outreach_data
            })
            response.raise_for_status()

        return {"status": "Report sent successfully"}

    except Exception as e:
        logger.error(f"Tick handler error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/target")
async def target_handler(request: Request, token: str = Depends(security)):
    payload = await request.json()
    logger.info(f"Received channel update: {payload}")
    return {"status": "received"}

@app.get("/health")
async def health_check():
    return {"status": "operational"}

# Run Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)