"""Puerto de la taxonomia: areas y subareas."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.taxonomy import Area, Subarea
from ..value_objects.taxonomy_keys import AreaKey


class TaxonomyRepository(ABC):
    @abstractmethod
    async def list_areas(self) -> list[Area]:
        """Areas ordenadas, cada una con sus subareas cargadas."""

    @abstractmethod
    async def list_subareas(self, area: AreaKey | None = None) -> list[Subarea]: ...

    @abstractmethod
    async def save_area(self, area: Area) -> Area: ...

    @abstractmethod
    async def save_subarea(self, subarea: Subarea) -> Subarea: ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Borra un area o una subarea por id; el contrato define un unico `delete`."""
