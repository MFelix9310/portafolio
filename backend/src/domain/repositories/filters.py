"""Criterios de consulta que viajan del caso de uso al puerto."""

from __future__ import annotations

from dataclasses import dataclass

from ..value_objects.publication_status import PublicationStatus
from ..value_objects.taxonomy_keys import AreaKey, SubareaKey


@dataclass(frozen=True, slots=True)
class ProjectFilter:
    """`status=None` significa 'todos'; solo las rutas de admin lo usan asi."""

    area: AreaKey | None = None
    subarea: SubareaKey | None = None
    status: PublicationStatus | None = PublicationStatus.PUBLISHED

    def __post_init__(self) -> None:
        if self.subarea is not None and self.area is None:
            raise ValueError("subarea requiere area")

    @property
    def include_drafts(self) -> bool:
        return self.status is None or self.status is PublicationStatus.DRAFT

    @classmethod
    def public(
        cls, area: AreaKey | None = None, subarea: SubareaKey | None = None
    ) -> "ProjectFilter":
        return cls(area=area, subarea=subarea, status=PublicationStatus.PUBLISHED)


@dataclass(frozen=True, slots=True)
class ContentFilter:
    """Filtro comun del resto de recursos, que solo se segmentan por estado."""

    status: PublicationStatus | None = PublicationStatus.PUBLISHED

    @property
    def include_drafts(self) -> bool:
        return self.status is None or self.status is PublicationStatus.DRAFT

    @classmethod
    def public(cls) -> "ContentFilter":
        return cls(status=PublicationStatus.PUBLISHED)

    @classmethod
    def everything(cls) -> "ContentFilter":
        return cls(status=None)
