"""La API completa, arrancada con el adaptador JSON y el verificador de desarrollo.

Es la prueba de que el backend arranca y responde con datos reales sin ninguna
infraestructura levantada, y de que `/admin` exige token de verdad.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.config.container import Container
from src.infrastructure.config.settings import (
    AuthBackend,
    Environment,
    PersistenceBackend,
    Settings,
)
from src.infrastructure.web.fastapi_app import create_app

DEV_TOKEN = "token-de-desarrollo"
BASE_URL = "https://xyzcompany.supabase.co"
PREFIX = "/api/v1"
AUTH = {"Authorization": f"Bearer {DEV_TOKEN}"}

DEFAULT_SETTINGS = Settings()
SEED = DEFAULT_SETTINGS.seed_path

pytestmark = pytest.mark.skipif(
    not SEED.exists(), reason="content/catalog.seed.json no esta en el checkout"
)


@pytest.fixture
async def client(tmp_path: Path):
    settings = Settings(
        environment=Environment.DEVELOPMENT,
        persistence_backend=PersistenceBackend.JSON,
        auth_backend=AuthBackend.DEV,
        dev_admin_token=DEV_TOKEN,
        seed_path=SEED,
        media_manifest_path=DEFAULT_SETTINGS.media_manifest_path,
        json_write_path=tmp_path / "catalog.local.json",
        media_public_base_url=BASE_URL,
        cors_origins=("http://localhost:3000",),
    ).validate()
    container = await Container(settings).init()
    with TestClient(create_app(container)) as test_client:
        yield test_client


class TestHealth:
    def test_health_no_pide_auth(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["persistence"] == "json"


class TestPublicRoutes:
    def test_catalogo_completo(self, client: TestClient) -> None:
        payload = client.get(f"{PREFIX}/catalog").json()
        # Sin numero fijo: el catalogo cambia con el contenido, la invariante no.
        assert payload["projects"]
        assert len(payload["areas"]) == 3
        assert payload["profile"]["name"]
        assert payload["media_base_url"] == BASE_URL

    def test_catalogo_resuelve_el_locale(self, client: TestClient) -> None:
        payload = client.get(f"{PREFIX}/catalog", params={"locale": "en"}).json()
        titles = [p["title"] for p in payload["projects"]]
        assert all(isinstance(title, str) for title in titles)

    def test_sin_locale_devuelve_el_mapa_bilingue(self, client: TestClient) -> None:
        payload = client.get(f"{PREFIX}/catalog").json()
        assert isinstance(payload["projects"][0]["title"], dict)

    def test_proyectos_filtrados_por_area(self, client: TestClient) -> None:
        response = client.get(f"{PREFIX}/projects", params={"area": "developer"})
        assert response.status_code == 200
        assert response.json()

    def test_area_sin_proyectos_devuelve_lista_vacia_no_error(self, client: TestClient) -> None:
        # Una subarea sin contenido debe dar 200 y lista vacia, no 404 ni error.
        response = client.get(
            f"{PREFIX}/projects", params={"area": "civil-bim", "subarea": "bim"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_subarea_sin_area_es_422(self, client: TestClient) -> None:
        response = client.get(f"{PREFIX}/projects", params={"subarea": "analyst"})
        assert response.status_code == 422

    def test_detalle_de_proyecto(self, client: TestClient) -> None:
        slug = client.get(f"{PREFIX}/projects").json()[0]["slug"]
        payload = client.get(f"{PREFIX}/projects/{slug}").json()
        assert payload["slug"] == slug
        assert "media" in payload

    def test_proyecto_inexistente_es_404(self, client: TestClient) -> None:
        response = client.get(f"{PREFIX}/projects/no-existe")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"

    def test_slug_invalido_es_422(self, client: TestClient) -> None:
        assert client.get(f"{PREFIX}/projects/NO_VALIDO").status_code == 422

    def test_areas_con_conteos(self, client: TestClient) -> None:
        areas = {a["key"]: a for a in client.get(f"{PREFIX}/areas").json()}
        assert set(areas) == {"data", "developer", "civil-bim"}
        assert all(isinstance(a["project_count"], int) for a in areas.values())
        assert all("subareas" in area for area in areas.values())

    @pytest.mark.parametrize(
        "resource", ["experiences", "certifications", "education", "publications", "contacts"]
    )
    def test_listados_publicos(self, client: TestClient, resource: str) -> None:
        response = client.get(f"{PREFIX}/{resource}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_formulario_de_contacto(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/messages",
            json={"name": "Ana", "email": "ana@example.com", "body": "Hola"},
        )
        assert response.status_code == 201
        # No se devuelve el cuerpo del mensaje al publico.
        assert set(response.json()) == {"id", "created_at"}

    def test_formulario_con_email_invalido(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/messages",
            json={"name": "Ana", "email": "no-es-email", "body": "Hola"},
        )
        assert response.status_code == 422


class TestAdminAuthorization:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("get", "/admin/projects"),
            ("post", "/admin/projects"),
            ("get", "/admin/messages"),
            ("post", "/admin/media/upload-url"),
            ("get", "/admin/profile"),
            ("post", "/admin/revalidate"),
        ],
    )
    def test_sin_token_es_401(self, client: TestClient, method: str, path: str) -> None:
        kwargs = {"json": {}} if method == "post" else {}
        response = getattr(client, method)(f"{PREFIX}{path}", **kwargs)
        # 401 antes de mirar el cuerpo: la autorizacion va primero.
        assert response.status_code == 401

    def test_token_incorrecto_es_401(self, client: TestClient) -> None:
        response = client.get(f"{PREFIX}/admin/projects", headers={"Authorization": "Bearer nope"})
        assert response.status_code == 401

    def test_cabecera_mal_formada_es_401(self, client: TestClient) -> None:
        response = client.get(f"{PREFIX}/admin/projects", headers={"Authorization": DEV_TOKEN})
        assert response.status_code == 401


class TestAdminRoutes:
    def test_listado_admin_incluye_borradores(self, client: TestClient) -> None:
        publicos = client.get(f"{PREFIX}/projects").json()
        admin = client.get(f"{PREFIX}/admin/projects", headers=AUTH).json()
        assert len(admin) >= len(publicos)

    def test_alta_actualizacion_y_borrado_de_proyecto(self, client: TestClient) -> None:
        nuevo = {
            "slug": "puente-atirantado",
            "title": {"es": "Puente atirantado", "en": "Cable-stayed bridge"},
            "status": "draft",
            "taxonomy": [{"area": "civil-bim", "subarea": "structural"}],
        }
        created = client.post(f"{PREFIX}/admin/projects", json=nuevo, headers=AUTH)
        assert created.status_code == 201
        project_id = created.json()["id"]

        # Publicar con un PATCH parcial: el titulo no viaja y no debe perderse.
        patched = client.patch(
            f"{PREFIX}/admin/projects/{project_id}",
            json={"status": "published"},
            headers=AUTH,
        )
        assert patched.status_code == 200
        assert patched.json()["title"]["en"] == "Cable-stayed bridge"
        assert patched.json()["status"] == "published"

        # Ya es visible en la ruta publica de su area.
        # Aparece entre los del area. Se comprueba pertenencia, no la lista
        # entera: el area ya tiene contenido real y fijarla congelaria el seed.
        def slugs_civil() -> list[str]:
            respuesta = client.get(f"{PREFIX}/projects", params={"area": "civil-bim"})
            return [p["slug"] for p in respuesta.json()]

        assert "puente-atirantado" in slugs_civil()

        assert (
            client.delete(f"{PREFIX}/admin/projects/{project_id}", headers=AUTH).status_code == 204
        )
        assert "puente-atirantado" not in slugs_civil()

    def test_slug_duplicado_es_409(self, client: TestClient) -> None:
        # 409 y no 422: el cuerpo es valido, lo que choca es el estado de la base.
        slug = client.get(f"{PREFIX}/projects").json()[0]["slug"]
        response = client.post(
            f"{PREFIX}/admin/projects",
            json={"slug": slug, "title": {"es": "Duplicado"}},
            headers=AUTH,
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "conflict"
        assert slug in response.json()["error"]["message"]

    def test_payload_con_campos_desconocidos_es_422(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/admin/projects",
            json={"slug": "x", "title": {"es": "X"}, "campo_inventado": 1},
            headers=AUTH,
        )
        assert response.status_code == 422

    def test_titulo_sin_espanol_es_422(self, client: TestClient) -> None:
        # Invariante del dominio (D5), no del esquema pydantic.
        response = client.post(
            f"{PREFIX}/admin/projects",
            json={"slug": "solo-ingles", "title": {"en": "Only english"}},
            headers=AUTH,
        )
        assert response.status_code == 422

    def test_recurso_desconocido_es_404(self, client: TestClient) -> None:
        assert client.get(f"{PREFIX}/admin/inventado", headers=AUTH).status_code == 404

    def test_reorder_en_bloque(self, client: TestClient) -> None:
        items = client.get(f"{PREFIX}/admin/projects", headers=AUTH).json()
        ids = [p["id"] for p in items]
        response = client.post(
            f"{PREFIX}/admin/projects/reorder", json={"ids": list(reversed(ids))}, headers=AUTH
        )
        assert response.status_code == 200
        assert [p["id"] for p in response.json()] == list(reversed(ids))

    def test_bandeja_de_mensajes(self, client: TestClient) -> None:
        client.post(
            f"{PREFIX}/messages",
            json={"name": "Ana", "email": "ana@example.com", "body": "Hola"},
        )
        inbox = client.get(f"{PREFIX}/admin/messages", headers=AUTH).json()
        assert inbox[0]["email"] == "ana@example.com"
        assert inbox[0]["read"] is False

    def test_url_de_subida_respeta_la_convencion_de_rutas(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/admin/media/upload-url",
            json={"filename": "captura.webp", "content_type": "image/webp"},
            headers=AUTH,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["storage_path"].startswith("media/uploads/")
        assert payload["public_url"] == (
            f"{BASE_URL}/storage/v1/object/public/{payload['storage_path']}"
        )

    def test_nombre_de_fichero_con_separadores_se_rechaza(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/admin/media/upload-url",
            json={"filename": "../../etc/passwd", "content_type": "image/webp"},
            headers=AUTH,
        )
        assert response.status_code == 422

    def test_content_type_no_permitido_se_rechaza(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/admin/media/upload-url",
            json={"filename": "script.sh", "content_type": "application/x-sh"},
            headers=AUTH,
        )
        assert response.status_code == 422

    def test_alta_de_subarea(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/admin/subareas",
            json={
                "area": "civil-bim",
                "key": "geotecnia",
                "name": {"es": "Geotecnia"},
                "display_order": 9,
            },
            headers=AUTH,
        )
        assert response.status_code == 201
        assert response.json()["key"] == "geotecnia"

    def test_revalidacion_sin_url_configurada_no_rompe(self, client: TestClient) -> None:
        response = client.post(f"{PREFIX}/admin/revalidate", json={}, headers=AUTH)
        assert response.status_code == 200
        assert response.json()["accepted"] is False


class TestCors:
    def test_origen_permitido(self, client: TestClient) -> None:
        response = client.get(f"{PREFIX}/areas", headers={"Origin": "http://localhost:3000"})
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_origen_no_permitido(self, client: TestClient) -> None:
        response = client.get(f"{PREFIX}/areas", headers={"Origin": "https://atacante.test"})
        assert "access-control-allow-origin" not in response.headers


class TestAreasAreFixed:
    """`/data`, `/developer` y `/civil-bim` son rutas del App Router: no se crean."""

    def _area_id(self, client: TestClient, key: str) -> str:
        areas = client.get(f"{PREFIX}/admin/areas", headers=AUTH).json()
        return next(a for a in areas if a["key"] == key)["id"]

    def test_crear_un_area_devuelve_405_con_explicacion(self, client: TestClient) -> None:
        response = client.post(
            f"{PREFIX}/admin/areas",
            json={"key": "iot", "name": {"es": "IoT"}},
            headers=AUTH,
        )
        assert response.status_code == 405
        assert response.headers["Allow"] == "GET, PATCH"
        assert "rutas del frontend" in response.json()["detail"]

    def test_borrar_un_area_devuelve_405(self, client: TestClient) -> None:
        area_id = self._area_id(client, "data")
        response = client.delete(f"{PREFIX}/admin/areas/{area_id}", headers=AUTH)
        assert response.status_code == 405
        assert response.headers["Allow"] == "GET, PATCH"
        assert len(client.get(f"{PREFIX}/admin/areas", headers=AUTH).json()) == 3

    def test_las_405_siguen_exigiendo_token(self, client: TestClient) -> None:
        # La autorizacion va antes que la regla de negocio.
        assert client.post(f"{PREFIX}/admin/areas", json={}).status_code == 401

    def test_editar_un_area(self, client: TestClient) -> None:
        area_id = self._area_id(client, "civil-bim")
        response = client.patch(
            f"{PREFIX}/admin/areas/{area_id}",
            json={
                "name": {"es": "Civil y BIM", "en": "Civil & BIM"},
                "blurb": {"es": "Estructuras, modelado y automatizacion"},
                "display_order": 5,
            },
            headers=AUTH,
        )
        assert response.status_code == 200
        assert response.json()["key"] == "civil-bim"
        assert response.json()["name"]["en"] == "Civil & BIM"
        assert response.json()["display_order"] == 5

    def test_patch_parcial_no_borra_el_resto(self, client: TestClient) -> None:
        area_id = self._area_id(client, "data")
        client.patch(
            f"{PREFIX}/admin/areas/{area_id}",
            json={"name": {"es": "Datos", "en": "Data"}},
            headers=AUTH,
        )
        response = client.patch(
            f"{PREFIX}/admin/areas/{area_id}", json={"display_order": 2}, headers=AUTH
        )
        assert response.json()["name"]["en"] == "Data"
        assert response.json()["display_order"] == 2

    def test_cambiar_la_clave_es_422(self, client: TestClient) -> None:
        area_id = self._area_id(client, "data")
        response = client.patch(
            f"{PREFIX}/admin/areas/{area_id}", json={"key": "datos"}, headers=AUTH
        )
        assert response.status_code == 422
        assert "ruta del frontend" in response.json()["error"]["message"]

    def test_despublicar_un_area_la_oculta_del_publico(self, client: TestClient) -> None:
        area_id = self._area_id(client, "civil-bim")
        client.patch(
            f"{PREFIX}/admin/areas/{area_id}", json={"status": "draft"}, headers=AUTH
        )
        publicas = {a["key"] for a in client.get(f"{PREFIX}/areas").json()}
        assert publicas == {"data", "developer"}
        assert len(client.get(f"{PREFIX}/admin/areas", headers=AUTH).json()) == 3

    def test_las_subareas_conservan_el_ciclo_completo(self, client: TestClient) -> None:
        created = client.post(
            f"{PREFIX}/admin/subareas",
            json={"area": "civil-bim", "key": "geotecnia", "name": {"es": "Geotecnia"}},
            headers=AUTH,
        )
        assert created.status_code == 201
        subarea_id = created.json()["id"]
        assert (
            client.delete(f"{PREFIX}/admin/subareas/{subarea_id}", headers=AUTH).status_code
            == 204
        )

    def test_borrar_un_area_por_la_ruta_de_subareas_es_403(self, client: TestClient) -> None:
        # El puerto comparte un unico `delete`; el caso de uso distingue el tipo.
        area_id = self._area_id(client, "data")
        response = client.delete(f"{PREFIX}/admin/subareas/{area_id}", headers=AUTH)
        assert response.status_code == 403
        assert "rutas fijas" in response.json()["error"]["message"]


class TestUniquenessOverHttp:
    def test_contacto_duplicado_es_409(self, client: TestClient) -> None:
        payload = {"kind": "github", "value": "https://github.com/MFelix9310"}
        first = client.post(f"{PREFIX}/admin/contacts", json=payload, headers=AUTH)
        assert first.status_code in (201, 409)
        response = client.post(f"{PREFIX}/admin/contacts", json=payload, headers=AUTH)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "conflict"

    def test_media_duplicada_es_409(self, client: TestClient) -> None:
        project_id = client.get(f"{PREFIX}/admin/projects", headers=AUTH).json()[0]["id"]
        payload = {
            "project_id": project_id,
            "kind": "image",
            "storage_path": "media/projects/duplicada.webp",
        }
        assert client.post(f"{PREFIX}/admin/media", json=payload, headers=AUTH).status_code == 200
        response = client.post(f"{PREFIX}/admin/media", json=payload, headers=AUTH)
        assert response.status_code == 409
        assert "media/projects/duplicada.webp" in response.json()["error"]["message"]

    def test_la_misma_ruta_en_otro_proyecto_es_200(self, client: TestClient) -> None:
        projects = client.get(f"{PREFIX}/admin/projects", headers=AUTH).json()
        for project in projects[:2]:
            response = client.post(
                f"{PREFIX}/admin/media",
                json={
                    "project_id": project["id"],
                    "kind": "image",
                    "storage_path": "media/projects/compartida.webp",
                },
                headers=AUTH,
            )
            assert response.status_code == 200
