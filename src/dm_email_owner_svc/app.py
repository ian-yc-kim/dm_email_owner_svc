import time
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(debug=True)

# Retrieve the configured logger
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        # Read request body for payload size
        body_bytes = await request.body()
        request._body = body_bytes
        payload_size = len(body_bytes)
    except Exception:
        payload_size = 0
    try:
        # Process the request
        response: Response = await call_next(request)
    except Exception as exc:
        logger.error("Unhandled exception during request", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    duration_ms = int((time.time() - start_time) * 1000)
    status_code = response.status_code
    # Log method, path, payload size, status code, and duration
    logger.info(
        f"{request.method} {request.url.path} | payload_size={payload_size} bytes | status_code={status_code} | duration_ms={duration_ms}"
    )
    return response

# add routers

# Test endpoints for middleware verification
@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.post("/echo")
async def echo(data: dict):
    return data

@app.get("/error")
async def error_endpoint():
    raise Exception("Test exception")
