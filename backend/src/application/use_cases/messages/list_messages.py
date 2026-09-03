"""Bandeja de mensajes. Solo accesible desde /admin (RLS regla 3)."""

from __future__ import annotations

from ....domain.entities.message import Message
from ....domain.repositories.message_repository import MessageRepository


class ListMessages:
    def __init__(self, repository: MessageRepository) -> None:
        self._repository = repository

    async def execute(self, *, unread_only: bool = False) -> list[Message]:
        return await self._repository.list(unread_only=unread_only)
