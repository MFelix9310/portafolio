"""Implementaciones de los puertos sobre el almacen JSON."""

from __future__ import annotations

from typing import Any, Callable, Generic, Sequence, TypeVar
from uuid import UUID, uuid4

from ....domain.entities.media import MediaAsset
from ....domain.entities.message import Message
from ....domain.entities.profile import Profile
from ....domain.entities.project import Project
from ....domain.entities.taxonomy import Area, Subarea
from ....domain.repositories.base import ContentRepository
from ....domain.repositories.filters import ContentFilter, ProjectFilter
from ....domain.repositories.media_repository import MediaRepository
from ....domain.repositories.message_repository import MessageRepository
from ....domain.repositories.profile_repository import ProfileRepository
from ....domain.repositories.project_repository import ProjectRepository
from ....domain.repositories.taxonomy_repository import TaxonomyRepository
from ....domain.services.catalog import apply_reorder, ordered, visible
from ....domain.value_objects.slug import Slug
from ....domain.value_objects.taxonomy_keys import AreaKey
from .. import serialization as ser
from .store import JsonCatalogStore

TEntity = TypeVar("TEntity")


class JsonContentRepository(ContentRepository[TEntity], Generic[TEntity]):
    """Un unico cuerpo para los cinco recursos de firma identica."""

    def __init__(
        self,
        store: JsonCatalogStore,
        collection: str,
        to_entity: Callable[[dict[str, Any]], TEntity],
        to_row: Callable[[TEntity], dict[str, Any]],
    ) -> None:
        self._store = store
        self._collection = collection
        self._to_entity = to_entity
        self._to_row = to_row

    def _all(self) -> list[TEntity]:
        return [self._to_entity(row) for row in self._store.collection(self._collection)]

    async def list(self, filter: ContentFilter) -> list[TEntity]:
        return ordered(visible(self._all(), include_drafts=filter.include_drafts))

    async def get(self, entity_id: UUID) -> TEntity | None:
        return next((e for e in self._all() if getattr(e, "id", None) == entity_id), None)

    async def save(self, entity: TEntity) -> TEntity:
        return self._to_entity(self._store.upsert(self._collection, self._to_row(entity)))

    async def delete(self, entity_id: UUID) -> bool:
        return self._store.remove(self._collection, entity_id)

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[TEntity]:
        reordered = apply_reorder(self._all(), ordered_ids)
        self._store.replace_collection(
            self._collection, [self._to_row(item) for item in reordered]
        )
        return reordered


class JsonProjectRepository(ProjectRepository):
    def __init__(self, store: JsonCatalogStore) -> None:
        self._store = store

    def _all(self) -> list[Project]:
        return [ser.project_from_row(row) for row in self._store.collection("projects")]

    async def get_by_slug(self, slug: Slug) -> Project | None:
        return next((p for p in self._all() if p.slug == slug), None)

    async def get(self, project_id: UUID) -> Project | None:
        return next((p for p in self._all() if p.id == project_id), None)

    async def list(self, filter: ProjectFilter) -> list[Project]:
        # Solo se resuelve el estado. La taxonomia la filtra domain.services.catalog.
        return ordered(visible(self._all(), include_drafts=filter.include_drafts))

    async def save(self, project: Project) -> Project:
        return ser.project_from_row(self._store.upsert("projects", ser.project_to_row(project)))

    async def delete(self, project_id: UUID) -> bool:
        return self._store.remove("projects", project_id)

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[Project]:
        reordered = apply_reorder(self._all(), ordered_ids)
        self._store.replace_collection(
            "projects", [ser.project_to_row(p) for p in reordered]
        )
        return reordered


class JsonProfileRepository(ProfileRepository):
    def __init__(self, store: JsonCatalogStore) -> None:
        self._store = store

    async def get(self) -> Profile | None:
        row = self._store.singleton("profile")
        return ser.profile_from_row(row) if row else None

    async def save(self, profile: Profile) -> Profile:
        return ser.profile_from_row(
            self._store.set_singleton("profile", ser.profile_to_row(profile))
        )


class JsonMessageRepository(MessageRepository):
    def __init__(self, store: JsonCatalogStore) -> None:
        self._store = store

    async def save(self, message: Message) -> Message:
        return ser.message_from_row(
            self._store.upsert("messages", ser.message_to_row(message))
        )

    async def list(self, *, unread_only: bool = False) -> list[Message]:
        rows = [ser.message_from_row(row) for row in self._store.collection("messages")]
        if unread_only:
            rows = [row for row in rows if not row.read]
        return sorted(rows, key=lambda row: row.created_at, reverse=True)


class JsonTaxonomyRepository(TaxonomyRepository):
    def __init__(self, store: JsonCatalogStore) -> None:
        self._store = store

    def _subareas(self) -> list[Subarea]:
        return [
            ser.subarea_from_row(row, row["area_key"])
            for row in self._store.collection("subareas")
        ]

    async def list_areas(self) -> list[Area]:
        subareas = self._subareas()
        areas = [
            ser.area_from_row(
                row,
                tuple(ordered([s for s in subareas if s.area_id == UUID(row["id"])])),
            )
            for row in self._store.collection("areas")
        ]
        return ordered(areas)

    async def list_subareas(self, area: AreaKey | None = None) -> list[Subarea]:
        rows = self._subareas()
        if area is not None:
            rows = [s for s in rows if s.area_key == area]
        return ordered(rows)

    async def save_area(self, area: Area) -> Area:
        row = self._store.upsert("areas", ser.area_to_row(area))
        return ser.area_from_row(row, area.subareas)

    async def save_subarea(self, subarea: Subarea) -> Subarea:
        if subarea.area_id is None:
            parent = next(
                (
                    row
                    for row in self._store.collection("areas")
                    if row["key"] == subarea.area_key.value
                ),
                None,
            )
            if parent is not None:
                subarea.area_id = UUID(parent["id"])
        row = self._store.upsert("subareas", ser.subarea_to_row(subarea))
        return ser.subarea_from_row(row, row["area_key"])

    async def delete(self, entity_id: UUID) -> bool:
        if self._store.remove("areas", entity_id):
            survivors = [
                row
                for row in self._store.collection("subareas")
                if row.get("area_id") != str(entity_id)
            ]
            self._store.replace_collection("subareas", survivors)
            return True
        return self._store.remove("subareas", entity_id)


class JsonMediaRepository(MediaRepository):
    """La media vive embebida en cada proyecto, igual que la trae el seed."""

    def __init__(self, store: JsonCatalogStore) -> None:
        self._store = store

    def _all(self) -> list[MediaAsset]:
        assets: list[MediaAsset] = []
        for project in self._store.collection("projects"):
            assets.extend(ser.media_from_row(row) for row in project.get("media", []))
        return assets

    async def list_for_project(self, project_id: UUID) -> list[MediaAsset]:
        return ordered([a for a in self._all() if a.project_id == project_id])

    async def get(self, media_id: UUID) -> MediaAsset | None:
        return next((a for a in self._all() if a.id == media_id), None)

    async def save(self, asset: MediaAsset) -> MediaAsset:
        projects = self._store.collection("projects")
        for project in projects:
            if project["id"] != str(asset.project_id):
                continue
            row = ser.media_to_row(asset)
            if not row["id"]:
                row["id"] = str(uuid4())
            media = [m for m in project.get("media", []) if m["id"] != row["id"]]
            media.append(row)
            project["media"] = media
            self._store.replace_collection("projects", projects)
            return ser.media_from_row(row)
        raise ValueError(f"proyecto inexistente: {asset.project_id}")

    async def delete(self, media_id: UUID) -> bool:
        projects = self._store.collection("projects")
        target = str(media_id)
        for project in projects:
            media = project.get("media", [])
            remaining = [m for m in media if m["id"] != target]
            if len(remaining) != len(media):
                project["media"] = remaining
                self._store.replace_collection("projects", projects)
                return True
        return False

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[MediaAsset]:
        reordered = apply_reorder(self._all(), ordered_ids)
        by_id = {str(asset.id): ser.media_to_row(asset) for asset in reordered}
        projects = self._store.collection("projects")
        for project in projects:
            project["media"] = [
                by_id.get(item["id"], item) for item in project.get("media", [])
            ]
        self._store.replace_collection("projects", projects)
        return reordered
