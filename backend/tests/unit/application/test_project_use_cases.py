"""Casos de uso de proyectos contra un repositorio en memoria."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.dto.commands import ReorderCommand
from src.application.errors import ConflictError, NotFoundError
from src.application.use_cases.projects.delete_project import DeleteProject
from src.application.use_cases.projects.get_project import GetProject
from src.application.use_cases.projects.list_projects import ListProjects
from src.application.use_cases.projects.reorder_projects import ReorderProjects
from src.application.use_cases.projects.save_project import SaveProject
from src.domain.entities.project import Project
from src.domain.repositories.filters import ProjectFilter
from src.domain.value_objects.publication_status import PublicationStatus
from src.domain.value_objects.slug import Slug
from src.domain.value_objects.taxonomy_keys import AreaKey, SubareaKey
from tests.conftest import make_project
from tests.fakes.repositories import InMemoryProjectRepository


@pytest.fixture
def repository(projects: list[Project]) -> InMemoryProjectRepository:
    return InMemoryProjectRepository(projects)


class TestListProjects:
    async def test_publico_no_ve_borradores(
        self, repository: InMemoryProjectRepository
    ) -> None:
        result = await ListProjects(repository).execute(ProjectFilter.public())
        assert "borrador" not in {p.slug.value for p in result}

    async def test_admin_ve_borradores(
        self, repository: InMemoryProjectRepository
    ) -> None:
        result = await ListProjects(repository).execute(ProjectFilter(status=None))
        assert "borrador" in {p.slug.value for p in result}

    async def test_filtra_por_area_y_subarea(
        self, repository: InMemoryProjectRepository
    ) -> None:
        criteria = ProjectFilter.public(AreaKey("data"), SubareaKey("analyst"))
        result = await ListProjects(repository).execute(criteria)
        assert {p.slug.value for p in result} == {"petshop", "pandeo"}

    async def test_area_sin_proyectos_devuelve_vacio(
        self, repository: InMemoryProjectRepository
    ) -> None:
        criteria = ProjectFilter.public(AreaKey("civil-bim"))
        assert await ListProjects(repository).execute(criteria) == []

    async def test_sin_filtro_explicito_asume_publico(
        self, repository: InMemoryProjectRepository
    ) -> None:
        assert len(await ListProjects(repository).execute()) == 3


class TestGetProject:
    async def test_devuelve_el_proyecto_publicado(
        self, repository: InMemoryProjectRepository
    ) -> None:
        project = await GetProject(repository).execute(Slug("petshop"))
        assert project.title.resolve("en") == "Title petshop"

    async def test_borrador_es_404_para_el_publico(
        self, repository: InMemoryProjectRepository
    ) -> None:
        with pytest.raises(NotFoundError):
            await GetProject(repository).execute(Slug("borrador"))

    async def test_borrador_visible_para_admin(
        self, repository: InMemoryProjectRepository
    ) -> None:
        project = await GetProject(repository).execute(
            Slug("borrador"), include_drafts=True
        )
        assert project.status is PublicationStatus.DRAFT

    async def test_inexistente(self, repository: InMemoryProjectRepository) -> None:
        with pytest.raises(NotFoundError):
            await GetProject(repository).execute(Slug("no-existe"))


class TestSaveProject:
    async def test_crea_asignando_id(
        self, repository: InMemoryProjectRepository
    ) -> None:
        nuevo = make_project("puente-bim", tags=(("civil-bim", "bim"),))
        nuevo.id = None
        guardado = await SaveProject(repository).execute(nuevo)
        assert guardado.id is not None
        assert await repository.get_by_slug(Slug("puente-bim")) is not None

    async def test_rechaza_slug_duplicado(
        self, repository: InMemoryProjectRepository
    ) -> None:
        duplicado = make_project("petshop")
        duplicado.id = None
        with pytest.raises(ConflictError):
            await SaveProject(repository).execute(duplicado)

    async def test_permite_actualizar_conservando_el_slug(
        self, repository: InMemoryProjectRepository
    ) -> None:
        existente = await repository.get_by_slug(Slug("petshop"))
        assert existente is not None
        existente.display_order = 9
        guardado = await SaveProject(repository).execute(existente)
        assert guardado.display_order == 9


class TestDeleteAndReorder:
    async def test_borrado_de_inexistente(
        self, repository: InMemoryProjectRepository
    ) -> None:
        with pytest.raises(NotFoundError):
            await DeleteProject(repository).execute(uuid4())

    async def test_borrado_efectivo(
        self, repository: InMemoryProjectRepository, projects: list[Project]
    ) -> None:
        await DeleteProject(repository).execute(projects[0].id)
        assert await repository.get(projects[0].id) is None

    async def test_reorder_persiste_el_nuevo_orden(
        self, repository: InMemoryProjectRepository, projects: list[Project]
    ) -> None:
        command = ReorderCommand((projects[2].id, projects[1].id, projects[0].id))
        await ReorderProjects(repository).execute(command)
        result = await ListProjects(repository).execute(ProjectFilter(status=None))
        assert [p.slug.value for p in result][:3] == ["pandeo", "petshop", "laboratorios"]

    async def test_reorder_rechaza_ids_duplicados(self) -> None:
        repeated = uuid4()
        with pytest.raises(ValueError):
            ReorderCommand((repeated, repeated))
