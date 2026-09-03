"""Canal de contacto publicado: linkedin, github, email y similares."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from ..value_objects.publication_status import PublicationStatus

_KIND_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


@dataclass(slots=True)
class Contact:
    kind: str
    value: str
    id: UUID | None = None
    status: PublicationStatus = PublicationStatus.DRAFT
    display_order: int = 0

    def __post_init__(self) -> None:
        if not _KIND_RE.match(self.kind or ""):
            raise ValueError(f"kind de contacto invalido: {self.kind!r}")
        if not self.value.strip():
            raise ValueError("contact.value es obligatorio")
