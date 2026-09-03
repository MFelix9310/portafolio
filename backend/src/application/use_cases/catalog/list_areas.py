"""Areas con sus subareas y el numero de proyectos publicados en cada una.

`civil-bim` nace sin proyectos: el conteo cero es un resultado valido, no un hueco.
"""

from __future__ import annotations

from ....domain.repositories.filters import ProjectFilter
from ....domain.repositories.taxonomy_repository import TaxonomyRepository
from ....domain.services.catalog import (
    count_projects_by_area,
    count_projects_by_subarea,
    ordered,
)
from ...dto.catalog import AreaOverview, SubareaOverview
from ..projects.list_projects import ListProjects


class ListAreas:
    def __init__(
        self, repository: TaxonomyRepository, list_projects: ListProjects
    ) -> None:
        self._repository = repository
        self._list_projects = list_projects

    async def execute(self, *, include_drafts: bool = False) -> tuple[AreaOverview, ...]:
        criteria = ProjectFilter(status=None) if include_drafts else ProjectFilter.public()
        projects = await self._list_projects.execute(criteria)
        by_area = count_projects_by_area(projects)
        by_subarea = count_projects_by_subarea(projects)

        areas = await self._repository.list_areas()
        if not include_drafts:
            # Un area despublicada oculta su ruta del sitio publico.
            areas = [area for area in areas if area.status.is_public]

        overviews: list[AreaOverview] = []
        for area in ordered(areas):
            subareas = tuple(
                SubareaOverview(
                    key=sub.key.value,
                    name=sub.name.to_dict(),
                    display_order=sub.display_order,
                    project_count=by_subarea.get((area.key.value, sub.key.value), 0),
                )
                for sub in ordered(area.subareas)
            )
            overviews.append(
                AreaOverview(
                    id=str(area.id) if area.id else None,
                    key=area.key.value,
                    name=area.name.to_dict(),
                    blurb=area.blurb.to_dict() if area.blurb else None,
                    display_order=area.display_order,
                    status=area.status.value,
                    project_count=by_area.get(area.key.value, 0),
                    subareas=subareas,
                )
            )
        return tuple(overviews)
