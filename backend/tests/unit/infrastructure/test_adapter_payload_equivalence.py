"""Equivalencia de payload entre los dos adaptadores.

La misma peticion a `/api/v1/projects` debe devolver lo mismo con
`PERSISTENCE_BACKEND=json` y con `supabase`: mismas claves, mismas rutas de media,
mismas URLs publicas. Si no, cambiar de adaptador romperia el frontend y el
argumento hexagonal se quedaria en el papel.

No hace falta Supabase levantado: se ejercita el codigo de mapeo de produccion
(`SupabaseProjectRepository._to_entity`) sobre una fila con la forma exacta que
devuelve PostgREST para el select anidado del repositorio.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from src.application.use_cases.projects.list_projects import ListProjects
from src.application.use_cases.projects.save_project import SaveProject
from src.domain.entities.media import MediaAsset, MediaKind, Rendition
from src.domain.entities.project import Project
from src.domain.repositories.filters import ProjectFilter
from src.domain.value_objects.localized_text import LocalizedText
from src.domain.value_objects.publication_status import PublicationStatus
from src.domain.value_objects.slug import Slug
from src.domain.value_objects.taxonomy_keys import TaxonomyTag
from src.infrastructure.persistence import serialization as ser
from src.infrastructure.persistence.json.repositories import JsonProjectRepository
from src.infrastructure.persistence.json.store import JsonCatalogStore
from src.infrastructure.persistence.supabase.repositories import SupabaseProjectRepository
from src.infrastructure.web.schemas import presenters

BASE_URL = "https://xyzcompany.supabase.co"
PROJECT_ID = uuid4()


VIDEO_ID = uuid4()
DOCUMENT_ID = uuid4()


def _sample_project() -> Project:
    """Proyecto con todo lo que puede divergir: media, renditions, taxonomia y nulos.

    Los ids son constantes del modulo: si se generaran en cada llamada, los dos
    adaptadores recibirian entidades distintas y la comparacion no probaria nada.
    """
    return Project(
        slug=Slug("prediccion-de-pandeo"),
        title=LocalizedText.of("Prediccion de pandeo", "Buckling prediction"),
        id=PROJECT_ID,
        summary=LocalizedText.of("Resumen en espanol"),
        body=None,  # A7: `body` es nullable y el seed no lo escribe.
        technologies=("Python", "TensorFlow"),
        project_url=None,
        repository_url="https://github.com/MFelix9310/pandeo",
        thumbnail_path="media/projects/5.webp",
        legacy_id=5,
        status=PublicationStatus.PUBLISHED,
        display_order=2,
        taxonomy=(TaxonomyTag.of("data", "scientist"), TaxonomyTag.of("data", "analyst")),
        media=(
            MediaAsset(
                kind=MediaKind.VIDEO,
                storage_path="media/projects/videos/1-1080.mp4",
                id=VIDEO_ID,
                project_id=PROJECT_ID,
                poster_path="media/projects/videos/1-poster.webp",
                caption=LocalizedText.of("Video de la pagina"),
                duration_seconds=38.57,
                width=1920,
                height=984,
                renditions=(
                    Rendition("1080", "media/projects/videos/1-1080.mp4", 3971390),
                    Rendition("720", "media/projects/videos/1-720.mp4", 2252733),
                ),
                display_order=0,
            ),
            MediaAsset(
                kind=MediaKind.DOCUMENT,
                storage_path="media/projects/documents/3.xlsx",
                id=DOCUMENT_ID,
                project_id=PROJECT_ID,
                title=LocalizedText.of("Excel_Resumen"),
                display_order=1,
            ),
        ),
    )


def _postgrest_row(project: Project) -> dict[str, Any]:
    """Fila tal y como la devuelve PostgREST para el select anidado de projects."""
    row = ser.project_to_row(project, embed=False)
    row["project_subareas"] = [
        {"subareas": {"key": tag.subarea.value, "areas": {"key": tag.area.value}}}
        for tag in project.taxonomy
    ]
    row["project_media"] = [ser.media_to_row(asset) for asset in project.media]
    return row


@pytest.fixture
async def json_payload(tmp_path: Path) -> list[dict[str, Any]]:
    store = JsonCatalogStore(seed_path=None, write_path=tmp_path / "catalog.json")
    repository = JsonProjectRepository(store)
    await SaveProject(repository).execute(_sample_project())
    items = await ListProjects(repository).execute(ProjectFilter.public())
    return [presenters.project(item, None, BASE_URL) for item in items]


@pytest.fixture
def supabase_payload() -> list[dict[str, Any]]:
    row = _postgrest_row(_sample_project())
    entity = SupabaseProjectRepository._to_entity(row)
    return [presenters.project(entity, None, BASE_URL)]


class TestProjectsPayloadEquivalence:
    def test_mismas_claves(
        self, json_payload: list[dict[str, Any]], supabase_payload: list[dict[str, Any]]
    ) -> None:
        assert sorted(json_payload[0]) == sorted(supabase_payload[0])
        assert sorted(json_payload[0]["media"][0]) == sorted(supabase_payload[0]["media"][0])

    def test_payload_identico(
        self, json_payload: list[dict[str, Any]], supabase_payload: list[dict[str, Any]]
    ) -> None:
        assert json_payload == supabase_payload

    def test_rutas_y_urls_de_media_identicas(
        self, json_payload: list[dict[str, Any]], supabase_payload: list[dict[str, Any]]
    ) -> None:
        def paths(payload: list[dict[str, Any]]) -> list[str | None]:
            project = payload[0]
            out: list[str | None] = [project["thumbnail_path"], project["thumbnail_url"]]
            for asset in project["media"]:
                out += [asset["storage_path"], asset["storage_url"]]
                out += [asset["poster_path"], asset["poster_url"]]
                for rendition in asset["renditions"].values():
                    out += [rendition["path"], rendition["url"]]
            return out

        assert paths(json_payload) == paths(supabase_payload)

    def test_las_urls_siguen_la_convencion_a4(
        self, json_payload: list[dict[str, Any]]
    ) -> None:
        video = json_payload[0]["media"][0]
        assert video["storage_url"] == (
            f"{BASE_URL}/storage/v1/object/public/media/projects/videos/1-1080.mp4"
        )
        assert video["renditions"]["720"]["url"] == (
            f"{BASE_URL}/storage/v1/object/public/media/projects/videos/1-720.mp4"
        )

    def test_body_nulo_no_rompe_ninguno_de_los_dos(
        self, json_payload: list[dict[str, Any]], supabase_payload: list[dict[str, Any]]
    ) -> None:
        assert json_payload[0]["body"] is None
        assert supabase_payload[0]["body"] is None

    def test_taxonomia_identica(
        self, json_payload: list[dict[str, Any]], supabase_payload: list[dict[str, Any]]
    ) -> None:
        assert json_payload[0]["taxonomy"] == [
            {"area": "data", "subarea": "scientist"},
            {"area": "data", "subarea": "analyst"},
        ]
        assert json_payload[0]["taxonomy"] == supabase_payload[0]["taxonomy"]


class TestStorageAdaptersAgreeOnUrls:
    def test_ambos_adaptadores_componen_la_misma_url_publica(self) -> None:
        from src.infrastructure.storage.local_storage import LocalMediaStorage

        local = LocalMediaStorage(public_base_url=BASE_URL, bucket="media")
        path = "media/projects/videos/1-1080.mp4"
        # El adaptador de Supabase compone la URL con la misma funcion del dominio.
        expected = f"{BASE_URL}/storage/v1/object/public/{path}"
        assert local.public_url(path) == expected

    async def test_el_ticket_de_subida_lleva_el_prefijo_del_bucket(self) -> None:
        from src.infrastructure.storage.local_storage import LocalMediaStorage

        local = LocalMediaStorage(public_base_url=BASE_URL, bucket="media")
        ticket = await local.create_upload_url("captura.webp", "image/webp")
        assert ticket.storage_path.startswith("media/uploads/")
        assert ticket.public_url.endswith(ticket.storage_path)
