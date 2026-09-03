"""Reordenacion en bloque desde el panel."""

from __future__ import annotations

from typing import Generic, TypeVar

from ....domain.repositories.base import ContentRepository
from ...dto.commands import ReorderCommand

TEntity = TypeVar("TEntity")


class ReorderContent(Generic[TEntity]):
    def __init__(self, repository: ContentRepository[TEntity]) -> None:
        self._repository = repository

    async def execute(self, command: ReorderCommand) -> list[TEntity]:
        return await self._repository.reorder(command.ordered_ids)
