"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis import get_redis, RedisClient

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """
    Readiness check - verify all dependencies are available.
    Used by Kubernetes readiness probe.
    """
    checks = {
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        if redis.redis:
            await redis.redis.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "unhealthy: not connected"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"

    # Overall status
    is_healthy = all(status == "healthy" for status in checks.values())

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "checks": checks,
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - verify application is running.
    Used by Kubernetes liveness probe.
    """
    return {"status": "alive"}
