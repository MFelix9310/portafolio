"""Escritura del perfil singleton."""

from __future__ import annotations

from ....domain.entities.profile import Profile
from ....domain.repositories.profile_repository import ProfileRepository


class SaveProfile:
    def __init__(self, repository: ProfileRepository) -> None:
        self._repository = repository

    async def execute(self, profile: Profile) -> Profile:
        return await self._repository.save(profile)
