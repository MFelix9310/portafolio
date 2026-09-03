"""Exporta el contenido real del portafolio Django antiguo a un seed JSON.

Se genera desde `db.sqlite3` en vez de transcribirlo a mano: el criterio de
aceptacion es que ningun dato real se pierda, y copiar 6 proyectos con sus
fechas, URLs y media a mano es exactamente como se pierden.

Dos correcciones deliberadas sobre el origen, ambas registradas en la salida:

* `education` filas 2 y 6 tienen `institution` y `title` intercambiados en la
  base antigua (el campo institucion contiene el nombre del master). Se
  reordena; el valor original queda en `_source`.
* `Project.skills` es un string plano con solo tres valores posibles
  (`data_scientist`, `data_analyst`, `python_developer`). Se traduce a la
  taxonomia nueva area/subarea segun PROJECT_TAXONOMY.
"""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from pathlib import Path

LEGACY_DB = Path("C:/tmp/portfolio-research/PORTFOLIO_WEB/db.sqlite3")
OUTPUT = Path(__file__).resolve().parent.parent / "content" / "catalog.seed.json"

# El tag antiguo `python_developer` significaba dos cosas distintas: "es una
# aplicacion que construi" y "esta escrito en Python". Solo la primera es una
# entrega de developer, asi que se asigna por proyecto y no por regla ciega.
PROJECT_TAXONOMY = {
    1: [("developer", "backend")],
    2: [("developer", "fullstack"), ("data", "analyst")],
    3: [("data", "scientist"), ("data", "analyst")],
    4: [("data", "scientist"), ("developer", "backend")],
    5: [("data", "scientist"), ("data", "analyst")],
    6: [("data", "scientist"), ("data", "analyst"), ("developer", "backend")],
}

# Filas de `education` cuyo institution/title estan invertidos en el origen.
EDUCATION_SWAPPED = {2, 6}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    ascii_only = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    slug = "".join(c if c.isalnum() else "-" for c in ascii_only.lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:80]


def localized(es: str | None, en: str | None) -> dict[str, str]:
    """ES obligatorio, EN opcional. Sin EN no se inventa: se omite la clave."""
    value = {"es": es or ""}
    if en and en.strip() and en.strip() != (es or "").strip():
        value["en"] = en.strip()
    return value


def split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    conn = sqlite3.connect(LEGACY_DB)
    conn.row_factory = sqlite3.Row

    def q(sql: str) -> list[dict]:
        return [dict(r) for r in conn.execute(sql)]

    images: dict[int, list[dict]] = {}
    for row in q('select * from portfolio_projectimage order by project_id, "order"'):
        images.setdefault(row["project_id"], []).append(
            {"path": row["image"], "caption": row["caption"] or None, "order": row["order"]}
        )

    videos: dict[int, list[dict]] = {}
    for row in q('select * from portfolio_projectvideo order by project_id, "order"'):
        videos.setdefault(row["project_id"], []).append(
            {"path": row["video"], "caption": row["caption"] or None, "order": row["order"]}
        )

    documents: dict[int, list[dict]] = {}
    for row in q('select * from portfolio_projectdocument order by project_id, "order"'):
        documents.setdefault(row["project_id"], []).append(
            {"path": row["document"], "title": row["title"], "order": row["order"]}
        )

    projects = []
    for row in q("select * from portfolio_project order by id"):
        pid = row["id"]
        projects.append(
            {
                "legacy_id": pid,
                "slug": slugify(row["title"]),
                "title": localized(row["title"], row["title_en"]),
                "summary": localized(row["description"], row["description_en"]),
                "technologies": split_list(row["technologies"]),
                "technologies_en": split_list(row["technologies_en"]),
                "project_url": row["project_url"],
                "repository_url": row["github_url"],
                "thumbnail": row["thumbnail"],
                "created_at": row["created_at"],
                "display_order": row["order"],
                "status": "published" if row["is_active"] else "draft",
                "legacy_skills": split_list(row["skills"]),
                "taxonomy": [
                    {"area": area, "subarea": subarea}
                    for area, subarea in PROJECT_TAXONOMY.get(pid, [])
                ],
                "images": images.get(pid, []),
                "videos": videos.get(pid, []),
                "documents": documents.get(pid, []),
            }
        )

    experiences = [
        {
            "legacy_id": row["id"],
            "slug": slugify(f"{row['position']}-{row['company']}"),
            "company": localized(row["company"], row["company_en"]),
            "position": localized(row["position"], row["position_en"]),
            "description": localized(row["description"], row["description_en"]),
            "keywords": split_list(row["keywords"]),
            "keywords_en": split_list(row["keywords_en"]),
            "company_logo": row["company_logo"],
            "thumbnail": row["thumbnail"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "is_current": bool(row["current_job"]),
            "display_order": row["order"],
            "status": "published" if row["is_active"] else "draft",
        }
        for row in q("select * from portfolio_workexperience order by id")
    ]

    certifications = [
        {
            "legacy_id": row["id"],
            "slug": slugify(row["name"]),
            "name": localized(row["name"], row["name_en"]),
            "issuer": localized(row["institution"], row["institution_en"]),
            "description": localized(row["description"], row["description_en"]),
            "issued_on": row["date_obtained"],
            "expires_on": row["expiry_date"],
            "credential_url": row["credential_url"],
            "certificate_file": row["certificate_file"],
            "display_order": row["order"],
            "status": "published" if row["is_active"] else "draft",
        }
        for row in q("select * from portfolio_certification order by id")
    ]

    education = []
    for row in q("select * from portfolio_education order by id"):
        institution, title = row["institution"], row["title"]
        entry: dict = {}
        if row["id"] in EDUCATION_SWAPPED:
            entry["_source"] = {"institution": institution, "title": title}
            entry["_correction"] = "institution/title invertidos en la base antigua"
            institution, title = title, institution
        education.append(
            {
                "legacy_id": row["id"],
                "institution": localized(institution, None),
                "title": localized(title, row["title_en"]),
                "description": localized(row["description"], row["description_en"]),
                "graduation_year": row["graduation_year"],
                "display_order": row["order"],
                "status": "published" if row["is_active"] else "draft",
                **entry,
            }
        )

    publications = [
        {
            "legacy_id": row["id"],
            "slug": slugify(row["title"]),
            "kind": row["type"],
            "title": localized(row["title"], row["title_en"]),
            "authors": localized(row["authors"], row["authors_en"]),
            "venue": localized(row["journal_or_publisher"], row["journal_or_publisher_en"]),
            "abstract": localized(row["abstract"], row["abstract_en"]),
            "published_on": row["publication_date"],
            "doi": row["doi"],
            "isbn": row["isbn"],
            "url": row["url"],
            "pdf_file": row["pdf_file"],
            "thumbnail": row["thumbnail"],
            "display_order": row["order"],
            "status": "published" if row["is_active"] else "draft",
        }
        for row in q("select * from portfolio_publication order by id")
    ]

    contacts = [
        {
            "kind": row["type"],
            "value": row["value"],
            "display_order": row["order"],
            "status": "published" if row["is_active"] else "draft",
        }
        for row in q("select * from portfolio_contact order by id")
    ]

    profile_row = q("select * from portfolio_profile limit 1")[0]
    profile = {
        "name": profile_row["name"],
        "legacy_title": localized(profile_row["title"], profile_row["title_en"]),
        "bio": localized(profile_row["bio"], profile_row["bio_en"]),
        "photo": profile_row["photo"],
        "professional_photo": profile_row["professional_photo"],
    }

    seed = {
        "_generated_by": "tools/export_legacy_content.py",
        "_source": str(LEGACY_DB),
        "profile": profile,
        "projects": projects,
        "experiences": experiences,
        "certifications": certifications,
        "education": education,
        "publications": publications,
        "contacts": contacts,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = {k: len(v) for k, v in seed.items() if isinstance(v, list)}
    print(f"escrito {OUTPUT}")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
