from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, json, os
from datetime import datetime

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
CONFIG_PATH = "config/integration.json"
def load_config():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)

# Retrieve webhook URL
def get_webhook_url(channel_id):
    url = f"https://backend-im.duckdns.org/webhooks/{channel_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("webhook_url")
    raise HTTPException(status_code=response.status_code, detail="Failed to get webhook URL")

# Send data to webhook
def send_to_webhook(webhook_url, payload):
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to send data to webhook")

# Interval tick endpoint
@app.post("/tick")
def tick():
    config = load_config()["data"]
    channel_id = config.get("channel_id")
    if not channel_id:
        raise HTTPException(status_code=400, detail="Missing channel_id in config")

    webhook_url = get_webhook_url(channel_id)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "message": "Interval tick executed"
    }
    send_to_webhook(webhook_url, payload)
    return {"message": "Tick executed successfully"}

# Health check endpoint
@app.get("/status")
def status():
    return {"message": "Integration is running"}

# Serve integration.json
@app.get("/integration.json")
def integration_json(request: Request):
    config = load_config()
    base_url = str(request.base_url).rstrip('/')
    config["data"]["descriptions"]["app_url"] = base_url
    return config
