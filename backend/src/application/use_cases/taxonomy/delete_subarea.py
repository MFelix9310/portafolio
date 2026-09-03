"""Borrado de una subarea.

El puerto expone un unico `delete` para toda la taxonomia, asi que este caso de uso
comprueba antes que el id sea de una subarea. Un id de area se rechaza: las tres
areas son rutas del frontend y borrarlas dejaria la ruta viva y sin datos.
"""

from __future__ import annotations

from uuid import UUID

from ....domain.repositories.taxonomy_repository import TaxonomyRepository
from ...errors import ForbiddenOperationError, NotFoundError


class DeleteSubarea:
    def __init__(self, repository: TaxonomyRepository) -> None:
        self._repository = repository

    async def execute(self, subarea_id: UUID) -> None:
        if any(area.id == subarea_id for area in await self._repository.list_areas()):
            raise ForbiddenOperationError(
                "las areas no se pueden borrar: son rutas fijas del frontend"
            )
        if not any(sub.id == subarea_id for sub in await self._repository.list_subareas()):
            raise NotFoundError("subarea", subarea_id)
        if not await self._repository.delete(subarea_id):
            raise NotFoundError("subarea", subarea_id)
