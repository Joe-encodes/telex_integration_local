from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, json, os
from datetime import datetime
import logging

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
google_api_key = os.getenv("GOOGLE_API_KEY")
aimlapi_api_key = os.getenv("AIMLAPI_API_KEY")

# Validate API keys
if not google_api_key or not aimlapi_api_key:
    logger.error("Missing API keys. Ensure GOOGLE_API_KEY and AIMLAPI_API_KEY are set.")
    raise RuntimeError("Missing API keys")

app = FastAPI()

# CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load config
CONFIG_PATH = "config/integration.json"  # Updated file name
def load_config():
    try:
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise HTTPException(status_code=500, detail="Failed to load config")


# Retrieve webhook URL
def get_webhook_url(channel_id):
    url = f"https://telex.im/dashboard/channels/webhooks/{channel_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("webhook_url")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch webhook URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webhook URL")

# Send data to webhook
def send_to_webhook(webhook_url, payload):
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send data to webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to send data to webhook")

# Get setting value by label
def get_setting_value(config, label):
    for setting in config["data"]["settings"]:
        if setting["label"] == label:
            return setting.get("value", setting.get("default"))
    logger.error(f"Setting '{label}' not found in config")
    raise HTTPException(status_code=400, detail=f"Setting '{label}' not found in config")

# Find competitor backlinks using Google API
def find_competitor_backlinks(domain):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q=link:{domain}&key={google_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch competitor backlinks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch competitor backlinks")

# Draft personalized email using AI (mock implementation)
def draft_email(prospect):
    try:
        # Mock AI API call
        url = "https://api.aimlapi.com/draft-email"
        headers = {"Authorization": f"Bearer {aimlapi_api_key}"}
        payload = {"prospect": prospect}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("email")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to draft email: {e}")
        raise HTTPException(status_code=500, detail="Failed to draft email")

# Interval tick endpoint
@app.post("/tick")
def tick():
    try:
        logger.debug("Starting /tick endpoint")
        
        # Load config
        config = load_config()
        logger.debug(f"Loaded config: {json.dumps(config, indent=2)}")
        
        # Retrieve settings
        search_query = get_setting_value(config, "Search Query")
        result_limit = get_setting_value(config, "Result Limit")
        aimlapi_endpoint = get_setting_value(config, "AIMLAPI Endpoint")
        
        logger.debug(f"Search Query: {search_query}")
        logger.debug(f"Result Limit: {result_limit}")
        logger.debug(f"AIMLAPI Endpoint: {aimlapi_endpoint}")
        
        # Your logic here...
        
        logger.debug("Completed /tick endpoint")
        return {"message": "Tick executed successfully"}
    except Exception as e:
        logger.error(f"Error in /tick endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Health check endpoint
@app.get("/status")
def status():
    return {"message": "Integration is running"}

# Serve integration_config.json
@app.get("/integration.json")
def integration_json(request: Request):
    try:
        config = load_config()
        base_url = str(request.base_url).rstrip('/')
        config["data"]["descriptions"]["app_url"] = base_url
        return config
    except Exception as e:
        logger.error(f"Error in /integration.json endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")