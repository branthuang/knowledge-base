from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_health
from app.core.redis import check_redis_health

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    db_healthy = await check_db_health()
    redis_healthy = await check_redis_health()

    status = "healthy" if (db_healthy and redis_healthy) else "degraded"

    return {
        "status": status,
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "services": {
            "database": "connected" if db_healthy else "disconnected",
            "redis": "connected" if redis_healthy else "disconnected",
        },
    }
