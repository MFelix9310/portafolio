"""Borrado de un recurso de contenido."""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from ....domain.repositories.base import ContentRepository
from ...errors import NotFoundError

TEntity = TypeVar("TEntity")


class DeleteContent(Generic[TEntity]):
    def __init__(self, repository: ContentRepository[TEntity], resource: str) -> None:
        self._repository = repository
        self._resource = resource

    async def execute(self, entity_id: UUID) -> None:
        if not await self._repository.delete(entity_id):
            raise NotFoundError(self._resource, entity_id)
