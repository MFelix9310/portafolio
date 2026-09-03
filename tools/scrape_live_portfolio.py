"""Descarga el contenido real del portafolio desplegado, en HTML crudo.

El seed original se genero desde `db.sqlite3` del repo de GitHub y esta
desactualizado: el despliegue en pythonanywhere tiene 23 proyectos (ids 7 a 29)
y tres experiencias en vez de una.

Version 2. La primera version pedia el idioma con la cookie `django_language`,
que este sitio ignora: el cambio de idioma va por `/set-language/?lang=xx` y se
guarda en la sesion. El resultado fue que todas las paginas "en" eran en
realidad castellano. Ademas se volcaba solo texto plano, perdiendo los enlaces
de repositorio y de demo, los pies de foto y el orden de la galeria.

Ahora se guarda el HTML crudo de cada pagina en `tools/live-html/<lang>/` y un
indice en `content/live-portfolio.json` con las rutas de media detectadas.
"""

from __future__ import annotations

import html
import http.cookiejar
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://gambito93.pythonanywhere.com"
RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "content" / "live-portfolio.json"
DIR_HTML = RAIZ / "tools" / "live-html"

RUTAS = [
    "/portfolio/",
    "/portfolio/education/",
    "/portfolio/certifications/",
    "/portfolio/projects/",
    "/portfolio/experience/",
    "/portfolio/publications/",
    "/portfolio/contact/",
]

IDIOMAS = ("es", "en")


def abridor() -> urllib.request.OpenerDirector:
    tarro = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(tarro))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def fijar_idioma(op: urllib.request.OpenerDirector, idioma: str) -> None:
    with op.open(f"{BASE}/set-language/?lang={idioma}&next=/portfolio/", timeout=60) as r:
        r.read()


def descargar(op: urllib.request.OpenerDirector, ruta: str) -> str:
    with op.open(BASE + ruta, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def a_lineas(bruto: str) -> list[str]:
    cuerpo = re.sub(r"<script.*?</script>|<style.*?</style>", "", bruto, flags=re.S)
    texto = html.unescape(re.sub(r"<[^>]+>", "\n", cuerpo))
    lineas: list[str] = []
    anterior = None
    for cruda in texto.split("\n"):
        linea = " ".join(cruda.split())
        if linea and linea != anterior:
            lineas.append(linea)
        anterior = linea
    return lineas


def enlaces_internos(bruto: str) -> set[str]:
    return {
        e
        for e in re.findall(r'href=["\']([^"\']+)["\']', bruto)
        if re.match(r"^/portfolio/(projects|experience)/\d+/$", e)
    }


def medios(bruto: str) -> list[str]:
    fuentes = re.findall(r'(?:src|href)=["\'](/media/[^"\']+)["\']', bruto)
    return sorted({urllib.parse.unquote(f) for f in fuentes})


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    documentos: dict[str, dict] = {}
    opers = {}
    for idioma in IDIOMAS:
        opers[idioma] = abridor()
        fijar_idioma(opers[idioma], idioma)
        (DIR_HTML / idioma).mkdir(parents=True, exist_ok=True)

    pendientes = list(RUTAS)
    vistas: set[str] = set()

    while pendientes:
        ruta = pendientes.pop(0)
        if ruta in vistas:
            continue
        vistas.add(ruta)
        brutos: dict[str, str] = {}
        for idioma in IDIOMAS:
            try:
                brutos[idioma] = descargar(opers[idioma], ruta)
            except Exception as error:
                print(f"  fallo {ruta} [{idioma}]: {error}")
                brutos[idioma] = ""
        if not brutos["es"]:
            continue

        nombre = ruta.strip("/").replace("/", "_") + ".html"
        for idioma in IDIOMAS:
            if brutos[idioma]:
                (DIR_HTML / idioma / nombre).write_text(brutos[idioma], encoding="utf-8")

        documentos[ruta] = {
            "html": {i: f"tools/live-html/{i}/{nombre}" for i in IDIOMAS if brutos[i]},
            "es": a_lineas(brutos["es"]),
            "en": a_lineas(brutos["en"]) if brutos["en"] else [],
            "media": medios(brutos["es"]),
        }
        for nuevo in sorted(enlaces_internos(brutos["es"])):
            if nuevo not in vistas:
                pendientes.append(nuevo)
        distinto = "es!=en" if brutos["en"] and documentos[ruta]["es"] != documentos[ruta]["en"] else "es==en"
        print(f"  ok {ruta}  ({len(documentos[ruta]['media'])} media, {distinto})")
        time.sleep(0.3)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps({"_base": BASE, "documentos": documentos}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nescrito {SALIDA}  ({len(documentos)} paginas)")


if __name__ == "__main__":
    main()
