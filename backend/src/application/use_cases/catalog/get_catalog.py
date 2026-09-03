"""Catalogo completo en una sola respuesta.

Compone los casos de uso ya existentes en vez de hablar con los repositorios; asi el
filtrado y la visibilidad son exactamente los mismos que en los endpoints sueltos.
"""

from __future__ import annotations

from ....domain.entities.certification import Certification
from ....domain.entities.contact import Contact
from ....domain.entities.education import Education
from ....domain.entities.experience import Experience
from ....domain.entities.publication import Publication
from ....domain.repositories.filters import ContentFilter, ProjectFilter
from ....domain.value_objects.taxonomy_keys import AreaKey, SubareaKey
from ...dto.catalog import CatalogView
from ..content.list_content import ListContent
from ..profile.get_profile import GetProfile
from ..projects.list_projects import ListProjects
from .list_areas import ListAreas


class GetCatalog:
    def __init__(
        self,
        *,
        list_projects: ListProjects,
        list_areas: ListAreas,
        list_experiences: ListContent[Experience],
        list_certifications: ListContent[Certification],
        list_education: ListContent[Education],
        list_publications: ListContent[Publication],
        list_contacts: ListContent[Contact],
        get_profile: GetProfile,
    ) -> None:
        self._list_projects = list_projects
        self._list_areas = list_areas
        self._list_experiences = list_experiences
        self._list_certifications = list_certifications
        self._list_education = list_education
        self._list_publications = list_publications
        self._list_contacts = list_contacts
        self._get_profile = get_profile

    async def execute(
        self,
        *,
        area: AreaKey | None = None,
        subarea: SubareaKey | None = None,
        locale: str | None = None,
        include_drafts: bool = False,
    ) -> CatalogView:
        project_filter = (
            ProjectFilter(area=area, subarea=subarea, status=None)
            if include_drafts
            else ProjectFilter.public(area=area, subarea=subarea)
        )
        content_filter = (
            ContentFilter.everything() if include_drafts else ContentFilter.public()
        )

        return CatalogView(
            profile=await self._get_profile.execute(required=False),
            areas=await self._list_areas.execute(include_drafts=include_drafts),
            projects=tuple(await self._list_projects.execute(project_filter)),
            experiences=tuple(await self._list_experiences.execute(content_filter)),
            certifications=tuple(await self._list_certifications.execute(content_filter)),
            education=tuple(await self._list_education.execute(content_filter)),
            publications=tuple(await self._list_publications.execute(content_filter)),
            contacts=tuple(await self._list_contacts.execute(content_filter)),
            locale=locale,
        )
