"""`/health`: sin auth, sin tocar la base."""

from __future__ import annotations

from fastapi import APIRouter

from ...config.container import Container


def create_health_router(container: Container) -> APIRouter:
    router = APIRouter()

    @router.get("/health", tags=["health"], summary="Liveness")
    async def health() -> dict[str, object]:
        return {
            "status": "ok",
            "environment": container.settings.environment.value,
            "persistence": container.settings.persistence_backend.value,
            "auth": container.settings.auth_backend.value,
        }

    return router
