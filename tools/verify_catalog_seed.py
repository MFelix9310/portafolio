"""Comprobaciones sobre `content/catalog.seed.json`. Falla ruidosamente.

1. Conteos por entidad y por subarea de la taxonomia.
2. Toda subarea de la semilla del contrato (docs/02-contrato-datos.md A13) se
   declara, y se avisa de las que quedan sin ningun proyecto.
3. Todo `repository_url` y `project_url` emitido aparece literalmente en el HTML
   descargado del sitio en vivo. Nada deducido.
4. Toda ruta de media del seed tiene entrada en `content/media-manifest.json`.
5. Ningun proyecto del seed viejo desaparece del nuevo.

Uso: `python tools/verify_catalog_seed.py [--saltar-manifiesto]`
"""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.parse

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SEED = RAIZ / "content" / "catalog.seed.json"
VIEJO = RAIZ / "content" / "catalog.seed.legacy.json"
MANIFIESTO = RAIZ / "content" / "media-manifest.json"
DIR_HTML = RAIZ / "tools" / "live-html" / "es"

SEMILLA = {
    "data": ["analyst", "scientist", "engineer"],
    "developer": ["fullstack", "backend", "desktop"],
    "civil-bim": ["structural", "geotechnical", "bim", "construction"],
}


def rutas_media(seed: dict) -> dict[str, list[str]]:
    """Ruta de media -> lista de sitios del seed que la referencian."""
    encontradas: dict[str, list[str]] = {}

    def anota(ruta, origen):
        if ruta:
            encontradas.setdefault(ruta, []).append(origen)

    p = seed["profile"]
    anota(p.get("photo"), "profile.photo")
    anota(p.get("professional_photo"), "profile.professional_photo")
    for pr in seed["projects"]:
        anota(pr["thumbnail"], f"project[{pr['legacy_id']}].thumbnail")
        for grupo in ("images", "videos", "documents"):
            for i, item in enumerate(pr[grupo]):
                anota(item["path"], f"project[{pr['legacy_id']}].{grupo}[{i}]")
    for ex in seed["experiences"]:
        anota(ex["company_logo"], f"experience[{ex['legacy_id']}].company_logo")
        anota(ex["thumbnail"], f"experience[{ex['legacy_id']}].thumbnail")
        for i, item in enumerate(ex.get("images", [])):
            anota(item["path"], f"experience[{ex['legacy_id']}].images[{i}]")
    for c in seed["certifications"]:
        anota(c["certificate_file"], f"certification[{c['legacy_id']}].certificate_file")
    for pu in seed["publications"]:
        anota(pu["pdf_file"], f"publication[{pu['legacy_id']}].pdf_file")
        anota(pu["thumbnail"], f"publication[{pu['legacy_id']}].thumbnail")
    return encontradas


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    saltar_manifiesto = "--saltar-manifiesto" in sys.argv
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    errores: list[str] = []
    avisos: list[str] = []

    # 1. conteos ------------------------------------------------------------
    print("== conteos por entidad")
    for k in ("projects", "experiences", "certifications", "education", "publications", "contacts"):
        print(f"   {k:<15} {len(seed[k])}")

    # 2. taxonomia ----------------------------------------------------------
    print("\n== proyectos por subarea")
    cuenta: dict[tuple[str, str], list[int]] = {(a, s): [] for a, subs in SEMILLA.items() for s in subs}
    for pr in seed["projects"]:
        if not pr["taxonomy"]:
            errores.append(f"proyecto {pr['legacy_id']} sin taxonomia")
        for t in pr["taxonomy"]:
            par = (t["area"], t["subarea"])
            if par not in cuenta:
                errores.append(f"proyecto {pr['legacy_id']} usa area/subarea fuera de la semilla: {par}")
                cuenta[par] = []
            cuenta[par].append(pr["legacy_id"])
    for (a, s), ids in cuenta.items():
        marca = "  " if ids else "!!"
        print(f"   {marca} {a}/{s:<13} {len(ids):>2}  {ids}")
        if not ids:
            avisos.append(f"subarea sin proyectos: {a}/{s}")

    # 3. urls contra el HTML en vivo ----------------------------------------
    print("\n== urls contra el HTML en vivo")
    fallos_url = 0
    for pr in seed["projects"]:
        ruta = DIR_HTML / f"portfolio_projects_{pr['legacy_id']}.html"
        if not ruta.exists():
            errores.append(f"no hay HTML en vivo para el proyecto {pr['legacy_id']}")
            continue
        html = ruta.read_text(encoding="utf-8")
        for campo in ("repository_url", "project_url"):
            url = pr[campo]
            if not url:
                continue
            # El HTML escapa `&` y puede llevar el porcentaje codificado.
            candidatos = {url, url.replace("&", "&amp;"), urllib.parse.quote(url, safe=":/?=&%#")}
            if not any(c in html for c in candidatos):
                errores.append(f"proyecto {pr['legacy_id']}.{campo} no aparece en el HTML en vivo: {url}")
                fallos_url += 1
    print(f"   {fallos_url} discrepancias")

    # 4. media contra el manifiesto -----------------------------------------
    print("\n== media contra content/media-manifest.json")
    referencias = rutas_media(seed)
    print(f"   {len(referencias)} rutas distintas referenciadas por el seed")
    if saltar_manifiesto:
        print("   (comprobacion saltada)")
    elif not MANIFIESTO.exists():
        errores.append("falta content/media-manifest.json")
    else:
        entradas = json.loads(MANIFIESTO.read_text(encoding="utf-8"))["entries"]
        faltan = sorted(r for r in referencias if r not in entradas)
        for r in faltan:
            errores.append(f"ruta de media sin entrada en el manifiesto: {r}  ({referencias[r][0]})")
        print(f"   {len(referencias) - len(faltan)} con entrada, {len(faltan)} sin entrada")

    # 5. nada perdido del seed viejo ----------------------------------------
    print("\n== proyectos del seed viejo")
    viejo = json.loads(VIEJO.read_text(encoding="utf-8"))
    nuevos = {p["slug"]: p for p in seed["projects"]}
    for p in viejo["projects"]:
        if p["slug"] in nuevos:
            print(f"   ok  legacy {p['legacy_id']} -> live {nuevos[p['slug']]['legacy_id']}  {p['slug'][:55]}")
        else:
            errores.append(f"proyecto del seed viejo perdido: {p['legacy_id']} {p['slug']}")

    if avisos:
        print("\n== avisos")
        for a in avisos:
            print("   -", a)
    if errores:
        print(f"\n== FALLO: {len(errores)} errores")
        for e in errores:
            print("   -", e)
        return 1
    print("\n== OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
