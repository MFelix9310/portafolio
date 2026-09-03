"""Entidades -> JSON de respuesta.

Dos decisiones de presentacion viven aqui y en ningun otro sitio:

1. **Locale.** Con `?locale=en` cada campo bilingue sale resuelto (con fallback a
   `es`); sin locale sale el mapa completo, que es lo que el panel necesita para
   editar los dos idiomas. El fallback lo implementa `LocalizedText.resolve`.
2. **Rutas de media.** Cada `*_path` se emite verbatim, con el prefijo del bucket
   (addendum A4), y se acompana de su `*_url` publica compuesta con la misma
   convencion. Como la ruta es identica en los dos adaptadores, la URL tambien lo es:
   cambiar `PERSISTENCE_BACKEND` no mueve una sola URL del frontend.
"""

from __future__ import annotations

from typing import Any

from ....application.dto.catalog import AreaOverview, CatalogView
from ....application.ports.media_storage import UploadTicket
from ....domain.entities.certification import Certification
from ....domain.entities.contact import Contact
from ....domain.entities.education import Education
from ....domain.entities.experience import Experience
from ....domain.entities.media import MediaAsset
from ....domain.entities.message import Message
from ....domain.entities.profile import Profile
from ....domain.entities.project import Project
from ....domain.entities.publication import Publication
from ....domain.entities.taxonomy import Subarea
from ....domain.value_objects.localized_text import LocalizedText
from ....domain.value_objects.storage_path import public_url_of


def text(value: LocalizedText | None, locale: str | None) -> Any:
    if value is None:
        return None
    return value.resolve(locale) if locale else value.to_dict()


def _raw_text(value: dict[str, str] | None, locale: str | None) -> Any:
    """Igual que `text` pero partiendo de un mapa ya serializado (DTO de areas)."""
    if value is None:
        return None
    if not locale:
        return value
    return LocalizedText(value).resolve(locale)


def _url(path: str | None, base_url: str) -> str | None:
    return public_url_of(path, base_url)


def media_asset(asset: MediaAsset, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(asset.id) if asset.id else None,
        "project_id": str(asset.project_id) if asset.project_id else None,
        "kind": asset.kind.value,
        "storage_path": asset.storage_path,
        "storage_url": _url(asset.storage_path, base_url),
        "poster_path": asset.poster_path,
        "poster_url": _url(asset.poster_path, base_url),
        "caption": text(asset.caption, locale),
        "title": text(asset.title, locale),
        "duration_seconds": asset.duration_seconds,
        "width": asset.width,
        "height": asset.height,
        "renditions": {
            r.label: {"path": r.path, "url": _url(r.path, base_url), "bytes": r.bytes}
            for r in asset.renditions
        },
        "display_order": asset.display_order,
    }


def project(item: Project, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "slug": item.slug.value,
        "title": text(item.title, locale),
        "summary": text(item.summary, locale),
        # A7: `body` es nullable y el seed no lo escribe; puede venir vacio siempre.
        "body": text(item.body, locale),
        "technologies": list(item.technologies),
        "project_url": item.project_url,
        "repository_url": item.repository_url,
        "thumbnail_path": item.thumbnail_path,
        "thumbnail_url": _url(item.thumbnail_path, base_url),
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
        "taxonomy": [
            {"area": tag.area.value, "subarea": tag.subarea.value} for tag in item.taxonomy
        ],
        "media": [media_asset(asset, locale, base_url) for asset in item.media],
    }


def experience(item: Experience, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "slug": item.slug.value,
        "company": text(item.company, locale),
        "position": text(item.position, locale),
        "description": text(item.description, locale),
        "keywords": list(item.keywords),
        "company_logo_path": item.company_logo_path,
        "company_logo_url": _url(item.company_logo_path, base_url),
        "thumbnail_path": item.thumbnail_path,
        "thumbnail_url": _url(item.thumbnail_path, base_url),
        "start_date": item.start_date.isoformat(),
        "end_date": item.end_date.isoformat() if item.end_date else None,
        "is_current": item.is_current,
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def certification(item: Certification, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "slug": item.slug.value,
        "name": text(item.name, locale),
        "issuer": text(item.issuer, locale),
        "description": text(item.description, locale),
        "issued_on": item.issued_on.isoformat(),
        "expires_on": item.expires_on.isoformat() if item.expires_on else None,
        "credential_url": item.credential_url,
        "certificate_path": item.certificate_path,
        "certificate_url": _url(item.certificate_path, base_url),
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def education(item: Education, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "institution": text(item.institution, locale),
        "title": text(item.title, locale),
        "description": text(item.description, locale),
        "graduation_year": item.graduation_year,
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def publication(item: Publication, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "slug": item.slug.value,
        "kind": item.kind,
        "title": text(item.title, locale),
        "authors": text(item.authors, locale),
        "venue": text(item.venue, locale),
        "abstract": text(item.abstract, locale),
        "published_on": item.published_on.isoformat() if item.published_on else None,
        "doi": item.doi,
        "isbn": item.isbn,
        "url": item.url,
        "pdf_path": item.pdf_path,
        "pdf_url": _url(item.pdf_path, base_url),
        "thumbnail_path": item.thumbnail_path,
        "thumbnail_url": _url(item.thumbnail_path, base_url),
        "legacy_id": item.legacy_id,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def contact(item: Contact, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "kind": item.kind,
        "value": item.value,
        "status": item.status.value,
        "display_order": item.display_order,
    }


def profile(
    item: Profile | None, locale: str | None, base_url: str = ""
) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        "id": str(item.id) if item.id else None,
        "name": item.name,
        "headline": text(item.headline, locale),
        "bio": text(item.bio, locale),
        "photo_path": item.photo_path,
        "photo_url": _url(item.photo_path, base_url),
        "professional_photo_path": item.professional_photo_path,
        "professional_photo_url": _url(item.professional_photo_path, base_url),
        "status": item.status.value,
    }


def subarea(item: Subarea, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "area": item.area_key.value,
        "key": item.key.value,
        "name": text(item.name, locale),
        "display_order": item.display_order,
    }


def area_overview(item: AreaOverview, locale: str | None, base_url: str = "") -> dict[str, Any]:
    return {
        "id": item.id,
        "key": item.key,
        "name": _raw_text(item.name, locale),
        "blurb": _raw_text(item.blurb, locale),
        "display_order": item.display_order,
        "status": item.status,
        "project_count": item.project_count,
        "subareas": [
            {
                "key": sub.key,
                "name": _raw_text(sub.name, locale),
                "display_order": sub.display_order,
                "project_count": sub.project_count,
            }
            for sub in item.subareas
        ],
    }


def message(item: Message) -> dict[str, Any]:
    return {
        "id": str(item.id) if item.id else None,
        "name": item.name,
        "email": item.email,
        "subject": item.subject,
        "body": item.body,
        "read": item.read,
        "created_at": item.created_at.isoformat(),
    }


def upload_ticket(ticket: UploadTicket) -> dict[str, Any]:
    return {
        "upload_url": ticket.upload_url,
        "storage_path": ticket.storage_path,
        "public_url": ticket.public_url,
        "expires_at": ticket.expires_at.isoformat(),
        "token": ticket.token,
    }


def catalog(view: CatalogView, base_url: str = "") -> dict[str, Any]:
    locale = view.locale
    return {
        "locale": locale,
        "media_base_url": base_url,
        "profile": profile(view.profile, locale, base_url),
        "areas": [area_overview(item, locale, base_url) for item in view.areas],
        "projects": [project(item, locale, base_url) for item in view.projects],
        "experiences": [experience(item, locale, base_url) for item in view.experiences],
        "certifications": [
            certification(item, locale, base_url) for item in view.certifications
        ],
        "education": [education(item, locale, base_url) for item in view.education],
        "publications": [publication(item, locale, base_url) for item in view.publications],
        "contacts": [contact(item, locale, base_url) for item in view.contacts],
    }


# Registro usado por el router generico de /admin.
BY_RESOURCE: dict[str, Any] = {
    "projects": project,
    "experiences": experience,
    "certifications": certification,
    "education": education,
    "publications": publication,
    "contacts": contact,
}
