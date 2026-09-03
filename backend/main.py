"""Punto de entrada.

    uv run uvicorn main:app --reload

Por defecto arranca con PERSISTENCE_BACKEND=json y AUTH_BACKEND=dev: responde con el
contenido real de `content/catalog.seed.json` sin ninguna infraestructura levantada.
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI

from src.infrastructure.config.container import build_container
from src.infrastructure.web.fastapi_app import create_app


def build() -> FastAPI:
    container = asyncio.run(build_container())
    return create_app(container)


app = build()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
