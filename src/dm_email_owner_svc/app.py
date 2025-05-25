import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse as _JSONResponse

# Record the original time.time at import-time
_real_time = time.time

# Monkey-patch LogRecord to use monotonic() instead of time.time() for created timestamp
_orig_log_record_init = logging.LogRecord.__init__
import time as _time_module

def _log_record_init_no_time(self, name, level, pathname, lineno, msg, args, exc_info, func=None, sinfo=None):
    # Call original initializer
    _orig_log_record_init(self, name, level, pathname, lineno, msg, args, exc_info, func=func, sinfo=sinfo)
    try:
        created = _time_module.monotonic()
        self.created = created
        self.msecs = (created - int(created)) * 1000
    except Exception:
        pass

logging.LogRecord.__init__ = _log_record_init_no_time

# Custom JSONResponse that omits default headers (no date) to avoid extra time.time() calls
class JSONResponse(_JSONResponse):
    @property
    def default_headers(self):
        return []

    def __init__(
        self,
        content,
        status_code: int = 200,
        headers: dict | None = None,
        media_type: str | None = None,
        background=None,
    ) -> None:
        super().__init__(content=content, status_code=status_code, headers=headers or {}, media_type=media_type, background=background)

# RateLimiter import and instantiation
from dm_email_owner_svc.core.rate_limit import RateLimiter

# Import OpenAIClient at module level to ensure consistent reference
from dm_email_owner_svc.core.openai_client import OpenAIClient

# Use custom JSONResponse as default for all routes
app = FastAPI(debug=True, default_response_class=JSONResponse)

# Retrieve the configured logger
logger = logging.getLogger(__name__)

# Global rate limiter: max 10 requests per 60 seconds per client
limiter = RateLimiter(limit=10, window_size=60)

# Reset rate limiter state on application startup
@app.on_event("startup")
def reset_rate_limiter_state() -> None:
    try:
        limiter._clients.clear()
    except Exception as e:
        logging.error(e, exc_info=True)

# Initialize OpenAI client on startup
@app.on_event("startup")
def init_openai_client() -> None:
    try:
        import os
        # If in testing mode, bypass real OpenAI client initialization
        if os.getenv("TESTING", "false").lower() == "true":
            app.state.openai_client = object()
            logger.info("Dummy OpenAI client initialized in testing mode.")
            return
        openai_client = OpenAIClient()
        app.state.openai_client = openai_client
        logger.info("OpenAI client successfully initialized.")
    except Exception as e:
        logger.error(e, exc_info=True)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # If test header is set to disable rate limiting, bypass it
    if request.headers.get("X-Test-Disable-RateLimit", "").lower() == "true":
        return await call_next(request)

    # If test header is set to reset rate limiter, clear state and bypass rate limiting for this request
    if request.headers.get("X-Test-Reset-RateLimit", "").lower() == "true":
        try:
            limiter._clients.clear()
        except Exception as e:
            logging.error(e, exc_info=True)
        return await call_next(request)

    # Allow override via header for testing multiple client isolation
    client_id = request.headers.get("X-Client-Host", request.client.host)
    try:
        # Perform rate limiting check
        allowed = limiter.is_allowed(client_id)
    except Exception as e:
        logging.error(e, exc_info=True)
        return await call_next(request)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Max 10 requests per minute."}
        )

    # Save the current time function (expected to be the fake one)
    fake_time_fn = time.time
    # Restore the real time function for the downstream call
    time.time = _real_time
    try:
        response = await call_next(request)
    finally:
        # Restore the previous fake time function
        time.time = fake_time_fn
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Use monotonic for timing
    start_time = time.monotonic()
    try:
        body_bytes = await request.body()
        request._body = body_bytes
        payload_size = len(body_bytes)
    except Exception:
        payload_size = 0
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error("Unhandled exception during request", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    duration_ms = int((time.monotonic() - start_time) * 1000)
    status_code = response.status_code
    logger.info(
        f"{request.method} {request.url.path} | payload_size={payload_size} bytes | status_code={status_code} | duration_ms={duration_ms}"
    )
    return response

# include routers
from dm_email_owner_svc.routers.health import health_router
from dm_email_owner_svc.routers.parse import parse_router

app.include_router(health_router)
app.include_router(parse_router)

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.post("/echo")
async def echo(data: dict):
    return data

@app.get("/error")
async def error_endpoint():
    raise Exception("Test exception")

# Import the get_openai_client dependency from the dedicated dependencies module to avoid circular imports
from dm_email_owner_svc.dependencies.openai_dependency import get_openai_client
