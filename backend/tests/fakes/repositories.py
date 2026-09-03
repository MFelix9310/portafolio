"""Repositorios en memoria. Fakes reales, no mocks: se comportan como la base.

Sirven para que los tests de dominio y de casos de uso corran sin Supabase levantado.
"""

from __future__ import annotations

import copy
from typing import Generic, Sequence, TypeVar
from uuid import UUID, uuid4

from src.domain.entities.media import MediaAsset
from src.domain.entities.message import Message
from src.domain.entities.profile import Profile
from src.domain.entities.project import Project
from src.domain.entities.taxonomy import Area, Subarea
from src.domain.repositories.base import ContentRepository
from src.domain.repositories.filters import ContentFilter, ProjectFilter
from src.domain.repositories.media_repository import MediaRepository
from src.domain.repositories.message_repository import MessageRepository
from src.domain.repositories.profile_repository import ProfileRepository
from src.domain.repositories.project_repository import ProjectRepository
from src.domain.repositories.taxonomy_repository import TaxonomyRepository
from src.domain.services.catalog import apply_reorder, ordered, visible
from src.domain.value_objects.slug import Slug
from src.domain.value_objects.taxonomy_keys import AreaKey

TEntity = TypeVar("TEntity")


class _Store(Generic[TEntity]):
    """Almacen comun. Copia al entrar y al salir, como haria un round trip real."""

    def __init__(self, rows: Sequence[TEntity] = ()) -> None:
        self._rows: dict[UUID, TEntity] = {}
        for row in rows:
            self.put(row)

    def put(self, entity: TEntity) -> TEntity:
        stored = copy.deepcopy(entity)
        if getattr(stored, "id", None) is None:
            stored.id = uuid4()
        self._rows[stored.id] = stored
        return copy.deepcopy(stored)

    def all(self) -> list[TEntity]:
        return [copy.deepcopy(row) for row in self._rows.values()]

    def get(self, entity_id: UUID) -> TEntity | None:
        row = self._rows.get(entity_id)
        return copy.deepcopy(row) if row is not None else None

    def drop(self, entity_id: UUID) -> bool:
        return self._rows.pop(entity_id, None) is not None

    def replace_all(self, rows: Sequence[TEntity]) -> None:
        self._rows = {row.id: copy.deepcopy(row) for row in rows}


class InMemoryContentRepository(ContentRepository[TEntity]):
    def __init__(self, rows: Sequence[TEntity] = ()) -> None:
        self._store: _Store[TEntity] = _Store(rows)

    async def list(self, filter: ContentFilter) -> list[TEntity]:
        return ordered(visible(self._store.all(), include_drafts=filter.include_drafts))

    async def get(self, entity_id: UUID) -> TEntity | None:
        return self._store.get(entity_id)

    async def save(self, entity: TEntity) -> TEntity:
        return self._store.put(entity)

    async def delete(self, entity_id: UUID) -> bool:
        return self._store.drop(entity_id)

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[TEntity]:
        reordered = apply_reorder(self._store.all(), ordered_ids)
        self._store.replace_all(reordered)
        return [copy.deepcopy(row) for row in reordered]


class InMemoryProjectRepository(ProjectRepository):
    """El adaptador real solo empuja `status` a SQL; la taxonomia la filtra el dominio."""

    def __init__(self, rows: Sequence[Project] = ()) -> None:
        self._store: _Store[Project] = _Store(rows)

    async def get_by_slug(self, slug: Slug) -> Project | None:
        return next((p for p in self._store.all() if p.slug == slug), None)

    async def get(self, project_id: UUID) -> Project | None:
        return self._store.get(project_id)

    async def list(self, filter: ProjectFilter) -> list[Project]:
        return ordered(visible(self._store.all(), include_drafts=filter.include_drafts))

    async def save(self, project: Project) -> Project:
        return self._store.put(project)

    async def delete(self, project_id: UUID) -> bool:
        return self._store.drop(project_id)

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[Project]:
        reordered = apply_reorder(self._store.all(), ordered_ids)
        self._store.replace_all(reordered)
        return [copy.deepcopy(row) for row in reordered]


class InMemoryProfileRepository(ProfileRepository):
    def __init__(self, profile: Profile | None = None) -> None:
        self._profile = copy.deepcopy(profile)

    async def get(self) -> Profile | None:
        return copy.deepcopy(self._profile)

    async def save(self, profile: Profile) -> Profile:
        stored = copy.deepcopy(profile)
        if stored.id is None:
            stored.id = uuid4()
        self._profile = stored
        return copy.deepcopy(stored)


class InMemoryMessageRepository(MessageRepository):
    def __init__(self, rows: Sequence[Message] = ()) -> None:
        self._store: _Store[Message] = _Store(rows)

    async def save(self, message: Message) -> Message:
        return self._store.put(message)

    async def list(self, *, unread_only: bool = False) -> list[Message]:
        rows = self._store.all()
        if unread_only:
            rows = [row for row in rows if not row.read]
        return sorted(rows, key=lambda row: row.created_at, reverse=True)


class InMemoryTaxonomyRepository(TaxonomyRepository):
    def __init__(self, areas: Sequence[Area] = ()) -> None:
        self._areas: dict[UUID, Area] = {}
        self._subareas: dict[UUID, Subarea] = {}
        for area in areas:
            self._seed(area)

    def _seed(self, area: Area) -> None:
        stored = copy.deepcopy(area)
        if stored.id is None:
            stored.id = uuid4()
        subareas = []
        for sub in stored.subareas:
            if sub.id is None:
                sub.id = uuid4()
            sub.area_id = stored.id
            self._subareas[sub.id] = sub
            subareas.append(sub)
        stored.subareas = tuple(subareas)
        self._areas[stored.id] = stored

    async def list_areas(self) -> list[Area]:
        result = []
        for area in self._areas.values():
            clone = copy.deepcopy(area)
            clone.subareas = tuple(
                copy.deepcopy(sub)
                for sub in self._subareas.values()
                if sub.area_id == area.id
            )
            result.append(clone)
        return ordered(result)

    async def list_subareas(self, area: AreaKey | None = None) -> list[Subarea]:
        rows = [copy.deepcopy(sub) for sub in self._subareas.values()]
        if area is not None:
            rows = [sub for sub in rows if sub.area_key == area]
        return ordered(rows)

    async def save_area(self, area: Area) -> Area:
        stored = copy.deepcopy(area)
        if stored.id is None:
            stored.id = uuid4()
        self._areas[stored.id] = stored
        return copy.deepcopy(stored)

    async def save_subarea(self, subarea: Subarea) -> Subarea:
        stored = copy.deepcopy(subarea)
        if stored.id is None:
            stored.id = uuid4()
        if stored.area_id is None:
            parent = next(
                (a for a in self._areas.values() if a.key == stored.area_key), None
            )
            stored.area_id = parent.id if parent else None
        self._subareas[stored.id] = stored
        return copy.deepcopy(stored)

    async def delete(self, entity_id: UUID) -> bool:
        if self._areas.pop(entity_id, None) is not None:
            for sub_id in [
                sid for sid, s in self._subareas.items() if s.area_id == entity_id
            ]:
                self._subareas.pop(sub_id)
            return True
        return self._subareas.pop(entity_id, None) is not None


class InMemoryMediaRepository(MediaRepository):
    def __init__(self, rows: Sequence[MediaAsset] = ()) -> None:
        self._store: _Store[MediaAsset] = _Store(rows)

    async def list_for_project(self, project_id: UUID) -> list[MediaAsset]:
        return ordered([a for a in self._store.all() if a.project_id == project_id])

    async def get(self, media_id: UUID) -> MediaAsset | None:
        return self._store.get(media_id)

    async def save(self, asset: MediaAsset) -> MediaAsset:
        return self._store.put(asset)

    async def delete(self, media_id: UUID) -> bool:
        return self._store.drop(media_id)

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[MediaAsset]:
        reordered = apply_reorder(self._store.all(), ordered_ids)
        self._store.replace_all(reordered)
        return [copy.deepcopy(row) for row in reordered]
