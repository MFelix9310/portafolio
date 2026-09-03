"""Reordenacion en bloque de proyectos."""

from __future__ import annotations

from ....domain.entities.project import Project
from ....domain.repositories.project_repository import ProjectRepository
from ...dto.commands import ReorderCommand


class ReorderProjects:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, command: ReorderCommand) -> list[Project]:
        return await self._repository.reorder(command.ordered_ids)
