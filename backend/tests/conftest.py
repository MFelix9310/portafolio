"""Constructores compartidos por los tests."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.domain.entities.experience import Experience
from src.domain.entities.profile import Profile
from src.domain.entities.project import Project
from src.domain.entities.taxonomy import Area, Subarea
from src.domain.value_objects.date_range import DateRange
from src.domain.value_objects.localized_text import LocalizedText
from src.domain.value_objects.publication_status import PublicationStatus
from src.domain.value_objects.slug import Slug
from src.domain.value_objects.taxonomy_keys import (
    SEED_SUBAREA_KEYS,
    AreaKey,
    SubareaKey,
    TaxonomyTag,
)


def make_project(
    slug: str,
    *,
    tags: tuple[tuple[str, str], ...] = (),
    status: PublicationStatus = PublicationStatus.PUBLISHED,
    display_order: int = 0,
    project_id: UUID | None = None,
) -> Project:
    return Project(
        slug=Slug(slug),
        title=LocalizedText.of(f"Titulo {slug}", f"Title {slug}"),
        summary=LocalizedText.of(f"Resumen {slug}"),
        id=project_id or uuid4(),
        status=status,
        display_order=display_order,
        taxonomy=tuple(TaxonomyTag.of(area, sub) for area, sub in tags),
        technologies=("Python",),
    )


def make_experience(
    slug: str,
    *,
    status: PublicationStatus = PublicationStatus.PUBLISHED,
    display_order: int = 0,
) -> Experience:
    return Experience(
        slug=Slug(slug),
        company=LocalizedText.of("ESPOCH"),
        position=LocalizedText.of("Ingeniero de datos", "Data engineer"),
        period=DateRange(date(2022, 5, 24)),
        is_current=True,
        status=status,
        display_order=display_order,
        id=uuid4(),
    )


def make_profile() -> Profile:
    return Profile(
        name="Felix Ruiz M.",
        headline=LocalizedText.of("Python Developer & Data Scientist"),
        bio=LocalizedText.of("Especialista en datos.", "Data specialist."),
        id=uuid4(),
    )


def seed_areas() -> list[Area]:
    """Las tres areas del contrato con sus subareas."""
    areas: list[Area] = []
    for order, (area_key, subarea_keys) in enumerate(SEED_SUBAREA_KEYS.items()):
        area_id = uuid4()
        areas.append(
            Area(
                key=AreaKey(area_key),
                name=LocalizedText.of(area_key.title()),
                id=area_id,
                display_order=order,
                subareas=tuple(
                    Subarea(
                        key=SubareaKey(sub),
                        name=LocalizedText.of(sub.title()),
                        area_key=AreaKey(area_key),
                        id=uuid4(),
                        area_id=area_id,
                        display_order=index,
                    )
                    for index, sub in enumerate(subarea_keys)
                ),
            )
        )
    return areas


@pytest.fixture
def areas() -> list[Area]:
    return seed_areas()


@pytest.fixture
def projects() -> list[Project]:
    """Muestra fiel al seed: cruces multi-area y ningun proyecto en civil-bim."""
    return [
        make_project("laboratorios", tags=(("developer", "backend"),), display_order=0),
        make_project(
            "petshop",
            tags=(("developer", "fullstack"), ("data", "analyst")),
            display_order=1,
        ),
        make_project(
            "pandeo",
            tags=(("data", "scientist"), ("data", "analyst")),
            display_order=2,
        ),
        make_project(
            "borrador",
            tags=(("data", "scientist"),),
            status=PublicationStatus.DRAFT,
            display_order=3,
        ),
    ]
