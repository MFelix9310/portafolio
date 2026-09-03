"""Traduce `content/catalog.seed.json` (forma heredada) a filas canonicas.

El seed viene del sitio Django anterior: campos con sufijo `_en`, rutas sin sufijo
`_path`, media repartida en `images` / `videos` / `documents`. Aqui se normaliza a la
forma del contrato una sola vez, en el arranque.

Los ids se derivan con uuid5 sobre el recurso y su clave natural: sin base de datos
no hay `gen_random_uuid()`, y unos ids estables permiten que un PATCH del panel
sobreviva a un reinicio.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable
from uuid import NAMESPACE_URL, UUID, uuid5

from ....domain.value_objects.taxonomy_keys import SEED_SUBAREA_KEYS
from .media_manifest import MediaManifest

_NAMESPACE = uuid5(NAMESPACE_URL, "https://felixruiz.dev/portafolio")


def stable_id(resource: str, natural_key: str) -> UUID:
    return uuid5(_NAMESPACE, f"{resource}:{natural_key}")


def _localized(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    cleaned = {k: v for k, v in value.items() if isinstance(v, str) and v.strip()}
    return cleaned or None


def _media_rows(
    project_key: str, payload: dict[str, Any], manifest: MediaManifest
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = (("image", "images"), ("video", "videos"), ("document", "documents"))
    for kind, seed_key in groups:
        for index, item in enumerate(payload.get(seed_key) or []):
            legacy_path = item["path"]
            entry = manifest.entry(legacy_path)
            # El id se deriva de la ruta heredada, no de la final: sobrevive a un
            # recodificado que cambie el nombre del fichero en el bucket.
            rows.append(
                {
                    "id": str(stable_id("media", f"{project_key}:{legacy_path}")),
                    "project_id": str(stable_id("project", project_key)),
                    "kind": entry.kind if entry else kind,
                    "storage_path": entry.storage_path if entry else legacy_path,
                    "poster_path": entry.poster_path if entry else item.get("poster"),
                    "caption": _localized({"es": item["caption"]})
                    if item.get("caption")
                    else None,
                    "title": _localized({"es": item["title"]}) if item.get("title") else None,
                    "duration_seconds": entry.duration_seconds if entry else None,
                    "width": entry.width if entry else None,
                    "height": entry.height if entry else None,
                    "renditions": dict(entry.renditions) if entry else {},
                    "display_order": item.get("order", index),
                }
            )
    return rows


def _project_row(payload: dict[str, Any], manifest: MediaManifest) -> dict[str, Any]:
    slug = payload["slug"]
    return {
        "id": str(stable_id("project", slug)),
        "slug": slug,
        "title": _localized(payload.get("title")),
        "summary": _localized(payload.get("summary")),
        "body": _localized(payload.get("body")),
        "technologies": payload.get("technologies") or [],
        "project_url": payload.get("project_url"),
        "repository_url": payload.get("repository_url"),
        "thumbnail_path": manifest.path(payload.get("thumbnail")),
        "legacy_id": payload.get("legacy_id"),
        "status": payload.get("status", "draft"),
        "display_order": payload.get("display_order", 0),
        "taxonomy": [
            {"area": tag["area"], "subarea": tag["subarea"]}
            for tag in payload.get("taxonomy") or []
        ],
        "media": _media_rows(slug, payload, manifest),
    }


def _experience_row(payload: dict[str, Any], manifest: MediaManifest) -> dict[str, Any]:
    return {
        "id": str(stable_id("experience", payload["slug"])),
        "slug": payload["slug"],
        "company": _localized(payload.get("company")),
        "position": _localized(payload.get("position")),
        "description": _localized(payload.get("description")),
        "keywords": payload.get("keywords") or [],
        "company_logo_path": manifest.path(payload.get("company_logo")),
        "thumbnail_path": manifest.path(payload.get("thumbnail")),
        "legacy_id": payload.get("legacy_id"),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "is_current": payload.get("is_current", False),
        "status": payload.get("status", "draft"),
        "display_order": payload.get("display_order", 0),
    }


def _certification_row(
    payload: dict[str, Any], manifest: MediaManifest
) -> dict[str, Any]:
    return {
        "id": str(stable_id("certification", payload["slug"])),
        "slug": payload["slug"],
        "name": _localized(payload.get("name")),
        "issuer": _localized(payload.get("issuer")),
        "description": _localized(payload.get("description")),
        "issued_on": payload.get("issued_on"),
        "expires_on": payload.get("expires_on"),
        "credential_url": payload.get("credential_url"),
        "certificate_path": manifest.path(payload.get("certificate_file")),
        "legacy_id": payload.get("legacy_id"),
        "status": payload.get("status", "draft"),
        "display_order": payload.get("display_order", 0),
    }


def _education_row(payload: dict[str, Any], index: int) -> dict[str, Any]:
    natural = str(payload.get("legacy_id") or index)
    return {
        "id": str(stable_id("education", natural)),
        "institution": _localized(payload.get("institution")),
        "title": _localized(payload.get("title")),
        "description": _localized(payload.get("description")),
        "graduation_year": payload.get("graduation_year"),
        "legacy_id": payload.get("legacy_id"),
        "status": payload.get("status", "draft"),
        "display_order": payload.get("display_order", 0),
    }


def _publication_row(
    payload: dict[str, Any], manifest: MediaManifest
) -> dict[str, Any]:
    return {
        "id": str(stable_id("publication", payload["slug"])),
        "slug": payload["slug"],
        "kind": payload.get("kind") or "article",
        "title": _localized(payload.get("title")),
        "authors": _localized(payload.get("authors")),
        "venue": _localized(payload.get("venue")),
        "abstract": _localized(payload.get("abstract")),
        "published_on": payload.get("published_on"),
        "doi": payload.get("doi"),
        "isbn": payload.get("isbn"),
        "url": payload.get("url"),
        "pdf_path": manifest.path(payload.get("pdf_file")),
        "thumbnail_path": manifest.path(payload.get("thumbnail")),
        "legacy_id": payload.get("legacy_id"),
        "status": payload.get("status", "draft"),
        "display_order": payload.get("display_order", 0),
    }


def _contact_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(stable_id("contact", payload["kind"])),
        "kind": payload["kind"],
        "value": payload["value"],
        "status": payload.get("status", "draft"),
        "display_order": payload.get("display_order", 0),
    }


def _profile_row(payload: dict[str, Any], manifest: MediaManifest) -> dict[str, Any]:
    return {
        "id": str(stable_id("profile", "singleton")),
        "name": payload.get("name", "Felix Ruiz M."),
        # El seed llama `legacy_title` a lo que el contrato llama `headline`.
        "headline": _localized(payload.get("legacy_title")) or {"es": ""},
        "bio": _localized(payload.get("bio")) or {"es": ""},
        "photo_path": manifest.path(payload.get("photo")),
        "professional_photo_path": manifest.path(payload.get("professional_photo")),
        "status": "published",
    }


def _taxonomy_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Areas y subareas de la semilla del contrato; el seed de contenido no las trae."""
    areas: list[dict[str, Any]] = []
    subareas: list[dict[str, Any]] = []
    for order, (area_key, subarea_keys) in enumerate(SEED_SUBAREA_KEYS.items()):
        area_id = str(stable_id("area", area_key))
        areas.append(
            {
                "id": area_id,
                "key": area_key,
                "name": {"es": area_key.replace("-", " ").title()},
                "blurb": None,
                "display_order": order,
                "status": "published",
            }
        )
        for index, subarea_key in enumerate(subarea_keys):
            subareas.append(
                {
                    "id": str(stable_id("subarea", f"{area_key}:{subarea_key}")),
                    "area_id": area_id,
                    "area_key": area_key,
                    "key": subarea_key,
                    "name": {"es": subarea_key.title()},
                    "display_order": index,
                }
            )
    return areas, subareas


def _normalize_headline(profile: dict[str, Any]) -> dict[str, Any]:
    if not profile["headline"].get("es"):
        profile["headline"] = {"es": profile["name"]}
    if not profile["bio"].get("es"):
        profile["bio"] = {"es": profile["name"]}
    return profile


def load_seed(path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Devuelve el catalogo completo en filas canonicas, listo para el store."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    manifest = MediaManifest.load(manifest_path)
    areas, subareas = _taxonomy_rows()
    return {
        "profile": _normalize_headline(
            _profile_row(payload.get("profile") or {}, manifest)
        ),
        "areas": areas,
        "subareas": subareas,
        "projects": [_project_row(item, manifest) for item in payload.get("projects", [])],
        "experiences": [
            _experience_row(item, manifest) for item in payload.get("experiences", [])
        ],
        "certifications": [
            _certification_row(item, manifest)
            for item in payload.get("certifications", [])
        ],
        "education": [
            _education_row(item, index)
            for index, item in enumerate(payload.get("education", []))
        ],
        "publications": [
            _publication_row(item, manifest) for item in payload.get("publications", [])
        ],
        "contacts": [_contact_row(item) for item in payload.get("contacts", [])],
        "messages": [],
    }


def empty_catalog() -> dict[str, Any]:
    """Catalogo vacio con la taxonomia sembrada; util cuando no hay seed a mano."""
    areas, subareas = _taxonomy_rows()
    return {
        "profile": None,
        "areas": areas,
        "subareas": subareas,
        "projects": [],
        "experiences": [],
        "certifications": [],
        "education": [],
        "publications": [],
        "contacts": [],
        "messages": [],
    }


COLLECTIONS: tuple[str, ...] = (
    "areas",
    "subareas",
    "projects",
    "experiences",
    "certifications",
    "education",
    "publications",
    "contacts",
    "messages",
)


def iter_media(catalog: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for project in catalog.get("projects", []):
        yield from project.get("media", [])
