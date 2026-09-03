"""Dispara la revalidacion ISR del front tras publicar desde el panel (D1)."""

from __future__ import annotations

from ...ports.revalidation import FrontendRevalidationPort, RevalidationResult

DEFAULT_PATHS: tuple[str, ...] = ("/", "/data", "/developer", "/civil-bim")


class RevalidateFrontend:
    def __init__(self, port: FrontendRevalidationPort) -> None:
        self._port = port

    async def execute(self, paths: tuple[str, ...] | None = None) -> RevalidationResult:
        return await self._port.revalidate(paths or DEFAULT_PATHS)
