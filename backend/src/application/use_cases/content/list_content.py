"""Listado generico de un recurso de contenido.

Los cinco recursos con la misma firma comparten este caso de uso; la diferencia esta
en el repositorio que se le inyecta. Publico y /admin invocan esta misma clase: lo
unico que cambia es el `ContentFilter` que reciben.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from ....domain.repositories.base import ContentRepository
from ....domain.repositories.filters import ContentFilter
from ....domain.services.catalog import ordered, visible

TEntity = TypeVar("TEntity")


class ListContent(Generic[TEntity]):
    def __init__(self, repository: ContentRepository[TEntity]) -> None:
        self._repository = repository

    async def execute(self, filter: ContentFilter | None = None) -> list[TEntity]:
        criteria = filter or ContentFilter.public()
        rows = await self._repository.list(criteria)
        # Segunda pasada barata: el adaptador puede no filtrar y el dominio manda.
        return ordered(visible(rows, include_drafts=criteria.include_drafts))
