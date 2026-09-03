"""Borrado de un recurso de media: primero la fila, luego el fichero del bucket."""

from __future__ import annotations

from uuid import UUID

from ....domain.repositories.media_repository import MediaRepository
from ...errors import NotFoundError
from ...ports.media_storage import MediaStoragePort


class DeleteMedia:
    def __init__(self, repository: MediaRepository, storage: MediaStoragePort) -> None:
        self._repository = repository
        self._storage = storage

    async def execute(self, media_id: UUID, *, purge_file: bool = True) -> None:
        asset = await self._repository.get(media_id)
        if asset is None:
            raise NotFoundError("media", media_id)
        await self._repository.delete(media_id)
        if purge_file:
            # Un fichero huerfano es preferible a una fila apuntando a la nada.
            await self._storage.delete(asset.storage_path)
