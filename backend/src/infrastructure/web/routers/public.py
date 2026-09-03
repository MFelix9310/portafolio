"""Rutas publicas. Sin auth y sin borradores, nunca."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Query

from ....application.dto.commands import NewMessageCommand
from ....domain.repositories.filters import ContentFilter, ProjectFilter
from ....domain.value_objects.slug import Slug
from ....domain.value_objects.taxonomy_keys import AreaKey, SubareaKey
from ...config.container import Container
from ..dependencies import ContainerDep
from ..schemas import presenters
from ..schemas.requests import MessageIn

LocaleQuery = Annotated[str | None, Query(description="es | en. Sin valor, mapa completo")]
AreaQuery = Annotated[str | None, Query(description="clave de area")]
SubareaQuery = Annotated[str | None, Query(description="clave de subarea, dentro del area")]


def _project_filter(area: str | None, subarea: str | None) -> ProjectFilter:
    return ProjectFilter.public(
        AreaKey(area) if area else None,
        SubareaKey(subarea) if subarea else None,
    )


def create_public_router(container: Container) -> APIRouter:
    router = APIRouter(tags=["public"])

    @router.get("/catalog", summary="Catalogo completo, filtrado")
    async def get_catalog(
        c: ContainerDep,
        area: AreaQuery = None,
        subarea: SubareaQuery = None,
        locale: LocaleQuery = None,
    ) -> dict[str, Any]:
        view = await c.get_catalog.execute(
            area=AreaKey(area) if area else None,
            subarea=SubareaKey(subarea) if subarea else None,
            locale=locale,
        )
        return presenters.catalog(view, c.settings.media_public_base_url)

    @router.get("/projects", summary="Proyectos publicados")
    async def list_projects(
        c: ContainerDep,
        area: AreaQuery = None,
        subarea: SubareaQuery = None,
        locale: LocaleQuery = None,
    ) -> list[dict[str, Any]]:
        items = await c.list_projects.execute(_project_filter(area, subarea))
        base = c.settings.media_public_base_url
        return [presenters.project(item, locale, base) for item in items]

    @router.get("/projects/{slug}", summary="Detalle de proyecto")
    async def get_project(
        c: ContainerDep, slug: str, locale: LocaleQuery = None
    ) -> dict[str, Any]:
        project = await c.get_project.execute(Slug(slug))
        return presenters.project(project, locale, c.settings.media_public_base_url)

    @router.get("/areas", summary="Areas, subareas y conteos")
    async def list_areas(c: ContainerDep, locale: LocaleQuery = None) -> list[dict[str, Any]]:
        areas = await c.list_areas.execute()
        return [presenters.area_overview(item, locale) for item in areas]

    @router.get("/experiences")
    async def list_experiences(
        c: ContainerDep, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        items = await c.resources["experiences"].list.execute(ContentFilter.public())
        base = c.settings.media_public_base_url
        return [presenters.experience(item, locale, base) for item in items]

    @router.get("/certifications")
    async def list_certifications(
        c: ContainerDep, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        items = await c.resources["certifications"].list.execute(ContentFilter.public())
        base = c.settings.media_public_base_url
        return [presenters.certification(item, locale, base) for item in items]

    @router.get("/education")
    async def list_education(
        c: ContainerDep, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        items = await c.resources["education"].list.execute(ContentFilter.public())
        return [presenters.education(item, locale) for item in items]

    @router.get("/publications")
    async def list_publications(
        c: ContainerDep, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        items = await c.resources["publications"].list.execute(ContentFilter.public())
        base = c.settings.media_public_base_url
        return [presenters.publication(item, locale, base) for item in items]

    @router.get("/contacts")
    async def list_contacts(
        c: ContainerDep, locale: LocaleQuery = None
    ) -> list[dict[str, Any]]:
        items = await c.resources["contacts"].list.execute(ContentFilter.public())
        return [presenters.contact(item, locale) for item in items]

    @router.get("/profile")
    async def get_profile(c: ContainerDep, locale: LocaleQuery = None) -> dict[str, Any]:
        profile = await c.get_profile.execute()
        return presenters.profile(profile, locale, c.settings.media_public_base_url)

    @router.post("/messages", status_code=201, summary="Formulario de contacto")
    async def create_message(c: ContainerDep, payload: MessageIn) -> dict[str, Any]:
        message = await c.create_message.execute(
            NewMessageCommand(
                name=payload.name,
                email=payload.email,
                body=payload.body,
                subject=payload.subject,
            )
        )
        # No se devuelve el cuerpo: el formulario publico no debe poder releerse.
        return {"id": str(message.id), "created_at": message.created_at.isoformat()}

    return router
