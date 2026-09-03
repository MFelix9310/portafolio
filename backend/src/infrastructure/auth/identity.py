"""Identidad del administrador y contrato del verificador."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class AuthError(Exception):
    """Token ausente, invalido o de alguien que no es administrador."""


@dataclass(frozen=True, slots=True)
class AdminIdentity:
    user_id: str
    email: str | None = None
    role: str | None = None
    # Que verificador acepto el token; se registra en logs para auditoria.
    issued_by: str = "supabase"


class AdminTokenVerifier(ABC):
    @abstractmethod
    async def verify(self, token: str) -> AdminIdentity:
        """Devuelve la identidad o lanza AuthError. Nunca devuelve None."""
