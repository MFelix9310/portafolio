"""Alta y modificacion de un recurso de contenido.

Recibe una entidad de dominio ya construida y validada por sus invariantes. Ninguna
ruta puede escribir en la base sin pasar por aqui.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from ....domain.repositories.base import ContentRepository

TEntity = TypeVar("TEntity")


class SaveContent(Generic[TEntity]):
    def __init__(self, repository: ContentRepository[TEntity]) -> None:
        self._repository = repository

    async def execute(self, entity: TEntity) -> TEntity:
        return await self._repository.save(entity)
