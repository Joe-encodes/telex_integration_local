from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, json, os
from datetime import datetime
import logging
from openai import OpenAI
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
def load_config():
    try:
        with open("config/integration.json", "r") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise HTTPException(status_code=500, detail="Config loading failed")

# Retrieve webhook URL
def get_webhook_url(channel_id):
    return f"https://ping.telex.im/v1/webhooks/{channel_id}"

# Send data to webhook
def send_to_webhook(webhook_url, backlinks, emails):
    try:
        message = f"New Backlinks Found: {len(backlinks)}\n" + "\n".join(
            f"{bl.get('title')} | {bl.get('link')} | {email[:50]}"
            for bl, email in zip(backlinks, emails)
        )
        
        response = requests.post(
            webhook_url,
            json={
                "event_name": "RawBacklinkData",
                "status": "success",
                "username": "DataBot",
                "message": message
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return False

# Get setting value by label
def get_setting_value(config, label, env_var=None):
    for setting in config["data"]["settings"]:
        if setting["label"] == label:
            value = setting.get("value", setting.get("default"))
            if value:
                return value
            break
    
    if env_var:
        return os.getenv(env_var)
    
    raise ValueError(f"Setting '{label}' not found in config and no environment variable provided")

# Find competitor backlinks using Google API
def find_competitor_backlinks(cx, google_api_key, sites, max_results=5):
    try:
        search_query = " OR ".join([f"link:{site}" for site in sites])
        url = f"https://www.googleapis.com/customsearch/v1?q={search_query}&key={google_api_key}&cx={cx}&num={max_results}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        logger.error(f"Failed to fetch competitor backlinks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch competitor backlinks")

# Draft personalized email using AI
def draft_email(prospect, aimlapi_key):
    if not aimlapi_key:
        raise ValueError("AIMLAPI Key is required for email drafting")
    
    try:
        client = OpenAI(
            api_key=aimlapi_key,
            base_url="https://api.aimlapi.com/v1"
        )

        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[{
                "role": "user",
                "content": f"Draft a personalized email for: {prospect['title']} ({prospect['link']})"
            }],
            temperature=0.7,
            max_tokens=256
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to draft email: {e}")
        raise HTTPException(status_code=500, detail="Failed to draft email")

# Interval tick endpoint
@app.post("/tick")
def tick():
    try:
        config = load_config()
        
        # Retrieve settings
        cx = get_setting_value(config, "Search Engine ID (CX)")
        google_api_key = get_setting_value(config, "Google API Key", "GOOGLE_API_KEY")
        aimlapi_key = get_setting_value(config, "AIMLAPI Key", "AIMLAPI_API_KEY")
        sites = get_setting_value(config, "Sites to Monitor").split(",")
        channel_id = get_setting_value(config, "Channel ID")
        
        # Find backlinks
        backlinks = find_competitor_backlinks(cx, google_api_key, sites)
        
        # Draft emails
        emails = []
        for bl in backlinks:
            try:
                email = draft_email(bl, aimlapi_key)
                emails.append(email)
            except Exception as e:
                logger.error(f"Failed to draft email: {e}")
                continue
        
        # Send to Telex
        if channel_id:
            webhook_url = get_webhook_url(channel_id)
            send_to_webhook(webhook_url, backlinks, emails)
        
        return {"message": "Success", "backlinks": backlinks, "emails": emails}
    except Exception as e:
        logger.error(f"Error in /tick: {e}")
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