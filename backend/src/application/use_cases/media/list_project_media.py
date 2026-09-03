"""Media de un proyecto."""

from __future__ import annotations

from uuid import UUID

from ....domain.entities.media import MediaAsset
from ....domain.repositories.media_repository import MediaRepository
from ....domain.services.catalog import ordered


class ListProjectMedia:
    def __init__(self, repository: MediaRepository) -> None:
        self._repository = repository

    async def execute(self, project_id: UUID) -> list[MediaAsset]:
        return ordered(await self._repository.list_for_project(project_id))
