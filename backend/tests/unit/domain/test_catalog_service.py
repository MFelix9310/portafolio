"""El filtrado del catalogo vive en un unico sitio; aqui se comprueba que funciona."""

from __future__ import annotations

import pytest

from src.domain.entities.project import Project
from src.domain.services.catalog import (
    apply_reorder,
    count_projects_by_area,
    count_projects_by_subarea,
    filter_by_taxonomy,
    ordered,
    visible,
)
from src.domain.value_objects.publication_status import PublicationStatus
from src.domain.value_objects.taxonomy_keys import AreaKey, SubareaKey


def test_visible_oculta_borradores(projects: list[Project]) -> None:
    assert len(visible(projects)) == 3
    assert len(visible(projects, include_drafts=True)) == 4
    assert all(p.status is PublicationStatus.PUBLISHED for p in visible(projects))


def test_filtrado_por_area(projects: list[Project]) -> None:
    data = filter_by_taxonomy(projects, area=AreaKey("data"))
    assert {p.slug.value for p in data} == {"petshop", "pandeo", "borrador"}


def test_filtrado_por_area_y_subarea(projects: list[Project]) -> None:
    result = filter_by_taxonomy(
        projects, area=AreaKey("data"), subarea=SubareaKey("scientist")
    )
    assert {p.slug.value for p in result} == {"pandeo", "borrador"}


def test_civil_bim_devuelve_lista_vacia(projects: list[Project]) -> None:
    # Nace sin proyectos: cero resultados es un estado valido, no un error.
    assert filter_by_taxonomy(projects, area=AreaKey("civil-bim")) == []


def test_sin_filtros_devuelve_todo(projects: list[Project]) -> None:
    assert len(filter_by_taxonomy(projects)) == len(projects)


def test_subarea_sin_area_es_un_error(projects: list[Project]) -> None:
    with pytest.raises(ValueError):
        filter_by_taxonomy(projects, subarea=SubareaKey("analyst"))


def test_conteos_por_area_no_duplican_proyectos_multi_subarea(
    projects: list[Project],
) -> None:
    published = visible(projects)
    # 'pandeo' esta en data/scientist y data/analyst: cuenta una sola vez por area.
    assert count_projects_by_area(published) == {"data": 2, "developer": 2}
    assert count_projects_by_subarea(published)[("data", "analyst")] == 2


def test_ordered_usa_display_order(projects: list[Project]) -> None:
    revuelto = list(reversed(projects))
    assert [p.slug.value for p in ordered(revuelto)] == [
        "laboratorios",
        "petshop",
        "pandeo",
        "borrador",
    ]


def test_apply_reorder_respeta_la_secuencia_recibida(projects: list[Project]) -> None:
    nuevo_orden = [projects[2].id, projects[0].id]
    resultado = apply_reorder(projects, nuevo_orden)
    assert [p.slug.value for p in resultado][:2] == ["pandeo", "laboratorios"]
    # Los no mencionados quedan detras, conservando su orden relativo.
    assert [p.slug.value for p in resultado][2:] == ["petshop", "borrador"]
