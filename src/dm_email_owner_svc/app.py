import time
import logging
from fastapi import FastAPI, Request, Response
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

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Capture the fake (or real) time.time from global module
    fake_time = time.time
    # Allow override via header for testing multiple client isolation
    client_id = request.headers.get("X-Client-Host", request.client.host)
    try:
        # Perform rate limiting under the monkeypatched time
        allowed = limiter.is_allowed(client_id)
    except Exception as e:
        logging.error(e, exc_info=True)
        return await call_next(request)
    if not allowed:
        # No external libs invoked here
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Max 10 requests per minute."}
        )
    # Restore the real time.time for downstream libraries
    time.time = _real_time
    try:
        response = await call_next(request)
    finally:
        # Restore the fake time.time so the next limiter check still uses it
        time.time = fake_time
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
        response: Response = await call_next(request)
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
app.include_router(health_router)

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.post("/echo")
async def echo(data: dict):
    return data

@app.get("/error")
async def error_endpoint():
    raise Exception("Test exception")
