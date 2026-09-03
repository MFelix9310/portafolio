"""Alta o modificacion de una subarea.

La clave solo es unica dentro de su area, tal y como declara el contrato con
`unique(area_id, key)`.
"""

from __future__ import annotations

from ....domain.entities.taxonomy import Subarea
from ....domain.repositories.taxonomy_repository import TaxonomyRepository
from ...errors import ConflictError


class SaveSubarea:
    def __init__(self, repository: TaxonomyRepository) -> None:
        self._repository = repository

    async def execute(self, subarea: Subarea) -> Subarea:
        siblings = await self._repository.list_subareas(subarea.area_key)
        clash = next(
            (s for s in siblings if s.key == subarea.key and s.id != subarea.id), None
        )
        if clash is not None:
            raise ConflictError(
                "subarea", "(area_id, key)", f"{subarea.area_key}/{subarea.key}"
            )
        return await self._repository.save_subarea(subarea)
