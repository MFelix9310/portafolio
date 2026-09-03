"""Dependencias de FastAPI: acceso al contenedor y autorizacion del panel."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..auth.identity import AdminIdentity, AuthError
from ..config.container import Container

bearer_scheme = HTTPBearer(auto_error=False, description="JWT de Supabase")


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


async def require_admin(
    container: ContainerDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AdminIdentity:
    """Verifica de verdad el token. Sin `Authorization` valido no se pasa de aqui."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="falta la cabecera Authorization: Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await container.verifier.verify(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


AdminDep = Annotated[AdminIdentity, Depends(require_admin)]
