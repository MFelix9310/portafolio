"""Servicios de dominio: logica pura sin estado."""

from .catalog import (
    apply_reorder,
    count_projects_by_area,
    count_projects_by_subarea,
    filter_by_taxonomy,
    ordered,
    visible,
)

__all__ = [
    "apply_reorder",
    "count_projects_by_area",
    "count_projects_by_subarea",
    "filter_by_taxonomy",
    "ordered",
    "visible",
]
