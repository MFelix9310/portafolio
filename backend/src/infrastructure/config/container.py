"""Contenedor de inyeccion de dependencias, manual y explicito.

Aqui se decide que adaptador implementa cada puerto. Es el unico sitio del proyecto
donde `json` y `supabase` conviven; ni el dominio ni los casos de uso saben cual esta
enchufado, y eso es exactamente lo que demuestra que la regla de dependencia se
sostiene en la practica y no solo en el diagrama.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from ...application.ports.clock import ClockPort
from ...application.ports.media_storage import MediaStoragePort
from ...application.ports.revalidation import FrontendRevalidationPort
from ...application.use_cases.catalog.get_catalog import GetCatalog
from ...application.use_cases.catalog.list_areas import ListAreas
from ...application.use_cases.contacts.save_contact import SaveContact
from ...application.use_cases.content.delete_content import DeleteContent
from ...application.use_cases.content.get_content import GetContent
from ...application.use_cases.content.list_content import ListContent
from ...application.use_cases.content.reorder_content import ReorderContent
from ...application.use_cases.content.save_content import SaveContent
from ...application.use_cases.media.create_upload_url import CreateUploadUrl
from ...application.use_cases.media.delete_media import DeleteMedia
from ...application.use_cases.media.list_project_media import ListProjectMedia
from ...application.use_cases.media.reorder_media import ReorderMedia
from ...application.use_cases.media.save_media import SaveMedia
from ...application.use_cases.messages.create_message import CreateMessage
from ...application.use_cases.messages.list_messages import ListMessages
from ...application.use_cases.profile.get_profile import GetProfile
from ...application.use_cases.profile.save_profile import SaveProfile
from ...application.use_cases.projects.delete_project import DeleteProject
from ...application.use_cases.projects.get_project import GetProject
from ...application.use_cases.projects.get_project_by_id import GetProjectById
from ...application.use_cases.projects.list_projects import ListProjects
from ...application.use_cases.projects.reorder_projects import ReorderProjects
from ...application.use_cases.projects.save_project import SaveProject
from ...application.use_cases.revalidation.revalidate_frontend import RevalidateFrontend
from ...application.use_cases.taxonomy.delete_subarea import DeleteSubarea
from ...application.use_cases.taxonomy.list_subareas import ListSubareas
from ...application.use_cases.taxonomy.save_subarea import SaveSubarea
from ...application.use_cases.taxonomy.update_area import UpdateArea
from ..auth.dev_token import DevTokenVerifier
from ..auth.identity import AdminTokenVerifier
from ..auth.supabase_jwt import SupabaseJwtVerifier
from ..persistence import serialization as ser
from ..persistence.json.repositories import (
    JsonContentRepository,
    JsonMediaRepository,
    JsonMessageRepository,
    JsonProfileRepository,
    JsonProjectRepository,
    JsonTaxonomyRepository,
)
from ..persistence.json.store import JsonCatalogStore
from ..storage.local_storage import LocalMediaStorage
from ..storage.revalidation import HttpFrontendRevalidation, NoopRevalidation
from ..storage.system_clock import SystemClock
from .settings import AuthBackend, PersistenceBackend, Settings

logger = logging.getLogger("app.container")

# Recursos con firma identica: mismo juego de casos de uso, distinto repositorio.
UNIFORM_RESOURCES: tuple[tuple[str, str, Callable[..., Any], Callable[..., Any]], ...] = (
    ("experiences", "experiences", ser.experience_from_row, ser.experience_to_row),
    ("certifications", "certifications", ser.certification_from_row, ser.certification_to_row),
    ("education", "education", ser.education_from_row, ser.education_to_row),
    ("publications", "publications", ser.publication_from_row, ser.publication_to_row),
    ("contacts", "contacts", ser.contact_from_row, ser.contact_to_row),
)


@dataclass(slots=True)
class ResourceUseCases:
    """Bundle que consumen tanto las rutas publicas como las de /admin."""

    name: str
    list: Any
    get: Any
    save: Any
    delete: Any
    reorder: Any


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._supabase_client: Any | None = None
        self._json_store: JsonCatalogStore | None = None

        self.clock: ClockPort = SystemClock()
        self.storage: MediaStoragePort
        self.revalidation: FrontendRevalidationPort
        self.verifier: AdminTokenVerifier
        self.resources: dict[str, ResourceUseCases] = {}

    # ------------------------------------------------------------------ arranque

    async def init(self) -> "Container":
        repositories = await self._build_repositories()
        self.storage = await self._build_storage()
        self.revalidation = self._build_revalidation()
        self.verifier = self._build_verifier()
        self._wire_use_cases(repositories)
        logger.info(
            "container listo: persistencia=%s auth=%s entorno=%s",
            self.settings.persistence_backend.value,
            self.settings.auth_backend.value,
            self.settings.environment.value,
        )
        return self

    async def close(self) -> None:
        client = self._supabase_client
        if client is not None and hasattr(client, "auth"):
            await client.auth.sign_out()

    # -------------------------------------------------------------- adaptadores

    async def _supabase(self) -> Any:
        if self._supabase_client is None:
            from ..persistence.supabase.client import create_supabase_client

            self._supabase_client = await create_supabase_client(
                self.settings.supabase_url, self.settings.supabase_service_role_key
            )
        return self._supabase_client

    async def _build_repositories(self) -> dict[str, Any]:
        if self.settings.persistence_backend is PersistenceBackend.SUPABASE:
            return await self._supabase_repositories()
        return self._json_repositories()

    def _json_repositories(self) -> dict[str, Any]:
        store = JsonCatalogStore(
            seed_path=self.settings.seed_path,
            write_path=self.settings.json_write_path,
            manifest_path=self.settings.media_manifest_path,
        )
        self._json_store = store
        repositories: dict[str, Any] = {
            "projects": JsonProjectRepository(store),
            "profile": JsonProfileRepository(store),
            "messages": JsonMessageRepository(store),
            "taxonomy": JsonTaxonomyRepository(store),
            "media": JsonMediaRepository(store),
        }
        for name, collection, to_entity, to_row in UNIFORM_RESOURCES:
            repositories[name] = JsonContentRepository(store, collection, to_entity, to_row)
        return repositories

    async def _supabase_repositories(self) -> dict[str, Any]:
        from ..persistence.supabase.repositories import (
            SupabaseContentRepository,
            SupabaseMediaRepository,
            SupabaseMessageRepository,
            SupabaseProfileRepository,
            SupabaseProjectRepository,
            SupabaseTaxonomyRepository,
        )

        client = await self._supabase()
        repositories: dict[str, Any] = {
            "projects": SupabaseProjectRepository(client),
            "profile": SupabaseProfileRepository(client),
            "messages": SupabaseMessageRepository(client),
            "taxonomy": SupabaseTaxonomyRepository(client),
            "media": SupabaseMediaRepository(client),
        }
        for name, table, to_entity, to_row in UNIFORM_RESOURCES:
            repositories[name] = SupabaseContentRepository(client, table, to_entity, to_row)
        return repositories

    async def _build_storage(self) -> MediaStoragePort:
        if self.settings.persistence_backend is PersistenceBackend.SUPABASE:
            from ..storage.supabase_storage import SupabaseMediaStorage

            return SupabaseMediaStorage(
                await self._supabase(),
                self.settings.supabase_storage_bucket,
                self.settings.supabase_url,
            )
        # Misma base publica y misma convencion de rutas que Supabase: cambiar de
        # adaptador no mueve una sola URL del frontend (addendum A4).
        return LocalMediaStorage(
            public_base_url=self.settings.media_public_base_url,
            bucket=self.settings.supabase_storage_bucket,
        )

    def _build_revalidation(self) -> FrontendRevalidationPort:
        if self.settings.frontend_revalidate_url:
            return HttpFrontendRevalidation(
                self.settings.frontend_revalidate_url,
                self.settings.frontend_revalidate_secret,
            )
        return NoopRevalidation()

    def _build_verifier(self) -> AdminTokenVerifier:
        if self.settings.auth_backend is AuthBackend.DEV:
            # Settings.validate() ya garantiza que esto no ocurre en produccion.
            logger.warning("AUTH_BACKEND=dev activo: solo para desarrollo local")
            return DevTokenVerifier(self.settings.dev_admin_token)
        return SupabaseJwtVerifier(
            project_url=self.settings.supabase_url,
            audience=self.settings.supabase_jwt_audience,
            jwt_secret=self.settings.supabase_jwt_secret,
            admin_user_ids=self.settings.admin_user_ids,
        )

    # -------------------------------------------------------------- casos de uso

    def _wire_use_cases(self, repositories: dict[str, Any]) -> None:
        project_repo = repositories["projects"]
        self.list_projects = ListProjects(project_repo)
        self.get_project = GetProject(project_repo)
        self.get_project_by_id = GetProjectById(project_repo)
        self.save_project = SaveProject(project_repo)
        self.delete_project = DeleteProject(project_repo)
        self.reorder_projects = ReorderProjects(project_repo)
        self.resources["projects"] = ResourceUseCases(
            name="projects",
            list=self.list_projects,
            # El bundle expone la lectura por id: es la que usa /admin/{recurso}/{id}.
            # La lectura por slug la usa la ruta publica de detalle.
            get=self.get_project_by_id,
            save=self.save_project,
            delete=self.delete_project,
            reorder=self.reorder_projects,
        )

        for name, *_ in UNIFORM_RESOURCES:
            repository = repositories[name]
            # contacts es el unico con una clave unica compuesta (A5), asi que su
            # escritura pasa por un caso de uso propio en vez del generico.
            save = (
                SaveContact(repository) if name == "contacts" else SaveContent(repository)
            )
            self.resources[name] = ResourceUseCases(
                name=name,
                list=ListContent(repository),
                get=GetContent(repository, name),
                save=save,
                delete=DeleteContent(repository, name),
                reorder=ReorderContent(repository),
            )

        self.get_profile = GetProfile(repositories["profile"])
        self.save_profile = SaveProfile(repositories["profile"])

        taxonomy_repo = repositories["taxonomy"]
        self.list_areas = ListAreas(taxonomy_repo, self.list_projects)
        self.list_subareas = ListSubareas(taxonomy_repo)
        # No hay caso de uso para crear ni borrar areas: son rutas del frontend.
        self.update_area = UpdateArea(taxonomy_repo)
        self.save_subarea = SaveSubarea(taxonomy_repo)
        self.delete_subarea = DeleteSubarea(taxonomy_repo)

        self.create_message = CreateMessage(repositories["messages"], self.clock)
        self.list_messages = ListMessages(repositories["messages"])

        media_repo = repositories["media"]
        self.create_upload_url = CreateUploadUrl(self.storage)
        self.list_project_media = ListProjectMedia(media_repo)
        self.save_media = SaveMedia(media_repo)
        self.delete_media = DeleteMedia(media_repo, self.storage)
        self.reorder_media = ReorderMedia(media_repo)

        self.revalidate_frontend = RevalidateFrontend(self.revalidation)

        self.get_catalog = GetCatalog(
            list_projects=self.list_projects,
            list_areas=self.list_areas,
            list_experiences=self.resources["experiences"].list,
            list_certifications=self.resources["certifications"].list,
            list_education=self.resources["education"].list,
            list_publications=self.resources["publications"].list,
            list_contacts=self.resources["contacts"].list,
            get_profile=self.get_profile,
        )


async def build_container(settings: Settings | None = None) -> Container:
    resolved = (settings or Settings.from_env()).validate()
    return await Container(resolved).init()
