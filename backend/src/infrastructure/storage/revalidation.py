"""Adaptadores de revalidacion ISR del front."""

from __future__ import annotations

import httpx

from ...application.ports.revalidation import (
    FrontendRevalidationPort,
    RevalidationResult,
)

REQUEST_TIMEOUT = httpx.Timeout(5.0, connect=2.0)


class HttpFrontendRevalidation(FrontendRevalidationPort):
    """Llama al webhook de revalidacion de Vercel."""

    def __init__(self, url: str, secret: str) -> None:
        self._url = url
        self._secret = secret

    async def revalidate(self, paths: tuple[str, ...]) -> RevalidationResult:
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(
                    self._url,
                    json={"paths": list(paths)},
                    headers={"x-revalidate-secret": self._secret},
                )
        except httpx.HTTPError as exc:
            # El fallo del front no debe tumbar la publicacion en el panel.
            return RevalidationResult(paths, accepted=False, detail=str(exc))
        return RevalidationResult(
            paths,
            accepted=response.is_success,
            detail=None if response.is_success else f"HTTP {response.status_code}",
        )


class NoopRevalidation(FrontendRevalidationPort):
    """Sin URL configurada no hay front que revalidar; se registra y ya."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    async def revalidate(self, paths: tuple[str, ...]) -> RevalidationResult:
        self.calls.append(paths)
        return RevalidationResult(paths, accepted=False, detail="revalidacion no configurada")
