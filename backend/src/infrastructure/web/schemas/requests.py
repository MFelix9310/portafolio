"""Esquemas pydantic de entrada.

Pydantic vive aqui, en la frontera HTTP, y en ningun otro sitio (D2). Cada modelo
sabe convertirse en la entidad de dominio correspondiente; si el dominio rechaza el
resultado, el manejador de errores lo traduce a 422.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ....application.dto.commands import UpdateAreaCommand
from ....domain.entities.certification import Certification
from ....domain.entities.contact import Contact
from ....domain.entities.education import Education
from ....domain.entities.experience import Experience
from ....domain.entities.media import MediaAsset, MediaKind, Rendition
from ....domain.entities.profile import Profile
from ....domain.entities.project import Project
from ....domain.entities.publication import Publication
from ....domain.entities.taxonomy import Subarea
from ....domain.value_objects.date_range import DateRange
from ....domain.value_objects.localized_text import LocalizedText
from ....domain.value_objects.publication_status import PublicationStatus
from ....domain.value_objects.slug import Slug
from ....domain.value_objects.taxonomy_keys import AreaKey, SubareaKey, TaxonomyTag
from ...persistence import serialization as ser

LocalizedField = Annotated[dict[str, str], Field(min_length=1)]
SlugField = Annotated[str, Field(min_length=1, max_length=120)]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _text(value: dict[str, str]) -> LocalizedText:
    return LocalizedText(value)


def _opt_text(value: dict[str, str] | None) -> LocalizedText | None:
    return LocalizedText.optional(value)


class TaxonomyTagIn(_Base):
    area: str
    subarea: str

    def to_domain(self) -> TaxonomyTag:
        return TaxonomyTag(AreaKey(self.area), SubareaKey(self.subarea))


class RenditionIn(_Base):
    path: str
    bytes: int = Field(ge=0)


class MediaAssetIn(_Base):
    id: UUID | None = None
    project_id: UUID | None = None
    kind: str
    storage_path: str = Field(min_length=1)
    poster_path: str | None = None
    caption: dict[str, str] | None = None
    title: dict[str, str] | None = None
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    renditions: dict[str, RenditionIn] = Field(default_factory=dict)
    display_order: int = 0

    def to_domain(self) -> MediaAsset:
        return MediaAsset(
            kind=MediaKind.parse(self.kind),
            storage_path=self.storage_path,
            id=self.id,
            project_id=self.project_id,
            poster_path=self.poster_path,
            caption=_opt_text(self.caption),
            title=_opt_text(self.title),
            duration_seconds=self.duration_seconds,
            width=self.width,
            height=self.height,
            renditions=tuple(
                Rendition(label=label, path=item.path, bytes=item.bytes)
                for label, item in sorted(self.renditions.items())
            ),
            display_order=self.display_order,
        )


class ProjectIn(_Base):
    id: UUID | None = None
    slug: SlugField
    title: LocalizedField
    summary: dict[str, str] | None = None
    body: dict[str, str] | None = None
    technologies: list[str] = Field(default_factory=list)
    project_url: str | None = None
    repository_url: str | None = None
    thumbnail_path: str | None = None
    legacy_id: int | None = None
    status: str = "draft"
    display_order: int = 0
    taxonomy: list[TaxonomyTagIn] = Field(default_factory=list)
    media: list[MediaAssetIn] = Field(default_factory=list)

    def to_domain(self) -> Project:
        return Project(
            slug=Slug(self.slug),
            title=_text(self.title),
            id=self.id,
            summary=_opt_text(self.summary),
            body=_opt_text(self.body),
            technologies=tuple(self.technologies),
            project_url=self.project_url,
            repository_url=self.repository_url,
            thumbnail_path=self.thumbnail_path,
            legacy_id=self.legacy_id,
            status=PublicationStatus.parse(self.status),
            display_order=self.display_order,
            taxonomy=tuple(tag.to_domain() for tag in self.taxonomy),
            media=tuple(asset.to_domain() for asset in self.media),
        )


class ExperienceIn(_Base):
    id: UUID | None = None
    slug: SlugField
    company: LocalizedField
    position: LocalizedField
    description: dict[str, str] | None = None
    keywords: list[str] = Field(default_factory=list)
    company_logo_path: str | None = None
    thumbnail_path: str | None = None
    legacy_id: int | None = None
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    status: str = "draft"
    display_order: int = 0

    def to_domain(self) -> Experience:
        return Experience(
            slug=Slug(self.slug),
            company=_text(self.company),
            position=_text(self.position),
            period=DateRange(self.start_date, self.end_date),
            id=self.id,
            description=_opt_text(self.description),
            keywords=tuple(self.keywords),
            company_logo_path=self.company_logo_path,
            thumbnail_path=self.thumbnail_path,
            legacy_id=self.legacy_id,
            is_current=self.is_current,
            status=PublicationStatus.parse(self.status),
            display_order=self.display_order,
        )


class CertificationIn(_Base):
    id: UUID | None = None
    slug: SlugField
    name: LocalizedField
    issuer: LocalizedField
    description: dict[str, str] | None = None
    issued_on: date
    expires_on: date | None = None
    credential_url: str | None = None
    certificate_path: str | None = None
    legacy_id: int | None = None
    status: str = "draft"
    display_order: int = 0

    def to_domain(self) -> Certification:
        return Certification(
            slug=Slug(self.slug),
            name=_text(self.name),
            issuer=_text(self.issuer),
            issued_on=self.issued_on,
            id=self.id,
            description=_opt_text(self.description),
            expires_on=self.expires_on,
            credential_url=self.credential_url,
            certificate_path=self.certificate_path,
            legacy_id=self.legacy_id,
            status=PublicationStatus.parse(self.status),
            display_order=self.display_order,
        )


class EducationIn(_Base):
    id: UUID | None = None
    institution: LocalizedField
    title: LocalizedField
    description: dict[str, str] | None = None
    graduation_year: int | None = None
    legacy_id: int | None = None
    status: str = "draft"
    display_order: int = 0

    def to_domain(self) -> Education:
        return Education(
            institution=_text(self.institution),
            title=_text(self.title),
            id=self.id,
            description=_opt_text(self.description),
            graduation_year=self.graduation_year,
            legacy_id=self.legacy_id,
            status=PublicationStatus.parse(self.status),
            display_order=self.display_order,
        )


class PublicationIn(_Base):
    id: UUID | None = None
    slug: SlugField
    kind: str = "article"
    title: LocalizedField
    authors: dict[str, str] | None = None
    venue: dict[str, str] | None = None
    abstract: dict[str, str] | None = None
    published_on: date | None = None
    doi: str | None = None
    isbn: str | None = None
    url: str | None = None
    pdf_path: str | None = None
    thumbnail_path: str | None = None
    legacy_id: int | None = None
    status: str = "draft"
    display_order: int = 0

    def to_domain(self) -> Publication:
        return Publication(
            slug=Slug(self.slug),
            kind=self.kind,
            title=_text(self.title),
            id=self.id,
            authors=_opt_text(self.authors),
            venue=_opt_text(self.venue),
            abstract=_opt_text(self.abstract),
            published_on=self.published_on,
            doi=self.doi,
            isbn=self.isbn,
            url=self.url,
            pdf_path=self.pdf_path,
            thumbnail_path=self.thumbnail_path,
            legacy_id=self.legacy_id,
            status=PublicationStatus.parse(self.status),
            display_order=self.display_order,
        )


class ContactIn(_Base):
    id: UUID | None = None
    kind: str = Field(min_length=1)
    value: str = Field(min_length=1)
    status: str = "draft"
    display_order: int = 0

    def to_domain(self) -> Contact:
        return Contact(
            kind=self.kind,
            value=self.value,
            id=self.id,
            status=PublicationStatus.parse(self.status),
            display_order=self.display_order,
        )


class ProfileIn(_Base):
    id: UUID | None = None
    name: str = Field(min_length=1)
    headline: LocalizedField
    bio: LocalizedField
    photo_path: str | None = None
    professional_photo_path: str | None = None
    status: str = "published"

    def to_domain(self) -> Profile:
        return Profile(
            name=self.name,
            headline=_text(self.headline),
            bio=_text(self.bio),
            id=self.id,
            photo_path=self.photo_path,
            professional_photo_path=self.professional_photo_path,
            status=PublicationStatus.parse(self.status),
        )


class AreaPatchIn(_Base):
    """Edicion parcial de un area. No hay `AreaIn` de alta: las areas no se crean.

    `key` se acepta para poder devolver un error explicito si el panel intenta
    cambiarla, en vez de ignorar el campo en silencio.
    """

    key: str | None = None
    name: dict[str, str] | None = None
    blurb: dict[str, str] | None = None
    display_order: int | None = None
    status: str | None = None

    def to_command(self, area_id: UUID) -> UpdateAreaCommand:
        return UpdateAreaCommand(
            area_id=area_id,
            name=_text(self.name) if self.name else None,
            blurb=_opt_text(self.blurb),
            display_order=self.display_order,
            status=PublicationStatus.parse(self.status) if self.status else None,
            key=AreaKey(self.key) if self.key else None,
        )


class SubareaIn(_Base):
    id: UUID | None = None
    area: str
    area_id: UUID | None = None
    key: str
    name: LocalizedField
    display_order: int = 0

    def to_domain(self) -> Subarea:
        return Subarea(
            key=SubareaKey(self.key),
            name=_text(self.name),
            area_key=AreaKey(self.area),
            id=self.id,
            area_id=self.area_id,
            display_order=self.display_order,
        )


class MessageIn(_Base):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    subject: str | None = Field(default=None, max_length=300)
    body: str = Field(min_length=1, max_length=5000)


class ReorderIn(_Base):
    ids: list[UUID] = Field(min_length=1)


class UploadUrlIn(_Base):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=120)


class RevalidateIn(_Base):
    paths: list[str] | None = None


# Modelo de entrada por recurso, usado por el router generico de /admin.
BY_RESOURCE: dict[str, type[_Base]] = {
    "projects": ProjectIn,
    "experiences": ExperienceIn,
    "certifications": CertificationIn,
    "education": EducationIn,
    "publications": PublicationIn,
    "contacts": ContactIn,
}


def parse_resource(resource: str, payload: dict[str, Any]) -> Any:
    model = BY_RESOURCE[resource]
    return model.model_validate(payload).to_domain()  # type: ignore[attr-defined]


# Forma canonica de fila por recurso. La usa el PATCH parcial de /admin: se parte de
# la fila actual y se le superpone lo que manda el panel, de modo que enviar un solo
# campo no borra el resto.
TO_ROW_BY_RESOURCE: dict[str, Any] = {
    "projects": ser.project_to_row,
    "experiences": ser.experience_to_row,
    "certifications": ser.certification_to_row,
    "education": ser.education_to_row,
    "publications": ser.publication_to_row,
    "contacts": ser.contact_to_row,
}
