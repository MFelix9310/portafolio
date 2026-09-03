"""Traduccion entre entidades de dominio y filas planas.

La forma de la fila es la del contrato de datos: `jsonb` por locale, fechas ISO,
`status` textual. Los dos adaptadores (JSON local y Supabase) hablan este mismo
dialecto, asi que el mapeo se escribe una sola vez.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Mapping
from uuid import UUID

from ...domain.entities.certification import Certification
from ...domain.entities.contact import Contact
from ...domain.entities.education import Education
from ...domain.entities.experience import Experience
from ...domain.entities.media import MediaAsset, MediaKind, Rendition
from ...domain.entities.message import Message
from ...domain.entities.profile import Profile
from ...domain.entities.project import Project
from ...domain.entities.publication import Publication
from ...domain.entities.taxonomy import Area, Subarea
from ...domain.value_objects.date_range import DateRange
from ...domain.value_objects.localized_text import LocalizedText
from ...domain.value_objects.publication_status import PublicationStatus
from ...domain.value_objects.slug import Slug
from ...domain.value_objects.taxonomy_keys import AreaKey, SubareaKey, TaxonomyTag

Row = Mapping[str, Any]


# --------------------------------------------------------------------------- helpers


def _uuid(value: Any) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value
    return UUID(str(value))


def _text(value: Any) -> LocalizedText:
    return LocalizedText(dict(value or {}))


def _opt_text(value: Any) -> LocalizedText | None:
    """Texto localizado opcional: sin un `es` con contenido es None, no un error.

    Un pie de foto vacio o solo en ingles no puede tumbar el listado entero.
    Tambien desenvuelve {"es": {"es": ...}}, que dejo una version anterior del
    cargador en la base.
    """
    if not isinstance(value, dict):
        return None
    inner = value.get("es")
    if isinstance(inner, dict):
        value = inner
    limpio = {k: v.strip() for k, v in value.items() if isinstance(v, str) and v.strip()}
    return LocalizedText.optional(limpio) if limpio.get("es") else None


def _date(value: Any) -> date | None:
    if value is None or isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _str_id(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in (value or []))


# ------------------------------------------------------------------------ taxonomia


def area_from_row(row: Row, subareas: tuple[Subarea, ...] = ()) -> Area:
    return Area(
        key=AreaKey(row["key"]),
        name=_text(row.get("name")),
        id=_uuid(row.get("id")),
        blurb=_opt_text(row.get("blurb")),
        display_order=int(row.get("display_order", 0)),
        status=PublicationStatus.parse(row.get("status") or "published"),
        subareas=subareas,
    )


def area_to_row(area: Area) -> dict[str, Any]:
    return {
        "id": _str_id(area.id),
        "key": area.key.value,
        "name": area.name.to_dict(),
        "blurb": area.blurb.to_dict() if area.blurb else None,
        "display_order": area.display_order,
        "status": area.status.value,
    }


def subarea_from_row(row: Row, area_key: str) -> Subarea:
    return Subarea(
        key=SubareaKey(row["key"]),
        name=_text(row.get("name")),
        area_key=AreaKey(area_key),
        id=_uuid(row.get("id")),
        area_id=_uuid(row.get("area_id")),
        display_order=int(row.get("display_order", 0)),
    )


def subarea_to_row(subarea: Subarea) -> dict[str, Any]:
    return {
        "id": _str_id(subarea.id),
        "area_id": _str_id(subarea.area_id),
        "area_key": subarea.area_key.value,
        "key": subarea.key.value,
        "name": subarea.name.to_dict(),
        "display_order": subarea.display_order,
    }


# ---------------------------------------------------------------------------- media


def media_from_row(row: Row) -> MediaAsset:
    # `path` es la clave del contrato; `storagePath` la escribio una version
    # anterior del cargador. Se aceptan ambas para que una fila vieja no tumbe
    # el listado entero, y se ignora la rendition que no trae ninguna.
    renditions = tuple(
        Rendition(
            label=label,
            path=payload.get("path") or payload.get("storagePath"),
            bytes=int(payload.get("bytes") or 0),
        )
        for label, payload in sorted((row.get("renditions") or {}).items())
        if isinstance(payload, dict) and (payload.get("path") or payload.get("storagePath"))
    )
    return MediaAsset(
        kind=MediaKind.parse(row["kind"]),
        storage_path=row["storage_path"],
        id=_uuid(row.get("id")),
        project_id=_uuid(row.get("project_id")),
        poster_path=row.get("poster_path"),
        caption=_opt_text(row.get("caption")),
        title=_opt_text(row.get("title")),
        duration_seconds=(
            float(row["duration_seconds"])
            if row.get("duration_seconds") is not None
            else None
        ),
        width=row.get("width"),
        height=row.get("height"),
        renditions=renditions,
        display_order=int(row.get("display_order", 0)),
    )


def media_to_row(asset: MediaAsset) -> dict[str, Any]:
    return {
        "id": _str_id(asset.id),
        "project_id": _str_id(asset.project_id),
        "kind": asset.kind.value,
        "storage_path": asset.storage_path,
        "poster_path": asset.poster_path,
        "caption": asset.caption.to_dict() if asset.caption else None,
        "title": asset.title.to_dict() if asset.title else None,
        "duration_seconds": asset.duration_seconds,
        "width": asset.width,
        "height": asset.height,
        "renditions": {r.label: {"path": r.path, "bytes": r.bytes} for r in asset.renditions},
        "display_order": asset.display_order,
    }


# -------------------------------------------------------------------------- project


def project_from_row(row: Row) -> Project:
    taxonomy = tuple(
        TaxonomyTag.of(tag["area"], tag["subarea"]) for tag in (row.get("taxonomy") or [])
    )
    media = tuple(media_from_row(item) for item in (row.get("media") or []))
    return Project(
        slug=Slug(row["slug"]),
        title=_text(row.get("title")),
        id=_uuid(row.get("id")),
        summary=_opt_text(row.get("summary")),
        body=_opt_text(row.get("body")),
        technologies=_tuple(row.get("technologies")),
        project_url=row.get("project_url"),
        repository_url=row.get("repository_url"),
        thumbnail_path=row.get("thumbnail_path"),
        legacy_id=row.get("legacy_id"),
        status=PublicationStatus.parse(row.get("status")),
        display_order=int(row.get("display_order", 0)),
        taxonomy=taxonomy,
        media=media,
    )


def project_to_row(project: Project, *, embed: bool = True) -> dict[str, Any]:
    """`embed=False` deja fuera taxonomy y media: son tablas aparte en Postgres."""
    row: dict[str, Any] = {
        "id": _str_id(project.id),
        "slug": project.slug.value,
        "title": project.title.to_dict(),
        "summary": project.summary.to_dict() if project.summary else None,
        "body": project.body.to_dict() if project.body else None,
        "technologies": list(project.technologies),
        "project_url": project.project_url,
        "repository_url": project.repository_url,
        "thumbnail_path": project.thumbnail_path,
        "legacy_id": project.legacy_id,
        "status": project.status.value,
        "display_order": project.display_order,
    }
    if embed:
        row["taxonomy"] = [
            {"area": tag.area.value, "subarea": tag.subarea.value} for tag in project.taxonomy
        ]
        row["media"] = [media_to_row(asset) for asset in project.media]
    return row


# ------------------------------------------------------------------- otros recursos


def experience_from_row(row: Row) -> Experience:
    return Experience(
        slug=Slug(row["slug"]),
        company=_text(row.get("company")),
        position=_text(row.get("position")),
        period=DateRange(_date(row["start_date"]), _date(row.get("end_date"))),
        id=_uuid(row.get("id")),
        description=_opt_text(row.get("description")),
        keywords=_tuple(row.get("keywords")),
        company_logo_path=row.get("company_logo_path"),
        thumbnail_path=row.get("thumbnail_path"),
        legacy_id=row.get("legacy_id"),
        is_current=bool(row.get("is_current", False)),
        status=PublicationStatus.parse(row.get("status")),
        display_order=int(row.get("display_order", 0)),
    )


def experience_to_row(item: Experience) -> dict[str, Any]:
    return {
        "id": _str_id(item.id),
        "slug": item.slug.value,
        "company": item.company.to_dict(),
        "position": item.position.to_dict(),
        "description": item.description.to_dict() if item.description else None,
        "keywords": list(item.keywords),
        "company_logo_path": item.company_logo_path,
        "thumbnail_path": item.thumbnail_path,
        "start_date": _iso(item.start_date),
        "end_date": _iso(item.end_date),
        "is_current": item.is_current,
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def certification_from_row(row: Row) -> Certification:
    return Certification(
        slug=Slug(row["slug"]),
        name=_text(row.get("name")),
        issuer=_text(row.get("issuer")),
        issued_on=_date(row["issued_on"]),
        id=_uuid(row.get("id")),
        description=_opt_text(row.get("description")),
        expires_on=_date(row.get("expires_on")),
        credential_url=row.get("credential_url"),
        certificate_path=row.get("certificate_path"),
        legacy_id=row.get("legacy_id"),
        status=PublicationStatus.parse(row.get("status")),
        display_order=int(row.get("display_order", 0)),
    )


def certification_to_row(item: Certification) -> dict[str, Any]:
    return {
        "id": _str_id(item.id),
        "slug": item.slug.value,
        "name": item.name.to_dict(),
        "issuer": item.issuer.to_dict(),
        "description": item.description.to_dict() if item.description else None,
        "issued_on": _iso(item.issued_on),
        "expires_on": _iso(item.expires_on),
        "credential_url": item.credential_url,
        "certificate_path": item.certificate_path,
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def education_from_row(row: Row) -> Education:
    return Education(
        institution=_text(row.get("institution")),
        title=_text(row.get("title")),
        id=_uuid(row.get("id")),
        description=_opt_text(row.get("description")),
        graduation_year=row.get("graduation_year"),
        legacy_id=row.get("legacy_id"),
        status=PublicationStatus.parse(row.get("status")),
        display_order=int(row.get("display_order", 0)),
    )


def education_to_row(item: Education) -> dict[str, Any]:
    return {
        "id": _str_id(item.id),
        "institution": item.institution.to_dict(),
        "title": item.title.to_dict(),
        "description": item.description.to_dict() if item.description else None,
        "graduation_year": item.graduation_year,
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def publication_from_row(row: Row) -> Publication:
    return Publication(
        slug=Slug(row["slug"]),
        kind=row.get("kind", "article"),
        title=_text(row.get("title")),
        id=_uuid(row.get("id")),
        authors=_opt_text(row.get("authors")),
        venue=_opt_text(row.get("venue")),
        abstract=_opt_text(row.get("abstract")),
        published_on=_date(row.get("published_on")),
        doi=row.get("doi"),
        isbn=row.get("isbn"),
        url=row.get("url"),
        pdf_path=row.get("pdf_path"),
        thumbnail_path=row.get("thumbnail_path"),
        legacy_id=row.get("legacy_id"),
        status=PublicationStatus.parse(row.get("status")),
        display_order=int(row.get("display_order", 0)),
    )


def publication_to_row(item: Publication) -> dict[str, Any]:
    return {
        "id": _str_id(item.id),
        "slug": item.slug.value,
        "kind": item.kind,
        "title": item.title.to_dict(),
        "authors": item.authors.to_dict() if item.authors else None,
        "venue": item.venue.to_dict() if item.venue else None,
        "abstract": item.abstract.to_dict() if item.abstract else None,
        "published_on": _iso(item.published_on),
        "doi": item.doi,
        "isbn": item.isbn,
        "url": item.url,
        "pdf_path": item.pdf_path,
        "thumbnail_path": item.thumbnail_path,
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def contact_from_row(row: Row) -> Contact:
    return Contact(
        kind=row["kind"],
        value=row["value"],
        id=_uuid(row.get("id")),
        status=PublicationStatus.parse(row.get("status")),
        display_order=int(row.get("display_order", 0)),
    )


def contact_to_row(item: Contact) -> dict[str, Any]:
    return {
        "id": _str_id(item.id),
        "kind": item.kind,
        "value": item.value,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def profile_from_row(row: Row) -> Profile:
    return Profile(
        name=row["name"],
        headline=_text(row.get("headline")),
        bio=_text(row.get("bio")),
        id=_uuid(row.get("id")),
        photo_path=row.get("photo_path"),
        professional_photo_path=row.get("professional_photo_path"),
        status=PublicationStatus.parse(row.get("status") or "published"),
    )


def profile_to_row(item: Profile) -> dict[str, Any]:
    return {
        "id": _str_id(item.id),
        "name": item.name,
        "headline": item.headline.to_dict(),
        "bio": item.bio.to_dict(),
        "photo_path": item.photo_path,
        "professional_photo_path": item.professional_photo_path,
        "status": item.status.value,
        # A6: la fila unica se fuerza con una columna booleana con unique check.
        "singleton": True,
    }


def message_from_row(row: Row) -> Message:
    return Message(
        name=row["name"],
        email=row["email"],
        body=row["body"],
        created_at=_datetime(row["created_at"]),
        id=_uuid(row.get("id")),
        subject=row.get("subject"),
        read=bool(row.get("read", False)),
    )


def message_to_row(item: Message) -> dict[str, Any]:
    return {
        "id": _str_id(item.id),
        "name": item.name,
        "email": item.email,
        "subject": item.subject,
        "body": item.body,
        "read": item.read,
        "created_at": _iso(item.created_at),
    }
