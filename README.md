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
