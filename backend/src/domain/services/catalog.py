"""Reglas de visibilidad y filtrado del catalogo.

Fuente unica del filtrado por area+subarea (D4). Tanto el caso de uso de catalogo
como los adaptadores de persistencia pasan por aqui; ninguno reimplementa el
predicado por su cuenta.
"""

from __future__ import annotations

from typing import Iterable, Protocol, Sequence, TypeVar

from ..entities.project import Project
from ..value_objects.publication_status import PublicationStatus
from ..value_objects.taxonomy_keys import AreaKey, SubareaKey


class Publishable(Protocol):
    """Cualquier entidad con estado y orden. Evita repetir el mismo filtro 8 veces."""

    status: PublicationStatus
    display_order: int


T = TypeVar("T", bound=Publishable)


def visible(items: Iterable[T], *, include_drafts: bool = False) -> list[T]:
    """Aplica la regla 1 de RLS en el dominio: sin borradores salvo peticion explicita."""
    if include_drafts:
        return list(items)
    return [item for item in items if item.status.is_public]


def ordered(items: Iterable[T]) -> list[T]:
    return sorted(items, key=lambda item: item.display_order)


def filter_by_taxonomy(
    projects: Iterable[Project],
    *,
    area: AreaKey | None = None,
    subarea: SubareaKey | None = None,
) -> list[Project]:
    """Vista filtrada del unico catalogo. Sin area ni subarea devuelve todo."""
    if subarea is not None and area is None:
        raise ValueError("una subarea solo tiene sentido dentro de un area")
    return [project for project in projects if project.belongs_to(area, subarea)]


def count_projects_by_subarea(
    projects: Iterable[Project],
) -> dict[tuple[str, str], int]:
    """Conteos para GET /areas. Clave: (area_key, subarea_key)."""
    counts: dict[tuple[str, str], int] = {}
    for project in projects:
        for tag in project.taxonomy:
            key = (tag.area.value, tag.subarea.value)
            counts[key] = counts.get(key, 0) + 1
    return counts


def count_projects_by_area(projects: Iterable[Project]) -> dict[str, int]:
    """Un proyecto cuenta una sola vez por area aunque tenga varias subareas."""
    counts: dict[str, int] = {}
    for project in projects:
        for area_key in {tag.area.value for tag in project.taxonomy}:
            counts[area_key] = counts.get(area_key, 0) + 1
    return counts


def apply_reorder(items: Sequence[T], ordered_ids: Sequence[object]) -> list[T]:
    """Reasigna display_order segun la secuencia recibida del panel.

    Los elementos no mencionados conservan su posicion relativa al final, de modo
    que un reorder parcial nunca borra el orden del resto.
    """
    position = {identifier: index for index, identifier in enumerate(ordered_ids)}
    tail = len(position)
    result: list[T] = []
    for offset, item in enumerate(ordered(items)):
        item_id = getattr(item, "id", None)
        item.display_order = position.get(item_id, tail + offset)
        result.append(item)
    return ordered(result)
