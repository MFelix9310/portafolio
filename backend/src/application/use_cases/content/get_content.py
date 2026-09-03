"""Lectura de un recurso de contenido por id."""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from ....domain.repositories.base import ContentRepository
from ...errors import NotFoundError

TEntity = TypeVar("TEntity")


class GetContent(Generic[TEntity]):
    def __init__(self, repository: ContentRepository[TEntity], resource: str) -> None:
        self._repository = repository
        self._resource = resource

    async def execute(self, entity_id: UUID) -> TEntity:
        entity = await self._repository.get(entity_id)
        if entity is None:
            raise NotFoundError(self._resource, entity_id)
        return entity
