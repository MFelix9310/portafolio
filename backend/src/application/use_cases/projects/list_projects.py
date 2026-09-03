"""Listado de proyectos: unica entrada al catalogo.

`/projects`, `/catalog`, `/data`, `/developer` y `/civil-bim` acaban todos aqui. El
filtrado por area+subarea lo resuelve `domain.services.catalog`, no este caso de uso
ni el adaptador de persistencia (D4).
"""

from __future__ import annotations

from ....domain.entities.project import Project
from ....domain.repositories.filters import ProjectFilter
from ....domain.repositories.project_repository import ProjectRepository
from ....domain.services.catalog import filter_by_taxonomy, ordered, visible


class ListProjects:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, filter: ProjectFilter | None = None) -> list[Project]:
        criteria = filter or ProjectFilter.public()
        rows = await self._repository.list(criteria)
        rows = visible(rows, include_drafts=criteria.include_drafts)
        rows = filter_by_taxonomy(rows, area=criteria.area, subarea=criteria.subarea)
        return ordered(rows)
