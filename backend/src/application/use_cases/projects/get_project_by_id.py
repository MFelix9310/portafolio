"""Lectura de un proyecto por id.

El panel edita por id (`PATCH /admin/projects/{id}`) mientras que el sitio publico
lee por slug. Son dos accesos distintos al mismo repositorio, no el mismo caso de uso
con un parametro polimorfico.
"""

from __future__ import annotations

from uuid import UUID

from ....domain.entities.project import Project
from ....domain.repositories.project_repository import ProjectRepository
from ...errors import NotFoundError


class GetProjectById:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, project_id: UUID) -> Project:
        project = await self._repository.get(project_id)
        if project is None:
            raise NotFoundError("project", project_id)
        return project
