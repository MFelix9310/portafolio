"""Lectura del perfil singleton."""

from __future__ import annotations

from typing import Literal, overload

from ....domain.entities.profile import Profile
from ....domain.repositories.profile_repository import ProfileRepository
from ...errors import NotFoundError


class GetProfile:
    def __init__(self, repository: ProfileRepository) -> None:
        self._repository = repository

    @overload
    async def execute(self, *, required: Literal[True] = ...) -> Profile: ...

    @overload
    async def execute(self, *, required: Literal[False]) -> Profile | None: ...

    async def execute(self, *, required: bool = True) -> Profile | None:
        """`required=False` lo usa el catalogo: un perfil ausente no rompe la pagina."""
        profile = await self._repository.get()
        if profile is None and required:
            raise NotFoundError("profile", "singleton")
        return profile
