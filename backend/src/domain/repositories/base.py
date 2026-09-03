"""Forma comun de los puertos de persistencia.

Los cinco recursos de contenido (experiencias, certificaciones, formacion,
publicaciones, contactos) comparten exactamente la misma firma. Se declara una vez
como ABC generica y cada puerto del contrato la especializa con su entidad.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Sequence, TypeVar
from uuid import UUID

from .filters import ContentFilter

TEntity = TypeVar("TEntity")


class ContentRepository(ABC, Generic[TEntity]):
    """Puerto de salida. La implementacion vive en infraestructura."""

    @abstractmethod
    async def list(self, filter: ContentFilter) -> list[TEntity]:
        """Devuelve las filas que cumplen el filtro, ya ordenadas por display_order."""

    @abstractmethod
    async def get(self, entity_id: UUID) -> TEntity | None:
        """Devuelve la entidad o None; no lanza si no existe."""

    @abstractmethod
    async def save(self, entity: TEntity) -> TEntity:
        """Inserta si `id` es None, actualiza si no. Devuelve la entidad persistida."""

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """True si borro algo, False si no existia."""

    @abstractmethod
    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[TEntity]:
        """Reasigna display_order en bloque y devuelve el conjunto reordenado."""
