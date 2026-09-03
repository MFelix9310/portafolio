"""Perfil: fila unica (singleton) con la identidad publica de Felix."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ..value_objects.localized_text import LocalizedText
from ..value_objects.publication_status import PublicationStatus


@dataclass(slots=True)
class Profile:
    name: str
    headline: LocalizedText
    bio: LocalizedText
    id: UUID | None = None
    photo_path: str | None = None
    professional_photo_path: str | None = None
    # El contrato no lista status para profile, pero la regla 1 de RLS lo exige
    # para toda tabla de contenido. Por defecto publicado: el sitio sin perfil no existe.
    status: PublicationStatus = PublicationStatus.PUBLISHED

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("profile.name es obligatorio")
