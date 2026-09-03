"""Puerto de mensajes del formulario de contacto."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..entities.message import Message


class MessageRepository(ABC):
    @abstractmethod
    async def save(self, message: Message) -> Message: ...

    @abstractmethod
    async def list(self, *, unread_only: bool = False) -> list[Message]:
        """Solo el admin lee mensajes; se devuelven del mas reciente al mas antiguo."""
