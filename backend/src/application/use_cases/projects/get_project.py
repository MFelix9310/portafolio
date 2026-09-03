"""Detalle de un proyecto por slug."""

from __future__ import annotations

from ....domain.entities.project import Project
from ....domain.repositories.project_repository import ProjectRepository
from ....domain.value_objects.slug import Slug
from ...errors import NotFoundError


class GetProject:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, slug: Slug, *, include_drafts: bool = False) -> Project:
        project = await self._repository.get_by_slug(slug)
        if project is None:
            raise NotFoundError("project", slug.value)
        # Un borrador existe pero no es publico: 404, no 403, para no filtrar su existencia.
        if not include_drafts and not project.status.is_public:
            raise NotFoundError("project", slug.value)
        return project
