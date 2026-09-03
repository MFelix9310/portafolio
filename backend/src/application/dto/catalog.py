"""DTO del catalogo completo y de la vista de areas con conteos."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...domain.entities.certification import Certification
from ...domain.entities.contact import Contact
from ...domain.entities.education import Education
from ...domain.entities.experience import Experience
from ...domain.entities.profile import Profile
from ...domain.entities.project import Project
from ...domain.entities.publication import Publication
from ...domain.entities.taxonomy import Area


@dataclass(frozen=True, slots=True)
class SubareaOverview:
    """Subarea con el numero de proyectos publicados que cuelgan de ella."""

    key: str
    name: dict[str, str]
    display_order: int
    project_count: int


@dataclass(frozen=True, slots=True)
class AreaOverview:
    id: str | None
    key: str
    name: dict[str, str]
    blurb: dict[str, str] | None
    display_order: int
    status: str
    project_count: int
    subareas: tuple[SubareaOverview, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CatalogView:
    """Todo lo que el front necesita para construir el sitio en una sola llamada."""

    profile: Profile | None
    areas: tuple[AreaOverview, ...]
    projects: tuple[Project, ...]
    experiences: tuple[Experience, ...]
    certifications: tuple[Certification, ...]
    education: tuple[Education, ...]
    publications: tuple[Publication, ...]
    contacts: tuple[Contact, ...]
    locale: str | None = None


@dataclass(frozen=True, slots=True)
class AreaListView:
    areas: tuple[AreaOverview, ...]
    raw_areas: tuple[Area, ...] = field(default_factory=tuple)
