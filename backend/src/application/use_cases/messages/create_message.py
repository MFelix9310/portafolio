"""Alta de un mensaje del formulario publico de contacto."""

from __future__ import annotations

from ....domain.entities.message import Message
from ....domain.repositories.message_repository import MessageRepository
from ...dto.commands import NewMessageCommand
from ...errors import ValidationError
from ...ports.clock import ClockPort


class CreateMessage:
    def __init__(self, repository: MessageRepository, clock: ClockPort) -> None:
        self._repository = repository
        self._clock = clock

    async def execute(self, command: NewMessageCommand) -> Message:
        try:
            message = Message(
                name=command.name,
                email=command.email,
                body=command.body,
                subject=command.subject,
                created_at=self._clock.now(),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._repository.save(message)
