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
    try:
        # Correct URL structure
        url = f"https://ping.telex.im/v1/webhooks/{channel_id}"
        
        # Make the API request
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Extract the webhook URL from the response
        webhook_url = response.json().get("data", {}).get("webhook_url")
        if not webhook_url:
            logger.warning(f"No webhook URL found for channel ID: {channel_id}")
            return None
        
        return webhook_url
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch webhook URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webhook URL")

# Send data to webhook
def send_to_webhook(webhook_url, payload):
    try:
        # Make the API request
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send data to webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to send data to webhook")

# Get setting value by label
def get_setting_value(config, label, env_var=None):
    """
    Retrieve a setting value by its label from the configuration.
    If the setting is not found or is empty, fall back to the environment variable.
    """
    for setting in config["data"]["settings"]:
        if setting["label"] == label:
            value = setting.get("value", setting.get("default"))
            if value:  # If the user provided a value, use it
                return value
            break  # Exit the loop if the setting is found
    
    # If no value is found in the settings, fall back to the environment variable
    if env_var:
        return os.getenv(env_var)
    
    raise ValueError(f"Setting '{label}' not found in config and no environment variable provided")

# Find competitor backlinks using Google API
def find_competitor_backlinks(cx, google_api_key, sites, max_results=5):
    try:
        # Construct the search query
        search_query = " OR ".join([f"link:{site}" for site in sites])
        
        # Make the API request with a limit on the number of results
        url = f"https://www.googleapis.com/customsearch/v1?q={search_query}&key={google_api_key}&cx={cx}&num={max_results}"
        logger.debug(f"API Request: {url}")
        response = requests.get(url)
        logger.debug(f"API Response: {response.status_code} - {response.text}")
        response.raise_for_status()
        
        # Extract and log the items
        items = response.json().get("items", [])
        logger.debug(f"Found {len(items)} backlinks")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch competitor backlinks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch competitor backlinks")

# Draft personalized email using AI (mock implementation)


def draft_email(prospect, aimlapi_key):
    try:
        # Initialize the OpenAI client with the AIML API base URL and key
        client = OpenAI(
            api_key=aimlapi_key,
            base_url="https://api.aimlapi.com/v1"  # Use the versioned URL
        )

        # Define the system and user prompts
        system_prompt = "You are a helpful assistant that drafts personalized emails."
        user_prompt = f"Draft a personalized email for the following prospect: {prospect}"

        # Make the API call
        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",  # Use a supported model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,  # Adjust for creativity
            max_tokens=256,   # Limit the response length
        )

        # Extract the generated email content
        email_content = completion.choices[0].message.content
        return email_content

    except Exception as e:
        logger.error(f"Failed to draft email: {e}")
        raise HTTPException(status_code=500, detail="Failed to draft email")

# Interval tick endpoint
@app.post("/tick")
def tick():
    try:
        logger.debug("Starting /tick endpoint")
        
        # Load config
        config = load_config()
        
        # Retrieve settings with environment variables as fallback
        cx = get_setting_value(config, "Search Engine ID (CX)")
        google_api_key = get_setting_value(config, "Google API Key", env_var="GOOGLE_API_KEY")
        aimlapi_key = get_setting_value(config, "AIMLAPI Key", env_var="AIMLAPI_KEY")
        sites = get_setting_value(config, "Sites to Monitor").split(",")
        channel_id = get_setting_value(config, "Channel ID")
        
        logger.debug(f"Search Engine ID (CX): {cx}")
        logger.debug(f"Google API Key: {google_api_key}")
        logger.debug(f"AIMLAPI Key: {aimlapi_key}")
        logger.debug(f"Sites to Monitor: {sites}")
        logger.debug(f"Channel ID: {channel_id}")
        
        # Step 1: Find competitor backlinks
        backlinks = find_competitor_backlinks(cx, google_api_key, sites, max_results=5)
        
        if not backlinks:
            logger.warning("No backlinks found. Skipping email drafting and webhook sending.")
            return {"message": "No backlinks found", "backlinks": [], "emails": []}
        
        # Step 2: Draft personalized emails
        emails = []
        for backlink in backlinks:
            try:
                email = draft_email(backlink, aimlapi_key)
                emails.append(email)
            except HTTPException as e:
                logger.error(f"Failed to draft email for backlink {backlink}: {e}")
                continue  # Skip this backlink and continue with the next one
        
        # Step 3: Send results to Telex
        if channel_id:
            webhook_url = get_webhook_url(channel_id)
            
            if webhook_url:
                payload = {
                    "channel_id": channel_id,
                    "event_name": "Backlink Monitoring Results",
                    "message": "Backlink monitoring results",
                    "status": "success",
                    "username": "backlink-monitor"
                }
                send_to_webhook(webhook_url, payload)
            else:
                logger.warning("No webhook URL found. Skipping sending data to Telex.")
        else:
            logger.warning("No Channel ID found. Skipping sending data to Telex.")
        
        logger.debug("Completed /tick endpoint")
        return {"message": "Tick executed successfully", "backlinks": backlinks, "emails": emails}
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