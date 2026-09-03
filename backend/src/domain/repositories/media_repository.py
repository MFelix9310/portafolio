"""Puerto de project_media.

El contrato lista `media` entre los recursos de /admin pero no declara su puerto en
la seccion "Puertos del dominio". Se anade aqui para que el CRUD de media no escriba
a la base saltandose el dominio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from ..entities.media import MediaAsset


class MediaRepository(ABC):
    @abstractmethod
    async def list_for_project(self, project_id: UUID) -> list[MediaAsset]: ...

    @abstractmethod
    async def get(self, media_id: UUID) -> MediaAsset | None: ...

    @abstractmethod
    async def save(self, asset: MediaAsset) -> MediaAsset: ...

    @abstractmethod
    async def delete(self, media_id: UUID) -> bool: ...

    @abstractmethod
    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[MediaAsset]: ...
