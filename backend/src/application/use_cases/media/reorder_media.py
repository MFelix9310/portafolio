"""Reordenacion de la galeria de un proyecto."""

from __future__ import annotations

from ....domain.entities.media import MediaAsset
from ....domain.repositories.media_repository import MediaRepository
from ...dto.commands import ReorderCommand


class ReorderMedia:
    def __init__(self, repository: MediaRepository) -> None:
        self._repository = repository

    async def execute(self, command: ReorderCommand) -> list[MediaAsset]:
        return await self._repository.reorder(command.ordered_ids)
