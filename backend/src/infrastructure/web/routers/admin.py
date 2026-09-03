"""Rutas de /admin.

Regla dura del contrato: invocan exactamente los mismos casos de uso que las rutas
publicas. Lo unico que cambia es que aqui el filtro incluye borradores y que toda la
seccion depende de `require_admin`. No hay una sola ruta que hable con un repositorio.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from ....application.dto.commands import ReorderCommand, UploadUrlCommand
from ....domain.repositories.filters import ContentFilter, ProjectFilter
from ....domain.value_objects.taxonomy_keys import AreaKey
from ...config.container import Container
from ..dependencies import ContainerDep, require_admin
from ..schemas import presenters
from ..schemas.requests import BY_RESOURCE as REQUEST_MODELS
from ..schemas.requests import (
    TO_ROW_BY_RESOURCE,
    AreaPatchIn,
    MediaAssetIn,
    ProfileIn,
    ReorderIn,
    RevalidateIn,
    SubareaIn,
    UploadUrlIn,
    parse_resource,
)

LocaleQuery = Annotated[str | None, Query()]
Payload = Annotated[dict[str, Any], Body()]


def _resource_or_404(container: Container, resource: str):
    bundle = container.resources.get(resource)
    if bundle is None or resource not in REQUEST_MODELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"recurso desconocido: {resource}"
        )
    return bundle


def create_admin_router(container: Container) -> APIRouter:
    # La dependencia se declara a nivel de router: ninguna ruta puede olvidarla.
    router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

    # --- rutas especificas: se declaran antes que /{recurso} para que ganen ---

    @router.get("/profile")
    async def get_profile(c: ContainerDep, locale: LocaleQuery = None) -> dict[str, Any]:
        profile = await c.get_profile.execute(required=False)
        base = c.settings.media_public_base_url
        return presenters.profile(profile, locale, base) or {}

    @router.post("/profile")
    async def save_profile(c: ContainerDep, payload: ProfileIn) -> dict[str, Any]:
        profile = await c.save_profile.execute(payload.to_domain())
        return presenters.profile(profile, None, c.settings.media_public_base_url)

    @router.get("/areas")
    async def list_areas(c: ContainerDep, locale: LocaleQuery = None) -> list[dict[str, Any]]:
        areas = await c.list_areas.execute(include_drafts=True)
        return [presenters.area_overview(item, locale) for item in areas]

    # Las tres areas son rutas del App Router del front (/data, /developer,
    # /civil-bim). Crear una desde el panel daria un area sin pagina que la
    # renderice, y borrarla dejaria la ruta viva y sin datos. Se responde 405 con el
    # motivo en vez de omitir las rutas, para que el panel reciba una explicacion y
    # no un 404 ambiguo.
    AREAS_ARE_FIXED = (
        "las areas son fijas: /data, /developer y /civil-bim son rutas del frontend. "
        "Se pueden editar con PATCH /admin/areas/{id}, pero no crear ni borrar. "
        "Las subareas si admiten el ciclo completo en /admin/subareas."
    )

    @router.post("/areas", status_code=405, include_in_schema=False)
    async def create_area_not_allowed() -> None:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=AREAS_ARE_FIXED,
            headers={"Allow": "GET, PATCH"},
        )

    @router.delete("/areas/{entity_id}", status_code=405, include_in_schema=False)
    async def delete_area_not_allowed(entity_id: UUID) -> None:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=AREAS_ARE_FIXED,
            headers={"Allow": "GET, PATCH"},
        )

    @router.patch("/areas/{entity_id}")
    async def update_area(
        c: ContainerDep, entity_id: UUID, payload: AreaPatchIn
    ) -> dict[str, Any]:
        """Edita nombre, descripcion, orden y visibilidad. La clave no se toca."""
        area = await c.update_area.execute(payload.to_command(entity_id))
        return {
            "id": str(area.id),
            "key": area.key.value,
            "name": area.name.to_dict(),
            "blurb": area.blurb.to_dict() if area.blurb else None,
            "display_order": area.display_order,
            "status": area.status.value,
        }

    @router.get("/subareas")
    async def list_subareas(
        c: ContainerDep, area: str | None = None, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        items = await c.list_subareas.execute(AreaKey(area) if area else None)
        return [presenters.subarea(item, locale) for item in items]

    # 201 como el POST generico: mismo verbo y misma semantica, mismo codigo.
    @router.post("/subareas", status_code=201)
    async def save_subarea(c: ContainerDep, payload: SubareaIn) -> dict[str, Any]:
        subarea = await c.save_subarea.execute(payload.to_domain())
        return presenters.subarea(subarea, None)

    @router.delete("/subareas/{entity_id}", status_code=204)
    async def delete_subarea(c: ContainerDep, entity_id: UUID) -> None:
        await c.delete_subarea.execute(entity_id)

    @router.get("/messages")
    async def list_messages(c: ContainerDep, unread_only: bool = False) -> list[dict[str, Any]]:
        return [
            presenters.message(m) for m in await c.list_messages.execute(unread_only=unread_only)
        ]

    @router.post("/media/upload-url")
    async def create_upload_url(c: ContainerDep, payload: UploadUrlIn) -> dict[str, Any]:
        ticket = await c.create_upload_url.execute(
            UploadUrlCommand(filename=payload.filename, content_type=payload.content_type)
        )
        return presenters.upload_ticket(ticket)

    @router.get("/media")
    async def list_media(
        c: ContainerDep, project_id: UUID, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        assets = await c.list_project_media.execute(project_id)
        base = c.settings.media_public_base_url
        return [presenters.media_asset(asset, locale, base) for asset in assets]

    @router.post("/media")
    async def save_media(c: ContainerDep, payload: MediaAssetIn) -> dict[str, Any]:
        asset = await c.save_media.execute(payload.to_domain())
        return presenters.media_asset(asset, None, c.settings.media_public_base_url)

    @router.delete("/media/{media_id}", status_code=204)
    async def delete_media(c: ContainerDep, media_id: UUID) -> None:
        await c.delete_media.execute(media_id)

    @router.post("/media/reorder")
    async def reorder_media(c: ContainerDep, payload: ReorderIn) -> list[dict[str, Any]]:
        assets = await c.reorder_media.execute(ReorderCommand(tuple(payload.ids)))
        base = c.settings.media_public_base_url
        return [presenters.media_asset(asset, None, base) for asset in assets]

    @router.post("/revalidate")
    async def revalidate(c: ContainerDep, payload: RevalidateIn | None = None) -> dict[str, Any]:
        paths = tuple(payload.paths) if payload and payload.paths else None
        result = await c.revalidate_frontend.execute(paths)
        return {
            "accepted": result.accepted,
            "paths": list(result.requested_paths),
            "detail": result.detail,
        }

    # --- rutas genericas /admin/{recurso}, tal y como las nombra el contrato ---

    @router.get("/{recurso}")
    async def list_resource(
        c: ContainerDep, recurso: str, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        bundle = _resource_or_404(c, recurso)
        criteria = (
            ProjectFilter(status=None) if recurso == "projects" else ContentFilter.everything()
        )
        items = await bundle.list.execute(criteria)
        present = presenters.BY_RESOURCE[recurso]
        base = c.settings.media_public_base_url
        return [present(item, locale, base) for item in items]

    @router.post("/{recurso}", status_code=201)
    async def create_resource(c: ContainerDep, recurso: str, payload: Payload) -> dict[str, Any]:
        bundle = _resource_or_404(c, recurso)
        entity = parse_resource(recurso, payload)
        saved = await bundle.save.execute(entity)
        return presenters.BY_RESOURCE[recurso](saved, None, c.settings.media_public_base_url)

    @router.patch("/{recurso}/{entity_id}")
    async def update_resource(
        c: ContainerDep, recurso: str, entity_id: UUID, payload: Payload
    ) -> dict[str, Any]:
        bundle = _resource_or_404(c, recurso)
        # PATCH parcial: se parte de la fila canonica actual y se le superpone lo que
        # manda el panel, de modo que enviar un solo campo no borra el resto. Se usa la
        # fila canonica y no la de presentacion porque esta ultima anade `*_url`
        # derivadas que no son campos de entrada.
        current = await bundle.get.execute(entity_id)
        row = TO_ROW_BY_RESOURCE[recurso](current)
        merged = {**{k: v for k, v in row.items() if v is not None}, **payload}
        merged["id"] = str(entity_id)
        entity = parse_resource(recurso, merged)
        saved = await bundle.save.execute(entity)
        return presenters.BY_RESOURCE[recurso](saved, None, c.settings.media_public_base_url)

    @router.delete("/{recurso}/{entity_id}", status_code=204)
    async def delete_resource(c: ContainerDep, recurso: str, entity_id: UUID) -> None:
        bundle = _resource_or_404(c, recurso)
        await bundle.delete.execute(entity_id)

    @router.post("/{recurso}/reorder")
    async def reorder_resource(
        c: ContainerDep, recurso: str, payload: ReorderIn
    ) -> list[dict[str, Any]]:
        bundle = _resource_or_404(c, recurso)
        items = await bundle.reorder.execute(ReorderCommand(tuple(payload.ids)))
        present = presenters.BY_RESOURCE[recurso]
        base = c.settings.media_public_base_url
        return [present(item, None, base) for item in items]

    return router


__all__ = ["create_admin_router"]
