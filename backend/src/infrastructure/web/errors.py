"""Traduccion de errores de dominio y aplicacion a codigos HTTP.

El dominio lanza `ValueError` cuando una invariante no se cumple y la aplicacion
lanza `ApplicationError`. Ninguno de los dos conoce HTTP; la traduccion vive aqui.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ...application.errors import (
    ConflictError,
    ForbiddenOperationError,
    NotFoundError,
    StorageError,
    ValidationError,
)

logger = logging.getLogger("app.web")


def _payload(code: str, message: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_payload("not_found", str(exc)),
        )

    @app.exception_handler(ValidationError)
    async def _invalid(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_payload("invalid_input", str(exc)),
        )

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        # 409 y no 422: el cuerpo enviado es correcto, lo que choca es el estado.
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_payload("conflict", str(exc)),
        )

    @app.exception_handler(ForbiddenOperationError)
    async def _forbidden(_: Request, exc: ForbiddenOperationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=_payload("forbidden_operation", str(exc)),
        )

    @app.exception_handler(ValueError)
    async def _domain_invariant(_: Request, exc: ValueError) -> JSONResponse:
        # Una invariante del dominio rota es entrada mal formada, no un fallo interno.
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_payload("invalid_input", str(exc)),
        )

    @app.exception_handler(StorageError)
    async def _storage(_: Request, exc: StorageError) -> JSONResponse:
        logger.error("fallo de storage: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_payload("storage_unavailable", str(exc)),
        )
