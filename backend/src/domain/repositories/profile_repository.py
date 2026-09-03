"""Puerto del perfil singleton."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..entities.profile import Profile


class ProfileRepository(ABC):
    @abstractmethod
    async def get(self) -> Profile | None:
        """None cuando la base aun no tiene la fila unica."""

    @abstractmethod
    async def save(self, profile: Profile) -> Profile: ...
