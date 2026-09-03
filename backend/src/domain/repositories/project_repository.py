"""Puerto de persistencia de proyectos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from ..entities.project import Project
from ..value_objects.slug import Slug
from .filters import ProjectFilter


class ProjectRepository(ABC):
    @abstractmethod
    async def get_by_slug(self, slug: Slug) -> Project | None:
        """Detalle publico. Devuelve el proyecto con su media y su taxonomia."""

    @abstractmethod
    async def get(self, project_id: UUID) -> Project | None: ...

    @abstractmethod
    async def list(self, filter: ProjectFilter) -> list[Project]:
        """Catalogo filtrado. El filtrado por taxonomia usa domain.services.catalog."""

    @abstractmethod
    async def save(self, project: Project) -> Project: ...

    @abstractmethod
    async def delete(self, project_id: UUID) -> bool: ...

    @abstractmethod
    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[Project]: ...
