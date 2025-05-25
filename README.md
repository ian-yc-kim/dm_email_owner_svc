# dm_email_owner_svc

## Logging

This service uses non-blocking logging configured via Python's standard logging module in a background thread:

- Logging setup is defined in `src/dm_email_owner_svc/core/logging.py` in the `configure_logging()` function.
- Logs are emitted asynchronously using `QueueHandler` and `QueueListener` to avoid blocking the main application threads.

To enable logging, call `configure_logging()` at application startup (e.g., in `src/dm_email_owner_svc/main.py`).

Example:

```python
from dm_email_owner_svc.core.logging import configure_logging
import logging

def main():
    configure_logging()
    # Optionally adjust log level or format
    logging.getLogger().setLevel(logging.DEBUG)
    # Start the application
```

## Health Check

The service provides a simple health check endpoint to verify that it is running.

### Request

```bash
curl -X GET http://localhost:8000/health
```

### Response

```json
{
  "status": "ok"
}
```

## OpenAI Client Configuration

Configure the OpenAI client by setting the following environment variables:

- **OPENAI_API_KEY**: (required) Your OpenAI API key.
- **OPENAI_MODEL_NAME**: (optional) Model name to use (default: `gpt-4o-mini`).
- **OPENAI_TIMEOUT**: (optional) Request timeout in seconds (default: `30`).
- **OPENAI_MAX_RETRIES**: (optional) Number of retry attempts on failure (default: `3`).

## Usage Example

Below is an example of injecting the OpenAI client into a FastAPI route using dependency injection:

```python
from fastapi import Depends, FastAPI
from dm_email_owner_svc.core.openai_client import OpenAIClient, get_openai_client

app = FastAPI()

@app.post("/chat")
async def chat_endpoint(
    messages: list[dict],
    client: OpenAIClient = Depends(get_openai_client)
):
    result = client.chat_completion(messages)
    return result
```

### Parse Endpoint

- **HTTP Method and URL**: `POST /parse`
- **Request Body Schema**:
  ```json
  {
    "html_content": "<div>John Doe <john@example.com></div>",
    "emails": ["john@example.com"]
  }
  ```
- **Example Request**:
  ```bash
  curl -X POST http://localhost:8000/parse \
       -H 'Content-Type: application/json' \
       -d '{
         "html_content": "<div>John Doe <john@example.com></div>",
         "emails": ["john@example.com"]
       }'
  ```
- **Example Successful Response** (HTTP 200):
  ```json
  [
    {"email": "john@example.com", "owner": "John Doe"}
  ]
  ```
- **Error Responses**:
  - **422 Unprocessable Entity**: Validation error for malformed request payload.
  - **502 Bad Gateway**: Downstream API failure or response parsing error.
