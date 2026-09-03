"""Puerto de revalidacion ISR del front.

El contrato define `POST /admin/revalidate` pero no su puerto. Se declara aqui porque
es una salida de aplicacion hacia un sistema externo (Vercel), no una regla de negocio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RevalidationResult:
    requested_paths: tuple[str, ...]
    accepted: bool
    detail: str | None = None


class FrontendRevalidationPort(ABC):
    @abstractmethod
    async def revalidate(self, paths: tuple[str, ...]) -> RevalidationResult: ...
