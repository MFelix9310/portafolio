"""Alta o modificacion de un recurso de media.

Impone `project_media unique (project_id, storage_path)` (addendum A5). Sin esta
comprobacion los dos adaptadores divergen: el JSON acepta dos assets apuntando al
mismo fichero dentro del mismo proyecto y el de Supabase falla en el upsert con un
error de Postgres que el panel no sabe interpretar.
"""

from __future__ import annotations

from ....domain.entities.media import MediaAsset
from ....domain.repositories.media_repository import MediaRepository
from ...errors import ConflictError, ValidationError


class SaveMedia:
    def __init__(self, repository: MediaRepository) -> None:
        self._repository = repository

    async def execute(self, asset: MediaAsset) -> MediaAsset:
        if asset.project_id is None:
            raise ValidationError("un recurso de media necesita project_id")

        siblings = await self._repository.list_for_project(asset.project_id)
        clash = next(
            (
                other
                for other in siblings
                if other.storage_path == asset.storage_path and other.id != asset.id
            ),
            None,
        )
        if clash is not None:
            raise ConflictError(
                "recurso de media", "(project_id, storage_path)", asset.storage_path
            )
        return await self._repository.save(asset)
