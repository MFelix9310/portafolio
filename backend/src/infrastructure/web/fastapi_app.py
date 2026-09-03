"""Factoria de la aplicacion FastAPI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.container import Container
from .errors import register_error_handlers
from .routers.admin import create_admin_router
from .routers.health import create_health_router
from .routers.public import create_public_router

logger = logging.getLogger("app.web")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("arrancando")
    yield
    await app.state.container.close()
    logger.info("parado")


def create_app(container: Container) -> FastAPI:
    settings = container.settings
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = FastAPI(
        title="Portafolio Felix Ruiz M. - API",
        version="1.0.0",
        description="Backend hexagonal. Publico sin auth, /admin con JWT de Supabase.",
        lifespan=_lifespan,
    )
    app.state.container = container

    # CORS por env: el front vive en otro dominio y no se abre a '*' en produccion.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    register_error_handlers(app)

    # /health cuelga de la raiz y no lleva prefijo de version: es liveness, no API.
    app.include_router(create_health_router(container))
    app.include_router(create_public_router(container), prefix=settings.api_prefix)
    app.include_router(create_admin_router(container), prefix=settings.api_prefix)
    return app
