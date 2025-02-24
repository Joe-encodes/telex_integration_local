# Telex Interval Integration

This FastAPI integration monitors competitor backlinks and sends daily summaries to Telex with one-click email actions.

## Features
- Monitors backlinks using Google search
- Generates personalized outreach emails via AIMLAPI
- Sends daily summaries to Telex
- Configurable via `config/integration.json`

## Requirements
- Python 3.10+
- FastAPI, `requests`, and `schedule` modules
- Google API Key and AIMLAPI API Key

## Installation
```bash
# Clone the repository
git clone <repository_url>
cd <repository_folder>

# Install dependencies
pip install -r requirements.txt

# Create `.env` file with:
GOOGLE_API_KEY=your_google_api_key
AIMLAPI_API_KEY=your_aimlapi_api_key
BASE_WEBHOOK_URL=https://telex-platform.com/webhooks/feed

# Ensure `config/integration.json` is correctly configured
```

## Configuration
Modify `config/integration.json` to set:
- `tick_url`: Your app’s public `/tick` endpoint
- `target_url`: Optional target for additional requests
- `interval`: Cron syntax for schedule
- `google_api_key`, `aimlapi_api_key`, and search parameters

## Running the Application
```bash
# Run the app locally
uvicorn main:app --host 0.0.0.0 --port 8000

# OR with Docker
docker build -t telex-interval-integration .
docker run -d -p 8000:8000 telex-interval-integration
```

## Testing
```bash
# Test `/integration.json` endpoint
curl http://localhost:8000/integration.json

# Trigger `/tick` manually
curl -X POST http://localhost:8000/tick -H "Content-Type: application/json" -d '{"channel_id": "your_channel_id"}'

# Check `/status`
curl http://localhost:8000/status
```

## Deployment
Ensure the app is accessible via a public URL like `https://backend-im.duckdns.org`.

## Troubleshooting
- Verify `.env` and `config/integration.json` are correctly configured
- Ensure firewall rules allow incoming requests on port 8000
- Check logs for detailed error messages

For more information, refer to the integration’s source code.
