"""El adaptador JSON sobre el contenido real del repo.

Comprueba que `content/catalog.seed.json` + `content/media-manifest.json` entran
enteros y con las rutas de la convencion A4. Si el seed no esta (checkout parcial),
los tests se saltan en vez de fallar por algo que no es del backend.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pytest

from src.application.use_cases.catalog.list_areas import ListAreas
from src.application.use_cases.content.list_content import ListContent
from src.application.use_cases.profile.get_profile import GetProfile
from src.application.use_cases.projects.list_projects import ListProjects
from src.domain.repositories.filters import ContentFilter, ProjectFilter
from src.domain.value_objects.storage_path import StoragePath
from src.domain.value_objects.taxonomy_keys import AreaKey
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence import serialization as ser
from src.infrastructure.persistence.json.repositories import (
    JsonContentRepository,
    JsonProfileRepository,
    JsonProjectRepository,
    JsonTaxonomyRepository,
)
from src.infrastructure.persistence.json.store import JsonCatalogStore

SETTINGS = Settings()
SEED = SETTINGS.seed_path
MANIFEST = SETTINGS.media_manifest_path

pytestmark = pytest.mark.skipif(
    not SEED.exists(), reason="content/catalog.seed.json no esta en el checkout"
)


@lru_cache(maxsize=1)
def _seed() -> dict:
    """El seed crudo, para derivar lo esperado en vez de congelar conteos."""
    return json.loads(SEED.read_text(encoding="utf-8"))


@pytest.fixture
def store(tmp_path: Path) -> JsonCatalogStore:
    return JsonCatalogStore(
        seed_path=SEED,
        write_path=tmp_path / "catalog.local.json",
        manifest_path=MANIFEST if MANIFEST.exists() else None,
    )


async def test_todos_los_proyectos_publicados_del_seed_entran(store: JsonCatalogStore) -> None:
    esperados = [p for p in _seed()["projects"] if p.get("status") == "published"]
    items = await ListProjects(JsonProjectRepository(store)).execute(ProjectFilter.public())
    assert len(items) == len(esperados)
    assert all(p.title.resolve("es") for p in items)
    assert {p.slug.value for p in items} == {p["slug"] for p in esperados}


async def test_el_filtro_por_area_coincide_con_la_taxonomia_del_seed(
    store: JsonCatalogStore,
) -> None:
    # Se deriva del seed en vez de fijar un numero: asi el test sigue midiendo el
    # filtrado cuando el contenido cambia, en vez de romperse por cambiar.
    for area in ("data", "developer", "civil-bim"):
        esperados = {
            p["slug"]
            for p in _seed()["projects"]
            if p.get("status") == "published"
            and any(t["area"] == area for t in p.get("taxonomy", []))
        }
        criteria = ProjectFilter.public(AreaKey(area))
        items = await ListProjects(JsonProjectRepository(store)).execute(criteria)
        assert {p.slug.value for p in items} == esperados, area


async def test_conteos_de_areas_sobre_el_seed_real(store: JsonCatalogStore) -> None:
    list_areas = ListAreas(
        JsonTaxonomyRepository(store), ListProjects(JsonProjectRepository(store))
    )
    areas = {a.key: a for a in await list_areas.execute()}
    assert set(areas) == {"data", "developer", "civil-bim"}
    publicados = [p for p in _seed()["projects"] if p.get("status") == "published"]
    for key, area in areas.items():
        esperado = sum(1 for p in publicados if any(t["area"] == key for t in p.get("taxonomy", [])))
        assert area.project_count == esperado, key
    # Un proyecto puede estar en varias areas, asi que la suma pasa del total.
    assert sum(a.project_count for a in areas.values()) >= len(publicados)


async def test_el_perfil_conserva_el_bilinguismo(store: JsonCatalogStore) -> None:
    profile = await GetProfile(JsonProfileRepository(store)).execute()
    assert profile.name.startswith("F")
    assert profile.bio.resolve("es") != profile.bio.resolve("en")


async def test_experiencia_vigente_del_seed(store: JsonCatalogStore) -> None:
    repository = JsonContentRepository(
        store, "experiences", ser.experience_from_row, ser.experience_to_row
    )
    items = await ListContent(repository).execute(ContentFilter.public())
    esperados = [e for e in _seed()["experiences"] if e.get("status") == "published"]
    assert len(items) == len(esperados)
    # Coherencia interna: un puesto vigente no puede tener fecha de fin.
    vigentes = [e for e in items if e.is_current]
    assert vigentes, "el seed deberia traer al menos un puesto vigente"
    assert all(e.end_date is None for e in vigentes)


@pytest.mark.skipif(not MANIFEST.exists(), reason="sin media-manifest.json")
class TestMediaManifestConvention:
    async def test_las_rutas_llevan_el_prefijo_del_bucket(self, store: JsonCatalogStore) -> None:
        items = await ListProjects(JsonProjectRepository(store)).execute(ProjectFilter.public())
        paths = [asset.storage_path for project in items for asset in project.media] + [
            p.thumbnail_path for p in items if p.thumbnail_path
        ]
        assert paths, "el seed deberia traer media"
        assert all(path.startswith("media/") for path in paths), paths[:5]

    async def test_los_videos_traen_poster_y_renditions(self, store: JsonCatalogStore) -> None:
        items = await ListProjects(JsonProjectRepository(store)).execute(ProjectFilter.public())
        videos = [a for p in items for a in p.media if a.kind.value == "video"]
        assert videos
        for video in videos:
            assert video.poster_path and video.poster_path.startswith("media/")
            assert {r.label for r in video.renditions} == {"720", "1080"}
            assert all(r.path.startswith("media/") and r.bytes > 0 for r in video.renditions)
            assert video.duration_seconds and video.duration_seconds > 0

    async def test_url_publica_segun_la_convencion(self, store: JsonCatalogStore) -> None:
        items = await ListProjects(JsonProjectRepository(store)).execute(ProjectFilter.public())
        video = next(a for p in items for a in p.media if a.kind.value == "video")
        path = StoragePath(video.storage_path)
        assert path.bucket == "media"
        assert not path.object_key.startswith("media/")
        assert path.public_url("https://xyz.supabase.co") == (
            f"https://xyz.supabase.co/storage/v1/object/public/{video.storage_path}"
        )
