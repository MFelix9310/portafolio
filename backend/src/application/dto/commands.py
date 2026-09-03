"""Comandos de entrada que no son entidades de dominio."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ...domain.value_objects.localized_text import LocalizedText
from ...domain.value_objects.publication_status import PublicationStatus
from ...domain.value_objects.taxonomy_keys import AreaKey


@dataclass(frozen=True, slots=True)
class ReorderCommand:
    ordered_ids: tuple[UUID, ...]

    def __post_init__(self) -> None:
        if len(set(self.ordered_ids)) != len(self.ordered_ids):
            raise ValueError("reorder recibio ids duplicados")


@dataclass(frozen=True, slots=True)
class NewMessageCommand:
    """Alta desde el formulario publico. `created_at` lo pone el ClockPort."""

    name: str
    email: str
    body: str
    subject: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateAreaCommand:
    """Edicion parcial de un area. `key` viaja solo para poder rechazar su cambio."""

    area_id: UUID
    name: "LocalizedText | None" = None
    blurb: "LocalizedText | None" = None
    display_order: int | None = None
    status: "PublicationStatus | None" = None
    key: "AreaKey | None" = None


@dataclass(frozen=True, slots=True)
class UploadUrlCommand:
    filename: str
    content_type: str
