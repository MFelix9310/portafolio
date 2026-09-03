"""Proyecto: raiz del agregado de catalogo."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ..value_objects.localized_text import LocalizedText
from ..value_objects.publication_status import PublicationStatus
from ..value_objects.slug import Slug
from ..value_objects.taxonomy_keys import AreaKey, SubareaKey, TaxonomyTag
from .media import MediaAsset


@dataclass(slots=True)
class Project:
    slug: Slug
    title: LocalizedText
    id: UUID | None = None
    summary: LocalizedText | None = None
    body: LocalizedText | None = None
    technologies: tuple[str, ...] = field(default_factory=tuple)
    project_url: str | None = None
    repository_url: str | None = None
    thumbnail_path: str | None = None
    legacy_id: int | None = None
    status: PublicationStatus = PublicationStatus.DRAFT
    display_order: int = 0
    taxonomy: tuple[TaxonomyTag, ...] = field(default_factory=tuple)
    media: tuple[MediaAsset, ...] = field(default_factory=tuple)

    @property
    def areas(self) -> frozenset[AreaKey]:
        return frozenset(tag.area for tag in self.taxonomy)

    def subareas_of(self, area: AreaKey) -> frozenset[SubareaKey]:
        return frozenset(tag.subarea for tag in self.taxonomy if tag.area == area)

    def belongs_to(self, area: AreaKey | None, subarea: SubareaKey | None) -> bool:
        """Predicado unico de pertenencia; la subarea siempre se evalua dentro del area."""
        candidates = self.taxonomy
        if area is not None:
            candidates = tuple(tag for tag in candidates if tag.area == area)
        if subarea is not None:
            candidates = tuple(tag for tag in candidates if tag.subarea == subarea)
        return bool(candidates) if (area or subarea) else True
