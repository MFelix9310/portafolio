"""Incorpora experiencias desde `content/incoming/experiencias/*.json`.

El formato de entrada trae dos campos que el esquema de la base no tiene:
`vinculo_civil` y `cifra`. No se pierden: se pliegan dentro de `description`
como parrafos propios, porque el vinculo con la ingenieria civil es el
argumento del portafolio y merece ir en el cuerpo, no en un metadato.

`taxonomy`, `pais`, `confidencial`, `simultaneo_con` y `no_puedo_nombrar` se
conservan con prefijo `_` para poder auditarlos, y el cargador de Supabase los
ignora por no ser columnas.

    python tools/ingest_experiencias.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "content" / "incoming" / "experiencias"
CATALOGO = RAIZ / "content" / "catalog.seed.json"


def slugify(value: str) -> str:
    normal = unicodedata.normalize("NFD", value)
    ascii_only = "".join(c for c in normal if unicodedata.category(c) != "Mn")
    slug = "".join(c if c.isalnum() else "-" for c in ascii_only.lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:80]


def texto(valor, locale: str) -> str:
    if isinstance(valor, dict):
        return (valor.get(locale) or valor.get("es") or "").strip()
    return (valor or "").strip()


def descripcion(bruto: dict, locale: str) -> str:
    """Descripcion, vinculo civil y cifra, en ese orden, separados por parrafo."""
    partes = [texto(bruto.get("description"), locale)]

    vinculo = texto(bruto.get("vinculo_civil"), locale)
    if vinculo and vinculo.lower() not in ("null", "none", "ninguno"):
        partes.append(vinculo)

    cifra = bruto.get("cifra") or {}
    if isinstance(cifra, dict) and cifra.get("valor"):
        partes.append(str(cifra["valor"]).strip())

    return "\n\n".join(p for p in partes if p)


def convertir(bruto: dict, orden: int) -> dict:
    empresa = texto(bruto.get("company"), "es")
    puesto = texto(bruto.get("position"), "es")
    fila = {
        "legacy_id": None,
        "slug": slugify(f"{puesto}-{empresa}"),
        "company": {"es": empresa},
        "position": {"es": puesto},
        "description": {"es": descripcion(bruto, "es")},
        "keywords": bruto.get("keywords") or [],
        "keywords_en": [],
        "company_logo": None,
        "thumbnail": None,
        "start_date": bruto["start_date"],
        "end_date": bruto.get("end_date"),
        "is_current": bool(bruto.get("is_current")),
        # Mas reciente primero. La fecha manda; el orden solo desempata.
        "display_order": orden,
        "status": "published",
        "images": [],
        "_pais": bruto.get("pais"),
        "_taxonomy": bruto.get("taxonomy") or [],
        "_simultaneo_con": bruto.get("simultaneo_con") or [],
        "_no_puedo_nombrar": bruto.get("no_puedo_nombrar") or "",
    }
    for clave, locale in (("company", "en"), ("position", "en")):
        valor = texto(bruto.get(clave), "en")
        if valor and valor != fila[clave]["es"]:
            fila[clave]["en"] = valor
    en = descripcion(bruto, "en")
    if en and en != fila["description"]["es"]:
        fila["description"]["en"] = en
    return fila


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ficheros = sorted(ENTRADA.glob("*.json"))
    if not ficheros:
        raise SystemExit(f"nada en {ENTRADA}")

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    existentes = {e["slug"]: e for e in catalogo["experiences"]}

    nuevas = [convertir(json.loads(f.read_text(encoding="utf-8")), 0) for f in ficheros]
    for fila in nuevas:
        existentes[fila["slug"]] = fila

    # Orden cronologico inverso: lo vigente y lo mas reciente arriba.
    filas = sorted(
        existentes.values(),
        key=lambda e: (not e.get("is_current"), e.get("start_date") or ""),
        reverse=False,
    )
    filas.sort(key=lambda e: (e.get("start_date") or ""), reverse=True)
    for posicion, fila in enumerate(filas):
        fila["display_order"] = posicion

    catalogo["experiences"] = filas
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(nuevas)} incorporada(s), {len(filas)} experiencias en total:")
    for fila in filas:
        fin = "actualidad" if fila["is_current"] else (fila["end_date"] or "?")
        print(f"  {fila['start_date']} a {fin:<12} {fila['company']['es']}")
        if fila.get("_simultaneo_con"):
            print(f"      simultaneo con: {', '.join(fila['_simultaneo_con'])}")


if __name__ == "__main__":
    main()
