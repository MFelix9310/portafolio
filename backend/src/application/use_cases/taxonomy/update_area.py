"""Edicion de un area existente.

No hay caso de uso para crear ni para borrar areas, y esa ausencia es deliberada:
las tres areas son rutas del App Router del front. Un area creada desde el panel no
tendria pagina que la renderizara, y borrar una dejaria una ruta muerta con los
proyectos que colgaban de ella huerfanos. Lo unico editable es su contenido.
"""

from __future__ import annotations

from ....domain.entities.taxonomy import Area
from ....domain.repositories.taxonomy_repository import TaxonomyRepository
from ...dto.commands import UpdateAreaCommand
from ...errors import NotFoundError, ValidationError


class UpdateArea:
    def __init__(self, repository: TaxonomyRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateAreaCommand) -> Area:
        areas = await self._repository.list_areas()
        area = next((a for a in areas if a.id == command.area_id), None)
        if area is None:
            raise NotFoundError("area", command.area_id)

        # La clave es la ruta del front: cambiarla romperia /data, /developer o
        # /civil-bim sin que el panel tenga forma de saberlo.
        if command.key is not None and command.key != area.key:
            raise ValidationError(
                f"la clave del area no se puede cambiar ('{area.key}' -> '{command.key}'): "
                "es una ruta del frontend"
            )

        if command.name is not None:
            area.name = command.name
        if command.blurb is not None:
            area.blurb = command.blurb
        if command.display_order is not None:
            area.display_order = command.display_order
        if command.status is not None:
            area.status = command.status

        return await self._repository.save_area(area)
