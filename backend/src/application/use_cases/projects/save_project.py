"""Alta y modificacion de un proyecto."""

from __future__ import annotations

from ....domain.entities.project import Project
from ....domain.repositories.project_repository import ProjectRepository
from ...errors import ConflictError


class SaveProject:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, project: Project) -> Project:
        existing = await self._repository.get_by_slug(project.slug)
        if existing is not None and existing.id != project.id:
            raise ConflictError("proyecto", "slug", project.slug.value)
        return await self._repository.save(project)
