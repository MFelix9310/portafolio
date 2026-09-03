"""Experiencia profesional."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from ..value_objects.date_range import DateRange
from ..value_objects.localized_text import LocalizedText
from ..value_objects.publication_status import PublicationStatus
from ..value_objects.slug import Slug


@dataclass(slots=True)
class Experience:
    slug: Slug
    company: LocalizedText
    position: LocalizedText
    period: DateRange
    id: UUID | None = None
    description: LocalizedText | None = None
    keywords: tuple[str, ...] = field(default_factory=tuple)
    company_logo_path: str | None = None
    thumbnail_path: str | None = None
    legacy_id: int | None = None
    is_current: bool = False
    status: PublicationStatus = PublicationStatus.DRAFT
    display_order: int = 0

    def __post_init__(self) -> None:
        # Una experiencia vigente con fecha de fin es un dato incoherente, y el
        # contenido heredado trae ambos campos sueltos.
        if self.is_current and self.period.end is not None:
            raise ValueError("una experiencia vigente no puede tener fecha de fin")

    @property
    def start_date(self) -> date:
        return self.period.start

    @property
    def end_date(self) -> date | None:
        return self.period.end
