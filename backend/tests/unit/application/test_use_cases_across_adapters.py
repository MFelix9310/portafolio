"""Suite de casos de uso ejecutada contra cada adaptador de persistencia.

Ningun test de este fichero menciona JSON ni Supabase: hablan solo con casos de uso.
Si el dominio dependiera de la infraestructura, esta suite no podria existir.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.application.dto.commands import (
    NewMessageCommand,
    ReorderCommand,
    UpdateAreaCommand,
)
from src.application.errors import (
    ConflictError,
    ForbiddenOperationError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.catalog.get_catalog import GetCatalog
from src.application.use_cases.catalog.list_areas import ListAreas
from src.application.use_cases.contacts.save_contact import SaveContact
from src.application.use_cases.content.delete_content import DeleteContent
from src.application.use_cases.content.get_content import GetContent
from src.application.use_cases.content.list_content import ListContent
from src.application.use_cases.content.reorder_content import ReorderContent
from src.application.use_cases.content.save_content import SaveContent
from src.application.use_cases.media.delete_media import DeleteMedia
from src.application.use_cases.media.list_project_media import ListProjectMedia
from src.application.use_cases.media.save_media import SaveMedia
from src.application.use_cases.messages.create_message import CreateMessage
from src.application.use_cases.messages.list_messages import ListMessages
from src.application.use_cases.profile.get_profile import GetProfile
from src.application.use_cases.profile.save_profile import SaveProfile
from src.application.use_cases.projects.delete_project import DeleteProject
from src.application.use_cases.projects.get_project import GetProject
from src.application.use_cases.projects.list_projects import ListProjects
from src.application.use_cases.projects.reorder_projects import ReorderProjects
from src.application.use_cases.projects.save_project import SaveProject
from src.application.use_cases.taxonomy.delete_subarea import DeleteSubarea
from src.application.use_cases.taxonomy.list_subareas import ListSubareas
from src.application.use_cases.taxonomy.save_subarea import SaveSubarea
from src.application.use_cases.taxonomy.update_area import UpdateArea
from src.domain.entities.certification import Certification
from src.domain.entities.contact import Contact
from src.domain.entities.media import MediaAsset, MediaKind
from src.domain.entities.taxonomy import Subarea
from src.domain.repositories.filters import ContentFilter, ProjectFilter
from src.domain.value_objects.localized_text import LocalizedText
from src.domain.value_objects.publication_status import PublicationStatus
from src.domain.value_objects.slug import Slug
from src.domain.value_objects.taxonomy_keys import AreaKey, SubareaKey
from tests.conftest import make_experience, make_profile, make_project
from tests.fakes.adapters import FakeMediaStorage, FixedClock


async def _seed_projects(repos) -> list:
    """Alta a traves del caso de uso, nunca escribiendo al almacen por detras."""
    save = SaveProject(repos.projects)
    created = []
    for project in (
        make_project("laboratorios", tags=(("developer", "backend"),), display_order=0),
        make_project(
            "petshop",
            tags=(("developer", "fullstack"), ("data", "analyst")),
            display_order=1,
        ),
        make_project("pandeo", tags=(("data", "scientist"), ("data", "analyst")), display_order=2),
        make_project(
            "borrador",
            tags=(("data", "scientist"),),
            status=PublicationStatus.DRAFT,
            display_order=3,
        ),
    ):
        project.id = None
        created.append(await save.execute(project))
    return created


class TestProjectsAcrossAdapters:
    async def test_alta_y_listado_publico(self, repos) -> None:
        await _seed_projects(repos)
        items = await ListProjects(repos.projects).execute(ProjectFilter.public())
        assert {p.slug.value for p in items} == {"laboratorios", "petshop", "pandeo"}

    async def test_admin_ve_los_borradores(self, repos) -> None:
        await _seed_projects(repos)
        items = await ListProjects(repos.projects).execute(ProjectFilter(status=None))
        assert "borrador" in {p.slug.value for p in items}

    async def test_filtrado_por_area_y_subarea(self, repos) -> None:
        await _seed_projects(repos)
        criteria = ProjectFilter.public(AreaKey("data"), SubareaKey("analyst"))
        items = await ListProjects(repos.projects).execute(criteria)
        assert {p.slug.value for p in items} == {"petshop", "pandeo"}

    async def test_civil_bim_arranca_vacio(self, repos) -> None:
        await _seed_projects(repos)
        criteria = ProjectFilter.public(AreaKey("civil-bim"))
        assert await ListProjects(repos.projects).execute(criteria) == []

    async def test_detalle_por_slug_y_bilinguismo(self, repos) -> None:
        await _seed_projects(repos)
        project = await GetProject(repos.projects).execute(Slug("petshop"))
        assert project.title.resolve("en") == "Title petshop"
        assert project.summary.resolve("en") == "Resumen petshop"  # fallback a es

    async def test_borrador_no_es_visible_por_slug(self, repos) -> None:
        await _seed_projects(repos)
        with pytest.raises(NotFoundError):
            await GetProject(repos.projects).execute(Slug("borrador"))

    async def test_slug_duplicado(self, repos) -> None:
        await _seed_projects(repos)
        clon = make_project("petshop")
        clon.id = None
        with pytest.raises(ConflictError):
            await SaveProject(repos.projects).execute(clon)

    async def test_actualizacion_conserva_identidad(self, repos) -> None:
        created = await _seed_projects(repos)
        target = created[0]
        target.status = PublicationStatus.DRAFT
        await SaveProject(repos.projects).execute(target)
        items = await ListProjects(repos.projects).execute(ProjectFilter.public())
        assert "laboratorios" not in {p.slug.value for p in items}

    async def test_borrado(self, repos) -> None:
        created = await _seed_projects(repos)
        await DeleteProject(repos.projects).execute(created[0].id)
        items = await ListProjects(repos.projects).execute(ProjectFilter(status=None))
        assert "laboratorios" not in {p.slug.value for p in items}

    async def test_borrado_de_inexistente(self, repos) -> None:
        created = await _seed_projects(repos)
        await DeleteProject(repos.projects).execute(created[0].id)
        with pytest.raises(NotFoundError):
            await DeleteProject(repos.projects).execute(created[0].id)

    async def test_reorder(self, repos) -> None:
        created = await _seed_projects(repos)
        command = ReorderCommand((created[2].id, created[0].id, created[1].id))
        await ReorderProjects(repos.projects).execute(command)
        items = await ListProjects(repos.projects).execute(ProjectFilter(status=None))
        assert [p.slug.value for p in items][:3] == ["pandeo", "laboratorios", "petshop"]


class TestContentResourcesAcrossAdapters:
    async def test_ciclo_completo_de_experiencias(self, repos) -> None:
        repository = repos.content["experiences"]
        experience = make_experience("espoch")
        experience.id = None
        saved = await SaveContent(repository).execute(experience)
        assert saved.id is not None

        listed = await ListContent(repository).execute(ContentFilter.public())
        assert [e.slug.value for e in listed] == ["espoch"]

        fetched = await GetContent(repository, "experiences").execute(saved.id)
        assert fetched.position.resolve("en") == "Data engineer"

        await DeleteContent(repository, "experiences").execute(saved.id)
        assert await ListContent(repository).execute(ContentFilter.everything()) == []

    async def test_borradores_ocultos_en_listado_publico(self, repos) -> None:
        repository = repos.content["experiences"]
        draft = make_experience("borrador-exp", status=PublicationStatus.DRAFT)
        draft.id = None
        await SaveContent(repository).execute(draft)
        assert await ListContent(repository).execute(ContentFilter.public()) == []
        assert len(await ListContent(repository).execute(ContentFilter.everything())) == 1

    async def test_reorder_de_certificaciones(self, repos) -> None:
        repository = repos.content["certifications"]
        save = SaveContent(repository)
        ids = []
        for index, slug in enumerate(("pcep", "pcap", "aws")):
            cert = Certification(
                slug=Slug(slug),
                name=LocalizedText.of(slug.upper()),
                issuer=LocalizedText.of("Institucion"),
                issued_on=date(2024, 1, 1),
                status=PublicationStatus.PUBLISHED,
                display_order=index,
            )
            ids.append((await save.execute(cert)).id)

        await ReorderContent(repository).execute(ReorderCommand((ids[2], ids[0], ids[1])))
        listed = await ListContent(repository).execute(ContentFilter.public())
        assert [c.slug.value for c in listed] == ["aws", "pcep", "pcap"]

    async def test_get_de_inexistente(self, repos) -> None:
        from uuid import uuid4

        with pytest.raises(NotFoundError):
            await GetContent(repos.content["education"], "education").execute(uuid4())


class TestProfileAndMessagesAcrossAdapters:
    async def test_perfil_ausente_y_luego_guardado(self, repos) -> None:
        get = GetProfile(repos.profile)
        assert await get.execute(required=False) is None
        with pytest.raises(NotFoundError):
            await get.execute()

        profile = make_profile()
        profile.id = None
        await SaveProfile(repos.profile).execute(profile)
        stored = await get.execute()
        assert stored.name == "Felix Ruiz M."
        assert stored.bio.resolve("en") == "Data specialist."

    async def test_mensaje_del_formulario(self, repos) -> None:
        clock = FixedClock()
        created = await CreateMessage(repos.messages, clock).execute(
            NewMessageCommand(name="Ana", email="ana@example.com", body="Hola")
        )
        assert created.created_at == clock.now()
        assert not created.read

        inbox = await ListMessages(repos.messages).execute()
        assert [m.email for m in inbox] == ["ana@example.com"]
        assert len(await ListMessages(repos.messages).execute(unread_only=True)) == 1

    async def test_mensaje_con_email_invalido(self, repos) -> None:
        with pytest.raises(ValidationError):
            await CreateMessage(repos.messages, FixedClock()).execute(
                NewMessageCommand(name="Ana", email="no-es-un-email", body="Hola")
            )


class TestTaxonomyAndCatalogAcrossAdapters:
    async def test_areas_con_conteos(self, repos) -> None:
        await _seed_projects(repos)
        list_areas = ListAreas(repos.taxonomy, ListProjects(repos.projects))
        areas = {a.key: a for a in await list_areas.execute()}

        assert areas["civil-bim"].project_count == 0
        assert areas["data"].project_count == 2
        subareas = {s.key: s.project_count for s in areas["data"].subareas}
        assert subareas == {"analyst": 2, "scientist": 1, "engineer": 0}

    async def test_areas_admin_incluye_borradores_en_el_conteo(self, repos) -> None:
        await _seed_projects(repos)
        list_areas = ListAreas(repos.taxonomy, ListProjects(repos.projects))
        areas = {a.key: a for a in await list_areas.execute(include_drafts=True)}
        assert areas["data"].project_count == 3

    async def test_alta_de_subarea(self, repos) -> None:
        subarea = Subarea(
            key=SubareaKey("geotecnia"),
            name=LocalizedText.of("Geotecnia"),
            area_key=AreaKey("civil-bim"),
            display_order=9,
        )
        await SaveSubarea(repos.taxonomy).execute(subarea)
        keys = {
            s.key.value for s in await ListSubareas(repos.taxonomy).execute(AreaKey("civil-bim"))
        }
        assert "geotecnia" in keys

    async def test_subarea_duplicada_en_la_misma_area(self, repos) -> None:
        subarea = Subarea(
            key=SubareaKey("bim"),
            name=LocalizedText.of("BIM otra vez"),
            area_key=AreaKey("civil-bim"),
        )
        with pytest.raises(ConflictError):
            await SaveSubarea(repos.taxonomy).execute(subarea)

    async def test_catalogo_completo(self, repos) -> None:
        await _seed_projects(repos)
        profile = make_profile()
        profile.id = None
        await SaveProfile(repos.profile).execute(profile)

        catalog = GetCatalog(
            list_projects=ListProjects(repos.projects),
            list_areas=ListAreas(repos.taxonomy, ListProjects(repos.projects)),
            list_experiences=ListContent(repos.content["experiences"]),
            list_certifications=ListContent(repos.content["certifications"]),
            list_education=ListContent(repos.content["education"]),
            list_publications=ListContent(repos.content["publications"]),
            list_contacts=ListContent(repos.content["contacts"]),
            get_profile=GetProfile(repos.profile),
        )
        view = await catalog.execute(locale="en")
        assert view.locale == "en"
        assert view.profile is not None
        assert len(view.projects) == 3
        assert len(view.areas) == 3

    async def test_catalogo_filtrado_por_area(self, repos) -> None:
        await _seed_projects(repos)
        catalog = GetCatalog(
            list_projects=ListProjects(repos.projects),
            list_areas=ListAreas(repos.taxonomy, ListProjects(repos.projects)),
            list_experiences=ListContent(repos.content["experiences"]),
            list_certifications=ListContent(repos.content["certifications"]),
            list_education=ListContent(repos.content["education"]),
            list_publications=ListContent(repos.content["publications"]),
            list_contacts=ListContent(repos.content["contacts"]),
            get_profile=GetProfile(repos.profile),
        )
        view = await catalog.execute(area=AreaKey("developer"))
        assert {p.slug.value for p in view.projects} == {"laboratorios", "petshop"}


class TestMediaAcrossAdapters:
    async def test_alta_listado_y_borrado_de_media(self, repos) -> None:
        created = await _seed_projects(repos)
        project = created[0]
        asset = MediaAsset(
            kind=MediaKind.VIDEO,
            storage_path="projects/videos/1.mp4",
            project_id=project.id,
            display_order=0,
        )
        saved = await SaveMedia(repos.media).execute(asset)
        assert saved.id is not None

        listed = await ListProjectMedia(repos.media).execute(project.id)
        assert [a.storage_path for a in listed] == ["projects/videos/1.mp4"]

        storage = FakeMediaStorage()
        await DeleteMedia(repos.media, storage).execute(saved.id)
        assert storage.deleted == ["projects/videos/1.mp4"]
        assert await ListProjectMedia(repos.media).execute(project.id) == []


class TestUniquenessAcrossAdapters:
    """Claves unicas del addendum A5, impuestas en la aplicacion.

    Es justo la divergencia que el test de equivalencia de payload no alcanzaba:
    comparaba lecturas, y esto solo se manifiesta al escribir. Antes de imponerla,
    el adaptador JSON aceptaba el duplicado y el de Supabase reventaba en el upsert.
    """

    async def test_media_duplicada_en_el_mismo_proyecto(self, repos) -> None:
        created = await _seed_projects(repos)
        project = created[0]
        save = SaveMedia(repos.media)
        await save.execute(
            MediaAsset(
                kind=MediaKind.IMAGE,
                storage_path="media/projects/1.webp",
                project_id=project.id,
            )
        )
        with pytest.raises(ConflictError) as exc:
            await save.execute(
                MediaAsset(
                    kind=MediaKind.IMAGE,
                    storage_path="media/projects/1.webp",
                    project_id=project.id,
                )
            )
        assert "media/projects/1.webp" in str(exc.value)
        assert len(await ListProjectMedia(repos.media).execute(project.id)) == 1

    async def test_la_misma_ruta_en_otro_proyecto_si_se_permite(self, repos) -> None:
        created = await _seed_projects(repos)
        save = SaveMedia(repos.media)
        for project in (created[0], created[1]):
            await save.execute(
                MediaAsset(
                    kind=MediaKind.IMAGE,
                    storage_path="media/projects/compartida.webp",
                    project_id=project.id,
                )
            )
        assert len(await ListProjectMedia(repos.media).execute(created[0].id)) == 1
        assert len(await ListProjectMedia(repos.media).execute(created[1].id)) == 1

    async def test_actualizar_una_media_no_choca_consigo_misma(self, repos) -> None:
        created = await _seed_projects(repos)
        save = SaveMedia(repos.media)
        asset = await save.execute(
            MediaAsset(
                kind=MediaKind.IMAGE,
                storage_path="media/projects/1.webp",
                project_id=created[0].id,
            )
        )
        asset.display_order = 5
        assert (await save.execute(asset)).display_order == 5

    async def test_media_sin_proyecto_se_rechaza(self, repos) -> None:
        with pytest.raises(ValidationError):
            await SaveMedia(repos.media).execute(
                MediaAsset(kind=MediaKind.IMAGE, storage_path="media/x.webp")
            )

    async def test_contacto_duplicado_kind_y_value(self, repos) -> None:
        repository = repos.content["contacts"]
        save = SaveContact(repository)
        await save.execute(
            Contact(
                kind="github",
                value="https://github.com/MFelix9310",
                status=PublicationStatus.PUBLISHED,
            )
        )
        with pytest.raises(ConflictError) as exc:
            await save.execute(
                Contact(
                    kind="github",
                    value="https://github.com/MFelix9310",
                    status=PublicationStatus.PUBLISHED,
                )
            )
        assert "kind" in str(exc.value)
        assert len(await ListContent(repository).execute(ContentFilter.everything())) == 1

    async def test_mismo_kind_con_otro_value_se_permite(self, repos) -> None:
        repository = repos.content["contacts"]
        save = SaveContact(repository)
        for value in ("mailto:a@example.com", "mailto:b@example.com"):
            await save.execute(
                Contact(kind="email", value=value, status=PublicationStatus.PUBLISHED)
            )
        assert len(await ListContent(repository).execute(ContentFilter.everything())) == 2

    async def test_actualizar_un_contacto_no_choca_consigo_mismo(self, repos) -> None:
        repository = repos.content["contacts"]
        save = SaveContact(repository)
        contact = await save.execute(
            Contact(kind="linkedin", value="https://linkedin.com/in/felix")
        )
        contact.status = PublicationStatus.PUBLISHED
        assert (await save.execute(contact)).status is PublicationStatus.PUBLISHED


class TestAreasAreFixedAcrossAdapters:
    """Las areas se editan, no se crean ni se borran: son rutas del frontend."""

    async def _area(self, repos, key: str):
        return next(a for a in await repos.taxonomy.list_areas() if a.key.value == key)

    async def test_no_existe_caso_de_uso_para_crear_areas(self) -> None:
        # La ausencia es la garantia: si alguien anade SaveArea, este test lo señala.
        import src.application.use_cases.taxonomy as taxonomy

        assert not hasattr(taxonomy, "SaveArea")
        assert sorted(taxonomy.__all__) == [
            "DeleteSubarea",
            "ListSubareas",
            "SaveSubarea",
            "UpdateArea",
        ]

    async def test_editar_nombre_descripcion_y_orden(self, repos) -> None:
        area = await self._area(repos, "civil-bim")
        updated = await UpdateArea(repos.taxonomy).execute(
            UpdateAreaCommand(
                area_id=area.id,
                name=LocalizedText.of("Civil y BIM", "Civil & BIM"),
                blurb=LocalizedText.of("Estructuras y modelado"),
                display_order=7,
            )
        )
        assert updated.name.resolve("en") == "Civil & BIM"
        assert updated.blurb.resolve() == "Estructuras y modelado"
        assert updated.display_order == 7
        assert updated.key.value == "civil-bim"

    async def test_cambiar_la_clave_se_rechaza(self, repos) -> None:
        area = await self._area(repos, "data")
        with pytest.raises(ValidationError, match="ruta del frontend"):
            await UpdateArea(repos.taxonomy).execute(
                UpdateAreaCommand(area_id=area.id, key=AreaKey("datos"))
            )

    async def test_repetir_la_misma_clave_no_es_un_cambio(self, repos) -> None:
        area = await self._area(repos, "data")
        updated = await UpdateArea(repos.taxonomy).execute(
            UpdateAreaCommand(area_id=area.id, key=AreaKey("data"), display_order=3)
        )
        assert updated.display_order == 3

    async def test_area_inexistente(self, repos) -> None:
        from uuid import uuid4

        with pytest.raises(NotFoundError):
            await UpdateArea(repos.taxonomy).execute(UpdateAreaCommand(area_id=uuid4()))

    async def test_despublicar_un_area_la_oculta_del_listado_publico(self, repos) -> None:
        area = await self._area(repos, "civil-bim")
        await UpdateArea(repos.taxonomy).execute(
            UpdateAreaCommand(area_id=area.id, status=PublicationStatus.DRAFT)
        )
        list_areas = ListAreas(repos.taxonomy, ListProjects(repos.projects))
        assert {a.key for a in await list_areas.execute()} == {"data", "developer"}
        # El panel las sigue viendo todas.
        assert len(await list_areas.execute(include_drafts=True)) == 3

    async def test_borrar_un_area_se_rechaza(self, repos) -> None:
        area = await self._area(repos, "data")
        with pytest.raises(ForbiddenOperationError, match="rutas fijas"):
            await DeleteSubarea(repos.taxonomy).execute(area.id)
        assert len(await repos.taxonomy.list_areas()) == 3

    async def test_borrar_una_subarea_si_funciona(self, repos) -> None:
        subareas = await ListSubareas(repos.taxonomy).execute(AreaKey("civil-bim"))
        target = next(s for s in subareas if s.key.value == "bim")
        await DeleteSubarea(repos.taxonomy).execute(target.id)
        remaining = await ListSubareas(repos.taxonomy).execute(AreaKey("civil-bim"))
        assert "bim" not in {s.key.value for s in remaining}
