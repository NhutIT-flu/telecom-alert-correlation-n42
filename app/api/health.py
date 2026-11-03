from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    """Liveness endpoint; readiness checks will be added with runtime dependencies."""
    return {"status": "UP", "service": "n42-api", "version": "0.1.0"}
