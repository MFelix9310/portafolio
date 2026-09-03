"""Alta y modificacion de un canal de contacto.

Existe en vez de reutilizar el `SaveContent` generico por una sola razon: el
addendum A5 declara `contacts unique (kind, value)`. Dejar esa unicidad solo en el
esquema hacia que el adaptador JSON aceptara el duplicado y el de Supabase reventara
con un error de Postgres. La regla vive aqui, asi que los dos se comportan igual.
"""

from __future__ import annotations

from ....domain.entities.contact import Contact
from ....domain.repositories.base import ContentRepository
from ....domain.repositories.filters import ContentFilter
from ...errors import ConflictError


class SaveContact:
    def __init__(self, repository: ContentRepository[Contact]) -> None:
        self._repository = repository

    async def execute(self, contact: Contact) -> Contact:
        existing = await self._repository.list(ContentFilter.everything())
        clash = next(
            (
                other
                for other in existing
                if other.kind == contact.kind
                and other.value == contact.value
                and other.id != contact.id
            ),
            None,
        )
        if clash is not None:
            raise ConflictError("contacto", "(kind, value)", (contact.kind, contact.value))
        return await self._repository.save(contact)
