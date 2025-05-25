from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("/health")
async def health() -> dict[str, str]:
    """
    Health check endpoint returning service status.
    """
    return {"status": "ok"}
