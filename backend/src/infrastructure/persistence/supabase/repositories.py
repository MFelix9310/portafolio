"""Implementaciones de los puertos sobre Postgres via PostgREST.

Ojo con el reparto de responsabilidades: aqui solo se empuja a SQL lo que la base
hace mejor (estado y orden). El filtrado por area+subarea lo resuelve
`domain.services.catalog` para que exista una unica implementacion del predicado.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Sequence, TypeVar
from uuid import UUID

from supabase import AsyncClient

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
from ....domain.services.catalog import apply_reorder, ordered
from ....domain.value_objects.slug import Slug
from ....domain.value_objects.taxonomy_keys import AreaKey
from .. import serialization as ser
from .client import first_row, rows_of

TEntity = TypeVar("TEntity")

PROJECT_SELECT = (
    "*, project_subareas(subareas(key, areas(key))), "
    "project_media(*)"
)


def _strip_nulls(row: dict[str, Any]) -> dict[str, Any]:
    """Un `id` None en el payload hace que Postgres no aplique su default."""
    return {key: value for key, value in row.items() if not (key == "id" and value is None)}


class SupabaseContentRepository(ContentRepository[TEntity], Generic[TEntity]):
    def __init__(
        self,
        client: AsyncClient,
        table: str,
        to_entity: Callable[[dict[str, Any]], TEntity],
        to_row: Callable[[TEntity], dict[str, Any]],
    ) -> None:
        self._client = client
        self._table = table
        self._to_entity = to_entity
        self._to_row = to_row

    async def list(self, filter: ContentFilter) -> list[TEntity]:
        query = self._client.table(self._table).select("*").order("display_order")
        if filter.status is not None:
            query = query.eq("status", filter.status.value)
        return [self._to_entity(row) for row in rows_of(await query.execute())]

    async def get(self, entity_id: UUID) -> TEntity | None:
        response = await (
            self._client.table(self._table).select("*").eq("id", str(entity_id)).execute()
        )
        row = first_row(response)
        return self._to_entity(row) if row else None

    async def save(self, entity: TEntity) -> TEntity:
        payload = _strip_nulls(self._to_row(entity))
        response = await self._client.table(self._table).upsert(payload).execute()
        row = first_row(response)
        return self._to_entity(row) if row else entity

    async def delete(self, entity_id: UUID) -> bool:
        response = await (
            self._client.table(self._table).delete().eq("id", str(entity_id)).execute()
        )
        return bool(rows_of(response))

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[TEntity]:
        current = await self.list(ContentFilter.everything())
        reordered = apply_reorder(current, ordered_ids)
        payload = [_strip_nulls(self._to_row(item)) for item in reordered]
        await self._client.table(self._table).upsert(payload).execute()
        return reordered


class SupabaseProjectRepository(ProjectRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> Project:
        """Aplana el select anidado de PostgREST a la forma canonica de fila."""
        taxonomy = []
        for link in row.get("project_subareas") or []:
            subarea = link.get("subareas") or {}
            area = subarea.get("areas") or {}
            if subarea.get("key") and area.get("key"):
                taxonomy.append({"area": area["key"], "subarea": subarea["key"]})
        flat = {k: v for k, v in row.items() if k not in ("project_subareas", "project_media")}
        flat["taxonomy"] = taxonomy
        flat["media"] = row.get("project_media") or []
        return ser.project_from_row(flat)

    async def get_by_slug(self, slug: Slug) -> Project | None:
        response = await (
            self._client.table("projects")
            .select(PROJECT_SELECT)
            .eq("slug", slug.value)
            .execute()
        )
        row = first_row(response)
        return self._to_entity(row) if row else None

    async def get(self, project_id: UUID) -> Project | None:
        response = await (
            self._client.table("projects")
            .select(PROJECT_SELECT)
            .eq("id", str(project_id))
            .execute()
        )
        row = first_row(response)
        return self._to_entity(row) if row else None

    async def list(self, filter: ProjectFilter) -> list[Project]:
        query = (
            self._client.table("projects").select(PROJECT_SELECT).order("display_order")
        )
        if filter.status is not None:
            query = query.eq("status", filter.status.value)
        return [self._to_entity(row) for row in rows_of(await query.execute())]

    async def save(self, project: Project) -> Project:
        payload = _strip_nulls(ser.project_to_row(project, embed=False))
        response = await self._client.table("projects").upsert(payload).execute()
        row = first_row(response) or payload
        project_id = UUID(row["id"])
        await self._sync_taxonomy(project_id, project)
        stored = await self.get(project_id)
        return stored or project

    async def _sync_taxonomy(self, project_id: UUID, project: Project) -> None:
        """project_subareas se reescribe entero: el panel manda el conjunto completo."""
        await (
            self._client.table("project_subareas")
            .delete()
            .eq("project_id", str(project_id))
            .execute()
        )
        if not project.taxonomy:
            return
        subareas = rows_of(
            await self._client.table("subareas").select("id, key, areas(key)").execute()
        )
        index = {
            ((row.get("areas") or {}).get("key"), row["key"]): row["id"] for row in subareas
        }
        links = [
            {"project_id": str(project_id), "subarea_id": index[key]}
            for tag in project.taxonomy
            if (key := (tag.area.value, tag.subarea.value)) in index
        ]
        if links:
            await self._client.table("project_subareas").insert(links).execute()

    async def delete(self, project_id: UUID) -> bool:
        response = await (
            self._client.table("projects").delete().eq("id", str(project_id)).execute()
        )
        return bool(rows_of(response))

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[Project]:
        current = await self.list(ProjectFilter(status=None))
        reordered = apply_reorder(current, ordered_ids)
        payload = [
            {"id": str(item.id), "display_order": item.display_order} for item in reordered
        ]
        await self._client.table("projects").upsert(payload).execute()
        return reordered


class SupabaseProfileRepository(ProfileRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def get(self) -> Profile | None:
        response = await self._client.table("profile").select("*").limit(1).execute()
        row = first_row(response)
        return ser.profile_from_row(row) if row else None

    async def save(self, profile: Profile) -> Profile:
        payload = _strip_nulls(ser.profile_to_row(profile))
        # A6: `singleton` es la clave unica que fuerza que solo haya una fila.
        response = await (
            self._client.table("profile")
            .upsert(payload, on_conflict="singleton")
            .execute()
        )
        row = first_row(response)
        return ser.profile_from_row(row) if row else profile


class SupabaseMessageRepository(MessageRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def save(self, message: Message) -> Message:
        payload = _strip_nulls(ser.message_to_row(message))
        response = await self._client.table("messages").insert(payload).execute()
        row = first_row(response)
        return ser.message_from_row(row) if row else message

    async def list(self, *, unread_only: bool = False) -> list[Message]:
        query = (
            self._client.table("messages").select("*").order("created_at", desc=True)
        )
        if unread_only:
            query = query.eq("read", False)
        return [ser.message_from_row(row) for row in rows_of(await query.execute())]


class SupabaseTaxonomyRepository(TaxonomyRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def list_areas(self) -> list[Area]:
        response = await (
            self._client.table("areas").select("*, subareas(*)").order("display_order").execute()
        )
        areas = []
        for row in rows_of(response):
            subareas = tuple(
                ordered(
                    [ser.subarea_from_row(sub, row["key"]) for sub in row.get("subareas") or []]
                )
            )
            flat = {k: v for k, v in row.items() if k != "subareas"}
            areas.append(ser.area_from_row(flat, subareas))
        return ordered(areas)

    async def list_subareas(self, area: AreaKey | None = None) -> list[Subarea]:
        response = await (
            self._client.table("subareas")
            .select("*, areas(key)")
            .order("display_order")
            .execute()
        )
        rows = []
        for row in rows_of(response):
            area_key = (row.get("areas") or {}).get("key")
            if area is not None and area_key != area.value:
                continue
            rows.append(ser.subarea_from_row(row, area_key))
        return ordered(rows)

    async def save_area(self, area: Area) -> Area:
        payload = _strip_nulls(ser.area_to_row(area))
        response = await self._client.table("areas").upsert(payload).execute()
        row = first_row(response) or payload
        return ser.area_from_row(row, area.subareas)

    async def save_subarea(self, subarea: Subarea) -> Subarea:
        payload = _strip_nulls(ser.subarea_to_row(subarea))
        area_key = payload.pop("area_key")
        if not payload.get("area_id"):
            parent = first_row(
                await self._client.table("areas").select("id").eq("key", area_key).execute()
            )
            if parent is None:
                raise ValueError(f"area inexistente: {area_key}")
            payload["area_id"] = parent["id"]
        response = await self._client.table("subareas").upsert(payload).execute()
        row = first_row(response) or payload
        return ser.subarea_from_row(row, area_key)

    async def delete(self, entity_id: UUID) -> bool:
        for table in ("areas", "subareas"):
            response = await (
                self._client.table(table).delete().eq("id", str(entity_id)).execute()
            )
            if rows_of(response):
                return True
        return False


class SupabaseMediaRepository(MediaRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def list_for_project(self, project_id: UUID) -> list[MediaAsset]:
        response = await (
            self._client.table("project_media")
            .select("*")
            .eq("project_id", str(project_id))
            .order("display_order")
            .execute()
        )
        return [ser.media_from_row(row) for row in rows_of(response)]

    async def get(self, media_id: UUID) -> MediaAsset | None:
        response = await (
            self._client.table("project_media").select("*").eq("id", str(media_id)).execute()
        )
        row = first_row(response)
        return ser.media_from_row(row) if row else None

    async def save(self, asset: MediaAsset) -> MediaAsset:
        payload = _strip_nulls(ser.media_to_row(asset))
        response = await self._client.table("project_media").upsert(payload).execute()
        row = first_row(response)
        return ser.media_from_row(row) if row else asset

    async def delete(self, media_id: UUID) -> bool:
        response = await (
            self._client.table("project_media").delete().eq("id", str(media_id)).execute()
        )
        return bool(rows_of(response))

    async def reorder(self, ordered_ids: Sequence[UUID]) -> list[MediaAsset]:
        response = await self._client.table("project_media").select("*").execute()
        current = [ser.media_from_row(row) for row in rows_of(response)]
        reordered = apply_reorder(current, ordered_ids)
        payload = [
            {"id": str(item.id), "display_order": item.display_order} for item in reordered
        ]
        await self._client.table("project_media").upsert(payload).execute()
        return reordered


__all__ = [
    "SupabaseContentRepository",
    "SupabaseMediaRepository",
    "SupabaseMessageRepository",
    "SupabaseProfileRepository",
    "SupabaseProjectRepository",
    "SupabaseTaxonomyRepository",
]
