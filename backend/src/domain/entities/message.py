"""Mensaje del formulario de contacto. Solo el admin lo lee (RLS regla 3)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

# Validacion de frontera: barata a proposito, no pretende implementar RFC 5322.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")

MAX_BODY_LENGTH = 5000


@dataclass(slots=True)
class Message:
    name: str
    email: str
    body: str
    created_at: datetime
    id: UUID | None = None
    subject: str | None = None
    read: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("message.name es obligatorio")
        if not _EMAIL_RE.match(self.email or ""):
            raise ValueError(f"email invalido: {self.email!r}")
        if not self.body.strip():
            raise ValueError("message.body es obligatorio")
        if len(self.body) > MAX_BODY_LENGTH:
            raise ValueError(f"message.body supera {MAX_BODY_LENGTH} caracteres")

    def mark_read(self) -> None:
        self.read = True
