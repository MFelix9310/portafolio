"""Carga content/catalog.seed.json en un proyecto Supabase. Idempotente.

El JSON es la fuente de verdad: aqui no se duplica contenido a mano. Las rutas de
media del sitio antiguo se traducen a su destino en Storage usando
content/media-manifest.json; si una ruta no esta en el manifiesto el script falla
en vez de insertar un NULL silencioso.

**No escribe nada por defecto.** Sin `--apply` monta el plan completo en memoria
—sin tocar la red— y lo imprime. Escribir exige el flag explicito.

    python supabase/seed/load_seed.py                    # plan, sin red, sin escribir
    python supabase/seed/load_seed.py --apply            # escribe los datos
    python supabase/seed/load_seed.py --apply --upload   # datos + ficheros a Storage

Variables de entorno (necesarias solo con --apply):

    SUPABASE_URL               https://<ref>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY  service_role del dashboard

La service_role key **nunca** va al navegador: se usa desde esta linea de comandos
y para nada mas. Solo la libreria estandar; no hay dependencias que instalar.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "catalog.seed.json"
MANIFEST = ROOT / "content" / "media-manifest.json"
BUCKET = "media"


class SeedError(RuntimeError):
    """Error de datos o de transporte: paramos antes de dejar contenido a medias."""


# ---------------------------------------------------------------------- media


class MediaMap:
    """Traduce rutas legacy -> destino en Storage, via content/media-manifest.json."""

    def __init__(self, manifest: dict[str, Any]) -> None:
        self.base = ROOT / manifest["_base"]
        self.entries: dict[str, dict[str, Any]] = manifest["entries"]
        self.used: set[str] = set()

    def entry(self, legacy_path: str | None) -> dict[str, Any] | None:
        if not legacy_path:
            return None
        found = self.entries.get(legacy_path)
        if found is None:
            raise SeedError(
                f"La ruta '{legacy_path}' del catalogo no esta en media-manifest.json. "
                "Se perderia contenido: regenera el manifiesto antes de seguir."
            )
        self.used.add(legacy_path)
        return found

    def path(self, legacy_path: str | None) -> str | None:
        """storagePath canonico (para video, la rendition 1080)."""
        found = self.entry(legacy_path)
        return found["storagePath"] if found else None

    def local(self, relative: str) -> Path:
        # El manifiesto se genera en Windows y trae separadores '\'.
        return self.base / Path(relative.replace("\\", "/"))

    def upload_plan(self) -> list[tuple[str, Path]]:
        """(storagePath, fichero local) de todo lo que el catalogo referencia."""
        plan: dict[str, Path] = {}
        for key in sorted(self.used):
            found = self.entries[key]
            if found["kind"] == "video":
                if found.get("posterLocalFile"):
                    plan[found["posterPath"]] = self.local(found["posterLocalFile"])
                for rendition in found.get("renditions", {}).values():
                    plan[rendition["storagePath"]] = self.local(rendition["localFile"])
            else:
                plan[found["storagePath"]] = self.local(found["localFile"])
        return sorted(plan.items())


def renditions_for_db(entry: dict[str, Any]) -> dict[str, Any] | None:
    """renditions sin localFile: la ruta local no significa nada en la base."""
    if entry.get("kind") != "video":
        return None
    # Clave `path`, como fija el contrato A4 y lee el serializador del backend.
    # El manifiesto la llama `storagePath`; copiar ese nombre tal cual dejaba
    # el listado publico en 500 por un KeyError.
    data = {
        quality: {"path": r["storagePath"], "bytes": r["bytes"]}
        for quality, r in entry.get("renditions", {}).items()
    }
    return data or None


# -------------------------------------------------------------------- helpers


def blank_to_none(value: Any) -> Any:
    """El export antiguo usa '' donde deberia haber NULL."""
    return None if value in ("", []) else value


def check_es(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value.get("es"):
        raise SeedError(f"{label}: falta la clave 'es' obligatoria (D5). Valor: {value!r}")
    return value


def localized(text: Any) -> dict[str, str] | None:
    """Texto del export -> jsonb por locale.

    El seed heredado traia pies de foto y titulos como texto plano; el seed
    reconstruido desde el sitio en vivo ya los trae como {"es": ..., "en": ...}.
    Envolver un diccionario otra vez producia {"es": {"es": ...}} y rompia el
    listado publico: 46 pies de foto y 9 titulos llegaron asi a la base.
    """
    if isinstance(text, dict):
        limpio = {k: v.strip() for k, v in text.items() if isinstance(v, str) and v.strip()}
        return limpio if limpio.get("es") else None
    text = blank_to_none(text)
    return {"es": text} if text else None


# ------------------------------------------------------------ plan (sin red)


def build_plan(catalog: dict[str, Any], media: MediaMap) -> dict[str, Any]:
    """Convierte el catalogo en filas listas para PostgREST. No toca la red."""
    profile = catalog["profile"]
    plan: dict[str, Any] = {
        "profile": [
            {
                "singleton": True,
                "name": profile["name"],
                # El export lo llama legacy_title; el contrato, headline.
                "headline": check_es(profile["legacy_title"], "profile.legacy_title"),
                "bio": blank_to_none(profile.get("bio")),
                "photo_path": media.path(profile.get("photo")),
                "professional_photo_path": media.path(profile.get("professional_photo")),
                "status": "published",
            }
        ],
        "projects": [],
        "experiences": [],
        "certifications": [],
        "education": [],
        "publications": [],
        "contacts": [],
    }
    # Indexados por legacy_id del proyecto: su project_id real no se conoce
    # hasta que PostgREST devuelve la fila.
    links: dict[int, list[tuple[str, str]]] = {}
    project_media: dict[int, list[dict[str, Any]]] = {}

    for project in catalog["projects"]:
        legacy_id = project["legacy_id"]
        plan["projects"].append(
            {
                "slug": project["slug"],
                "title": check_es(project["title"], f"projects[{legacy_id}].title"),
                "summary": blank_to_none(project.get("summary")),
                "technologies": project.get("technologies") or [],
                "project_url": blank_to_none(project.get("project_url")),
                "repository_url": blank_to_none(project.get("repository_url")),
                "thumbnail_path": media.path(project.get("thumbnail")),
                "legacy_id": legacy_id,
                "status": project["status"],
                "display_order": project["display_order"],
                # `body` se omite a proposito: no existe en el export y PostgREST
                # solo actualiza las columnas que enviamos, asi que una recarga no
                # pisa lo que Felix escriba desde /admin.
            }
        )
        links[legacy_id] = [(t["area"], t["subarea"]) for t in project["taxonomy"]]
        project_media[legacy_id] = build_media_rows(project, media)

    for row in catalog["experiences"]:
        legacy_id = row["legacy_id"]
        plan["experiences"].append(
            {
                "slug": row["slug"],
                "company": check_es(row["company"], f"experiences[{legacy_id}].company"),
                "position": check_es(row["position"], f"experiences[{legacy_id}].position"),
                "description": blank_to_none(row.get("description")),
                "keywords": row.get("keywords") or [],
                "company_logo_path": media.path(blank_to_none(row.get("company_logo"))),
                "thumbnail_path": media.path(blank_to_none(row.get("thumbnail"))),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "is_current": row.get("is_current", False),
                "legacy_id": legacy_id,
                "status": row["status"],
                "display_order": row["display_order"],
            }
        )

    for row in catalog["certifications"]:
        legacy_id = row["legacy_id"]
        plan["certifications"].append(
            {
                "slug": row["slug"],
                "name": check_es(row["name"], f"certifications[{legacy_id}].name"),
                "issuer": blank_to_none(row.get("issuer")),
                "description": blank_to_none(row.get("description")),
                "issued_on": row.get("issued_on"),
                "expires_on": row.get("expires_on"),
                "credential_url": blank_to_none(row.get("credential_url")),
                "certificate_path": media.path(blank_to_none(row.get("certificate_file"))),
                "legacy_id": legacy_id,
                "status": row["status"],
                "display_order": row["display_order"],
            }
        )

    for row in catalog["education"]:
        legacy_id = row["legacy_id"]
        plan["education"].append(
            {
                "institution": check_es(row["institution"], f"education[{legacy_id}].institution"),
                "title": check_es(row["title"], f"education[{legacy_id}].title"),
                "description": blank_to_none(row.get("description")),
                "graduation_year": row.get("graduation_year"),
                "legacy_id": legacy_id,
                "status": row["status"],
                "display_order": row["display_order"],
            }
        )

    for row in catalog["publications"]:
        legacy_id = row["legacy_id"]
        plan["publications"].append(
            {
                "slug": row["slug"],
                "kind": row["kind"],
                "title": check_es(row["title"], f"publications[{legacy_id}].title"),
                "authors": blank_to_none(row.get("authors")),
                "venue": blank_to_none(row.get("venue")),
                "abstract": blank_to_none(row.get("abstract")),
                "published_on": row.get("published_on"),
                "doi": blank_to_none(row.get("doi")),
                "isbn": blank_to_none(row.get("isbn")),
                "url": blank_to_none(row.get("url")),
                "pdf_path": media.path(blank_to_none(row.get("pdf_file"))),
                "thumbnail_path": media.path(blank_to_none(row.get("thumbnail"))),
                "legacy_id": legacy_id,
                "status": row["status"],
                "display_order": row["display_order"],
            }
        )

    for row in catalog["contacts"]:
        # Sin slug ni legacy_id en el export: la clave natural es (kind, value).
        plan["contacts"].append(
            {
                "kind": row["kind"],
                "value": row["value"],
                "status": row["status"],
                "display_order": row["display_order"],
            }
        )

    plan["_links"] = links
    plan["_media"] = project_media
    return plan


def build_media_rows(project: dict[str, Any], media: MediaMap) -> list[dict[str, Any]]:
    # El export trae order = 0 en todo; se usa la posicion para que el orden de
    # visualizacion sea estable y reproducible en vez de arbitrario.
    rows: list[dict[str, Any]] = []
    for kind, key in (("image", "images"), ("video", "videos"), ("document", "documents")):
        for item in project.get(key, []):
            entry = media.entry(item["path"])
            assert entry is not None  # media.entry solo devuelve None si la ruta es vacia
            rows.append(
                {
                    "kind": kind,
                    "storage_path": entry["storagePath"],
                    "poster_path": entry.get("posterPath"),
                    "caption": localized(item.get("caption")),
                    "title": localized(item.get("title")),
                    "duration_seconds": entry.get("durationSeconds"),
                    "width": entry.get("width"),
                    "height": entry.get("height"),
                    "renditions": renditions_for_db(entry),
                    "display_order": len(rows),
                }
            )
    return rows


def print_plan(plan: dict[str, Any], upload: list[tuple[str, Path]]) -> None:
    print("PLAN (no se ha escrito nada; usa --apply para aplicarlo)\n")
    for table in (
        "profile", "projects", "experiences", "certifications",
        "education", "publications", "contacts",
    ):
        rows = plan[table]
        print(f"  {table:<16} {len(rows):>3} filas")
    print(f"  {'project_subareas':<16} {sum(len(v) for v in plan['_links'].values()):>3} filas")
    print(f"  {'project_media':<16} {sum(len(v) for v in plan['_media'].values()):>3} filas")

    faltan = [str(p) for _, p in upload if not p.is_file()]
    total = sum(p.stat().st_size for _, p in upload if p.is_file())
    print(f"\n  storage/{BUCKET}   {len(upload):>3} ficheros, {total / 1_048_576:.1f} MiB")
    if faltan:
        print(f"  ATENCION: {len(faltan)} ficheros locales no existen:")
        for path in faltan[:10]:
            print(f"    {path}")


# ------------------------------------------------------------------ PostgREST


class Rest:
    def __init__(self, url: str, key: str) -> None:
        self.url = url.rstrip("/")
        self.key = key

    def _request(self, method: str, path: str, body: Any, prefer: str | None) -> Any:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"{self.url}{path}", data=data, method=method, headers=headers
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SeedError(f"{method} {path} -> {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise SeedError(f"{method} {path} -> sin conexion: {exc.reason}") from exc
        return json.loads(raw) if raw else []

    def upsert(self, table: str, rows: list[dict[str, Any]], on_conflict: str) -> list[dict]:
        if not rows:
            return []
        return self._request(
            "POST",
            f"/rest/v1/{table}?on_conflict={on_conflict}",
            rows,
            "resolution=merge-duplicates,return=representation",
        )

    def insert_ignore(self, table: str, rows: list[dict[str, Any]], on_conflict: str) -> None:
        if not rows:
            return
        self._request(
            "POST",
            f"/rest/v1/{table}?on_conflict={on_conflict}",
            rows,
            "resolution=ignore-duplicates,return=minimal",
        )

    def select(self, table: str, query: str) -> list[dict]:
        return self._request("GET", f"/rest/v1/{table}?{query}", None, None)


def apply_plan(rest: Rest, plan: dict[str, Any]) -> None:
    rest.upsert("profile", plan["profile"], "singleton")

    proyectos = rest.upsert("projects", plan["projects"], "legacy_id")
    por_legacy = {row["legacy_id"]: row["id"] for row in proyectos}
    print(f"  projects          {len(proyectos)} filas")

    subareas = resolve_subareas(rest)

    enlaces: list[dict[str, Any]] = []
    for legacy_id, pares in plan["_links"].items():
        for area_key, subarea_key in pares:
            subarea_id = subareas.get((area_key, subarea_key))
            if subarea_id is None:
                raise SeedError(
                    f"La taxonomia '{area_key}/{subarea_key}' no existe en la base. "
                    "Falta aplicar 20260828120200_taxonomia.sql."
                )
            enlaces.append({"project_id": por_legacy[legacy_id], "subarea_id": subarea_id})
    rest.insert_ignore("project_subareas", enlaces, "project_id,subarea_id")
    print(f"  project_subareas  {len(enlaces)} filas")

    medios: list[dict[str, Any]] = []
    for legacy_id, filas in plan["_media"].items():
        for fila in filas:
            medios.append({**fila, "project_id": por_legacy[legacy_id]})
    rest.upsert("project_media", medios, "project_id,storage_path")
    print(f"  project_media     {len(medios)} filas")

    for tabla in ("experiences", "certifications", "education", "publications"):
        rest.upsert(tabla, plan[tabla], "legacy_id")
        print(f"  {tabla:<17} {len(plan[tabla])} filas")

    rest.upsert("contacts", plan["contacts"], "kind,value")
    print(f"  {'contacts':<17} {len(plan['contacts'])} filas")


def resolve_subareas(rest: Rest) -> dict[tuple[str, str], str]:
    areas = {row["id"]: row["key"] for row in rest.select("areas", "select=id,key")}
    return {
        (areas[row["area_id"]], row["key"]): row["id"]
        for row in rest.select("subareas", "select=id,key,area_id")
        if row["area_id"] in areas
    }


# -------------------------------------------------------------------- storage


def upload_media(plan: list[tuple[str, Path]], url: str, key: str) -> None:
    """Sube los ficheros al bucket `media`. Idempotente: x-upsert y salto por tamano."""
    subidos = omitidos = 0
    for storage_path, local_file in plan:
        # storagePath incluye el prefijo del bucket; la API lo lleva en la ruta.
        object_key = storage_path[len(BUCKET) + 1:] if storage_path.startswith(f"{BUCKET}/") else storage_path
        if not local_file.is_file():
            raise SeedError(f"Falta el fichero local {local_file} (para {storage_path}).")
        size = local_file.stat().st_size

        if _remote_size(url, object_key) == size:
            omitidos += 1
            continue

        content_type = mimetypes.guess_type(local_file.name)[0] or "application/octet-stream"
        request = urllib.request.Request(
            f"{url}/storage/v1/object/{BUCKET}/{object_key}",
            data=local_file.read_bytes(),
            method="POST",
            headers={
                # `apikey` es obligatoria con las claves nuevas (`sb_secret_...`),
                # que no son JWT: sin ella Storage intenta parsear el Bearer
                # como JWT y responde "Invalid Compact JWS".
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SeedError(f"Storage rechazo {object_key}: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise SeedError(f"Storage inalcanzable para {object_key}: {exc.reason}") from exc
        subidos += 1
        print(f"  subido {object_key} ({size} bytes)")
    print(f"Storage: {subidos} subidos, {omitidos} ya presentes con el mismo tamano.")


def _remote_size(url: str, object_key: str) -> int | None:
    """Tamano del objeto ya publicado, o None si no existe."""
    request = urllib.request.Request(
        f"{url}/storage/v1/object/public/{BUCKET}/{object_key}", method="HEAD"
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            length = response.headers.get("Content-Length")
            return int(length) if length is not None else None
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None


# ----------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga catalog.seed.json en Supabase.")
    parser.add_argument("--apply", action="store_true", help="escribir de verdad (por defecto no)")
    parser.add_argument("--upload", action="store_true", help="subir tambien los ficheros a Storage")
    args = parser.parse_args()

    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        media = MediaMap(json.loads(MANIFEST.read_text(encoding="utf-8")))
        plan = build_plan(catalog, media)
        subida = media.upload_plan()

        if not args.apply:
            print_plan(plan, subida)
            print("\nNada escrito. Anade --apply (y --upload) para aplicarlo.")
            return 0

        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise SeedError(
                "--apply necesita SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY. "
                "Estan en el dashboard del proyecto, en Settings > API."
            )

        print(f"Aplicando sobre {url}\n")
        apply_plan(Rest(url, key), plan)
        if args.upload:
            upload_media(subida, url, key)
        print("\nHecho.")
    except SeedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
