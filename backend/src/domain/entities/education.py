"""Formacion academica. Sin slug: el contrato no lo define para esta tabla."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ..value_objects.localized_text import LocalizedText
from ..value_objects.publication_status import PublicationStatus


@dataclass(slots=True)
class Education:
    institution: LocalizedText
    title: LocalizedText
    id: UUID | None = None
    description: LocalizedText | None = None
    graduation_year: int | None = None
    legacy_id: int | None = None
    status: PublicationStatus = PublicationStatus.DRAFT
    display_order: int = 0

    def __post_init__(self) -> None:
        if self.graduation_year is not None and not 1900 <= self.graduation_year <= 2200:
            raise ValueError(f"graduation_year fuera de rango: {self.graduation_year}")
