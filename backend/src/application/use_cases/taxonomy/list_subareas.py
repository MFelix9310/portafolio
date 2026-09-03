"""Listado plano de subareas, opcionalmente acotado a un area."""

from __future__ import annotations

from ....domain.entities.taxonomy import Subarea
from ....domain.repositories.taxonomy_repository import TaxonomyRepository
from ....domain.services.catalog import ordered
from ....domain.value_objects.taxonomy_keys import AreaKey


class ListSubareas:
    def __init__(self, repository: TaxonomyRepository) -> None:
        self._repository = repository

    async def execute(self, area: AreaKey | None = None) -> list[Subarea]:
        return ordered(await self._repository.list_subareas(area))
