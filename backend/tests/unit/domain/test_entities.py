"""Invariantes de las entidades."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from src.domain.entities.certification import Certification
from src.domain.entities.contact import Contact
from src.domain.entities.education import Education
from src.domain.entities.experience import Experience
from src.domain.entities.media import MediaAsset, MediaKind, Rendition
from src.domain.entities.message import MAX_BODY_LENGTH, Message
from src.domain.entities.publication import Publication
from src.domain.value_objects.date_range import DateRange
from src.domain.value_objects.localized_text import LocalizedText
from src.domain.value_objects.slug import Slug
from tests.conftest import make_project


def test_experiencia_vigente_no_admite_fecha_de_fin() -> None:
    with pytest.raises(ValueError):
        Experience(
            slug=Slug("x"),
            company=LocalizedText.of("A"),
            position=LocalizedText.of("B"),
            period=DateRange(date(2020, 1, 1), date(2021, 1, 1)),
            is_current=True,
        )


def test_certificacion_no_puede_caducar_antes_de_emitirse() -> None:
    with pytest.raises(ValueError):
        Certification(
            slug=Slug("pcep"),
            name=LocalizedText.of("PCEP"),
            issuer=LocalizedText.of("OpenEDG"),
            issued_on=date(2024, 1, 1),
            expires_on=date(2023, 1, 1),
        )


def test_educacion_rechaza_anio_absurdo() -> None:
    with pytest.raises(ValueError):
        Education(
            institution=LocalizedText.of("UTA"),
            title=LocalizedText.of("Ingeniero Civil"),
            graduation_year=18,
        )


def test_publicacion_exige_kind_normalizado() -> None:
    with pytest.raises(ValueError):
        Publication(slug=Slug("x"), kind="Libro Impreso", title=LocalizedText.of("T"))


def test_contacto_exige_valor() -> None:
    with pytest.raises(ValueError):
        Contact(kind="github", value="  ")


class TestMessage:
    def _build(self, **overrides: object) -> Message:
        payload: dict[str, object] = {
            "name": "Ana",
            "email": "ana@example.com",
            "body": "Hola",
            "created_at": datetime(2026, 3, 1, tzinfo=UTC),
        }
        payload.update(overrides)
        return Message(**payload)  # type: ignore[arg-type]

    def test_valida_email(self) -> None:
        with pytest.raises(ValueError):
            self._build(email="ana@example")

    def test_limita_el_tamano_del_cuerpo(self) -> None:
        with pytest.raises(ValueError):
            self._build(body="x" * (MAX_BODY_LENGTH + 1))

    def test_marcar_leido(self) -> None:
        message = self._build()
        assert not message.read
        message.mark_read()
        assert message.read


class TestMediaAsset:
    def test_exige_storage_path(self) -> None:
        with pytest.raises(ValueError):
            MediaAsset(kind=MediaKind.IMAGE, storage_path="  ")

    def test_localiza_una_rendition(self) -> None:
        asset = MediaAsset(
            kind=MediaKind.VIDEO,
            storage_path="projects/videos/1.mp4",
            renditions=(
                Rendition("1080", "projects/videos/1-1080.mp4", 3980000),
                Rendition("720", "projects/videos/1-720.mp4", 1800000),
            ),
        )
        assert asset.rendition("720").bytes == 1800000
        assert asset.rendition("480") is None


class TestProjectTaxonomy:
    def test_pertenencia_por_area(self) -> None:
        project = make_project("p", tags=(("data", "analyst"), ("developer", "backend")))
        assert project.belongs_to(area=None, subarea=None)
        assert len(project.areas) == 2

    def test_subarea_se_evalua_dentro_de_su_area(self) -> None:
        from src.domain.value_objects.taxonomy_keys import AreaKey, SubareaKey

        project = make_project("p", tags=(("data", "analyst"), ("developer", "backend")))
        assert project.belongs_to(AreaKey("data"), SubareaKey("analyst"))
        # 'backend' existe, pero no bajo 'data'.
        assert not project.belongs_to(AreaKey("data"), SubareaKey("backend"))
