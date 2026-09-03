"""Publicaciones: libros, capitulos y articulos."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ..value_objects.localized_text import LocalizedText
from ..value_objects.publication_status import PublicationStatus
from ..value_objects.slug import Slug

_KIND_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

# El contrato no cierra la lista de kinds; estas son las que existen hoy.
KNOWN_PUBLICATION_KINDS: tuple[str, ...] = (
    "book",
    "chapter",
    "article",
    "paper",
    "report",
)


@dataclass(slots=True)
class Publication:
    slug: Slug
    kind: str
    title: LocalizedText
    id: UUID | None = None
    authors: LocalizedText | None = None
    venue: LocalizedText | None = None
    abstract: LocalizedText | None = None
    published_on: date | None = None
    doi: str | None = None
    isbn: str | None = None
    url: str | None = None
    pdf_path: str | None = None
    thumbnail_path: str | None = None
    legacy_id: int | None = None
    status: PublicationStatus = PublicationStatus.DRAFT
    display_order: int = 0

    def __post_init__(self) -> None:
        if not _KIND_RE.match(self.kind or ""):
            raise ValueError(f"kind de publicacion invalido: {self.kind!r}")
