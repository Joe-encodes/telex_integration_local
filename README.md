```markdown
# Telex Interval Integration: Google Backlink Monitor

This FastAPI application monitors competitor backlinks using Google search, generates personalized outreach emails via AIMLAPI, and sends daily summaries to Telex with one-click email actions.

## Features

-   **Backlink Monitoring:** Uses Google Custom Search API to find backlinks to specified competitor websites.
-   **AI-Powered Email Drafting:** Generates personalized outreach emails using AIMLAPI.
-   **Telex Integration:** Sends daily summaries to a specified Telex channel with formatted messages.
-   **Configurable Settings:** Customizable via `config/integration.json` and environment variables.
-   **Error Handling and Logging:** Robust error handling with detailed logging for debugging.
-   **Rate Limiting:** Implements retry logic with exponential backoff for Google API rate limits.

## Requirements

-   Python 3.10+
-   FastAPI, requests, python-dotenv, openai, and uvicorn.
-   Google Custom Search API Key (`GOOGLE_API_KEY`).
-   AIMLAPI API Key (`AIMLAPI_API_KEY`).
-   Telex Channel ID.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_folder>
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Create `.env` file:**

    Create a `.env` file in the root directory with your API keys and base webhook URL:

    ```plaintext
    GOOGLE_API_KEY=your_google_api_key
    AIMLAPI_API_KEY=your_aimlapi_api_key
    ```

4.  **Configure `config/integration.json`:**

    Ensure `config/integration.json` is correctly configured with your settings (see Configuration section below).

## Configuration

Modify `config/integration.json` to set the following parameters:

```json
{
  "data": {
    "settings": [
      {
        "label": "interval",
        "type": "text",
        "required": true,
        "default": "* * * * "
      },
      {
        "label": "Channel ID",
        "type": "text",
        "required": true,
        "default": "your_channel_id"
      },
      {
        "label": "Search Engine ID (CX)",
        "type": "text",
        "required": true,
        "default": "your_cx_id"
      },
      {
        "label": "Google API Key",
        "type": "text",
        "required": false,
        "default": ""
      },
      {
        "label": "AIMLAPI Key",
        "type": "text",
        "required": false,
        "default": ""
      },
      {
        "label": "Sites to Monitor",
        "type": "text",
        "required": true,
        "default": "[competitor1.com](https://www.google.com/search?q=competitor1.com),competitor2.com"
      },
      {
        "label": "Result Limit",
        "type": "number",
        "required": true,
        "default": 10
      }
    ],
    "tick_url": "your_public_url/tick",
    "target_url": ""
  }
}
```

-   `interval`: Cron syntax for scheduling the `/tick` endpoint (e.g., `* * * * *` for every minute).
-   `Channel ID`: The Telex channel ID to send summaries to.
-   `Search Engine ID (CX)`: Your Google Custom Search Engine ID.
-   `Google API Key` and `AIMLAPI Key`: Your API keys (can also be set via `.env`).
-   `Sites to Monitor`: Comma-separated list of competitor websites.
-   `Result Limit`: Maximum number of search results to retrieve.
-   `tick_url`: The public URL of your `/tick` endpoint.
-   `target_url`: Optional target for additional requests.

## Running the Application

1.  **Run locally:**

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

2.  **Run with Docker:**

    ```bash
    docker build -t telex-interval-integration .
    docker run -d -p 8000:8000 telex-interval-integration
    ```

## Testing

1.  **Test `/integration.json` endpoint:**

    ```bash
    curl http://localhost:8000/integration.json
    ```

2.  **Trigger `/tick` manually:**

    ```bash
    curl -X POST http://localhost:8000/tick -H "Content-Type: application/json" -d '{"channel_id": "your_channel_id"}'
    ```

3.  **Check `/status`:**

    ```bash
    curl http://localhost:8000/status
    ```

## Deployment

Ensure the application is deployed on a server with a public URL (e.g., `https://your-app-url.com`). Update the `tick_url` in `config/integration.json` with your deployed URL.

## Debugging and Troubleshooting

1.  **Verify Configuration:** Double-check `.env` and `config/integration.json` for correct API keys, channel IDs, and other settings.
2.  **Firewall Rules:** Ensure your firewall allows incoming requests on port 8000 (or the port you configured).
3.  **Logging:** Check the application logs for detailed error messages. The application uses `logging.DEBUG` for verbose output.
4.  **API Rate Limits:** If you encounter issues with Google API, check the logs for rate limit warnings and ensure your retry logic is working.
5.  **Environment Variables:** Ensure that the environment variables are correctly loaded from the `.env` file.
6.  **Telex Webhook:** Validate the Telex channel id, and ensure the webhook is correctly recieving the data.
7.  **AIMLAPI:** If emails are not generated, check the aimlapi key, and confirm that the AIMLAPI service is running.

## Code Structure

-   `main.py`: Contains the FastAPI application logic.
-   `config/integration.json`: Configuration file for the integration.
-   `requirements.txt`: List of Python dependencies.
-   `.env`: Stores environment variables (API keys).

## Key Functions

-   `load_config()`: Loads configuration from `config/integration.json`.
-   `get_webhook_url(channel_id)`: Constructs the Telex webhook URL.
-   `send_to_webhook(webhook_url, backlinks, emails)`: Sends data to the Telex webhook.
-   `find_competitor_backlinks(cx, google_api_key, sites, max_results=5, max_retries=3)`: Fetches backlinks using Google Custom Search API.
-   `draft_email(prospect, aimlapi_key)`: Generates personalized emails using AIMLAPI.
-   `tick()`: Main function that fetches backlinks, generates emails, and sends data to Telex.
-   `/integration.json`: Endpoint that returns the integration configuration.
-   `/status`: Health check endpoint.

```
