"""Borrado de un proyecto."""

from __future__ import annotations

from uuid import UUID

from ....domain.repositories.project_repository import ProjectRepository
from ...errors import NotFoundError


class DeleteProject:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, project_id: UUID) -> None:
        if not await self._repository.delete(project_id):
            raise NotFoundError("project", project_id)
