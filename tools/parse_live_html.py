"""Parsea el HTML crudo descargado por `scrape_live_portfolio.py`.

Devuelve estructuras de datos limpias (proyectos, experiencias, educacion,
certificaciones, publicaciones, perfil, contactos) por idioma. Lo consume
`build_catalog_seed.py`; se mantiene aparte para poder inspeccionar lo extraido
sin escribir el seed.

No se usa un parser HTML externo a proposito: las plantillas Django del sitio son
estables y regulares, y asi el script no depende de nada fuera de la stdlib.
"""

from __future__ import annotations

import html as html_mod
import json
import pathlib
import re
import unicodedata
import urllib.parse

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DIR_HTML = RAIZ / "tools" / "live-html"

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
    "diciembre": 12,
}


# --------------------------------------------------------------------------- #
# utilidades
# --------------------------------------------------------------------------- #
def texto(bruto: str | None) -> str | None:
    """Aplana un fragmento HTML a texto, conservando saltos de <br> y </p>."""
    if bruto is None:
        return None
    s = re.sub(r"<br\s*/?>", "\n", bruto, flags=re.I)
    s = re.sub(r"</p\s*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html_mod.unescape(s)
    lineas = [" ".join(l.split()) for l in s.split("\n")]
    return "\n".join(l for l in lineas if l).strip() or None


def ruta_media(url: str) -> str:
    """`/media/projects/images/1_ab.png` -> `projects/images/1_ab.png`."""
    limpio = urllib.parse.unquote(url)
    return limpio[len("/media/"):] if limpio.startswith("/media/") else limpio.lstrip("/")


def slugify(valor: str) -> str:
    s = unicodedata.normalize("NFD", valor)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80].rstrip("-")


def cargar(idioma: str, nombre: str) -> str:
    ruta = DIR_HTML / idioma / f"{nombre}.html"
    return ruta.read_text(encoding="utf-8") if ruta.exists() else ""


def cuerpo(bruto: str) -> str:
    i, j = bruto.find("<main"), bruto.find("</main>")
    if i == -1:
        return bruto
    return bruto[i:j] if j > i else bruto[i:]


def fecha_es(cadena: str) -> str | None:
    """`octubre 2025` -> `2025-10-01`."""
    m = re.search(r"([a-zá-ú]+)\s+(\d{4})", cadena.strip().lower())
    if not m or m.group(1) not in MESES:
        return None
    return f"{m.group(2)}-{MESES[m.group(1)]:02d}-01"


# --------------------------------------------------------------------------- #
# proyectos
# --------------------------------------------------------------------------- #
def listado_proyectos(idioma: str) -> list[dict]:
    b = cuerpo(cargar(idioma, "portfolio_projects"))
    tarjetas = re.split(r'<div class="col-md-6 col-lg-4 mb-4 project-item"', b)[1:]
    salida = []
    for orden, tarjeta in enumerate(tarjetas):
        skills = re.search(r'data-skills="([^"]*)"', tarjeta)
        pid = re.search(r'href="/portfolio/projects/(\d+)/"', tarjeta)
        titulo = re.search(r"<h4>(.*?)</h4>", tarjeta, re.S)
        tecno = re.search(r'<p class="mb-0">(.*?)</p>', tarjeta, re.S)
        badges = re.findall(r'<span class="category-badge">(.*?)</span>', tarjeta, re.S)
        img = re.search(r'<div id="image-\d+" class="project-image-container">\s*<img src="([^"]+)"', tarjeta)
        desc = re.search(r'<div id="description-\d+" class="project-description">\s*<p>(.*?)</p>', tarjeta, re.S)
        if not pid:
            continue
        tecnologias = texto(tecno.group(1)) if tecno else None
        salida.append({
            "id": int(pid.group(1)),
            "display_order": orden,
            "title": texto(titulo.group(1)) if titulo else None,
            "technologies": [t.strip() for t in tecnologias.split(",")] if tecnologias else [],
            "legacy_skills": [s for s in (skills.group(1).split(",") if skills else []) if s],
            "categories": [texto(x) for x in badges],
            "thumbnail": ruta_media(img.group(1)) if img else None,
            "summary": texto(desc.group(1)) if desc else None,
        })
    return salida


def detalle_proyecto(idioma: str, pid: int) -> dict:
    b = cuerpo(cargar(idioma, f"portfolio_projects_{pid}"))
    if not b:
        return {}

    titulo = re.search(r'<h1 class="display-4 fw-bold"[^>]*>(.*?)</h1>', b, re.S)
    tecno = re.search(r'<p class="lead text-orange mb-0"[^>]*>(.*?)</p>', b, re.S)
    enlaces = re.search(r'class="project-links mt-4".*?</div>', b, re.S)
    repo = demo = None
    if enlaces:
        for href, clase in re.findall(r'<a href="([^"]+)"[^>]*class="btn ([^"]+)"', enlaces.group(0)):
            if "btn-github" in clase:
                repo = html_mod.unescape(href)
            elif "btn-orange" in clase:
                demo = html_mod.unescape(href)

    portada = re.search(r'<div class="project-detail-img[^"]*"[^>]*>\s*<img src="([^"]+)"', b)
    resumen = re.search(r'<div class="project-detail-content"[^>]*>.*?<p>(.*?)</p>', b, re.S)

    imagenes = []
    galeria = re.search(r'<!-- Images -->(.*?)(?:<!-- Videos -->|<!-- Documents -->|</div>\s*</div>\s*</div>\s*</section>)', b, re.S)
    if galeria:
        for orden, (href, titulo_img) in enumerate(
            re.findall(r'<a href="(/media/[^"]+)"[^>]*class="glightbox"[^>]*data-title="([^"]*)"', galeria.group(1))
        ):
            imagenes.append({"path": ruta_media(href), "caption": html_mod.unescape(titulo_img) or None, "order": orden})

    videos = []
    bloque_v = re.search(r"<!-- Videos -->(.*?)(?:<!-- Documents -->|</div>\s*</div>\s*</section>)", b, re.S)
    if bloque_v:
        for orden, item in enumerate(re.split(r'<div class="col-md-6 mb-4">', bloque_v.group(1))[1:]):
            src = re.search(r'<source src="(/media/[^"]+)"', item)
            cap = re.search(r'<p class="mt-2 text-center">(.*?)</p>', item, re.S)
            if src:
                videos.append({"path": ruta_media(src.group(1)), "caption": texto(cap.group(1)) if cap else None, "order": orden})

    documentos = []
    bloque_d = re.search(r"<!-- Documents -->(.*)", b, re.S)
    if bloque_d:
        for orden, (href, etiqueta) in enumerate(
            re.findall(r'<a href="(/media/[^"]+)"[^>]*class="btn btn-outline-secondary[^"]*"[^>]*>(.*?)</a>', bloque_d.group(1), re.S)
        ):
            documentos.append({"path": ruta_media(href), "title": texto(etiqueta), "order": orden})

    return {
        "id": pid,
        "title": texto(titulo.group(1)) if titulo else None,
        "technologies_raw": texto(tecno.group(1)) if tecno else None,
        "repository_url": repo,
        "project_url": demo,
        "thumbnail": ruta_media(portada.group(1)) if portada else None,
        "summary": texto(resumen.group(1)) if resumen else None,
        "images": imagenes,
        "videos": videos,
        "documents": documentos,
    }


def ids_proyectos() -> list[int]:
    return [p["id"] for p in listado_proyectos("es")]


# --------------------------------------------------------------------------- #
# experiencias
# --------------------------------------------------------------------------- #
def listado_experiencias(idioma: str) -> list[dict]:
    b = cuerpo(cargar(idioma, "portfolio_experience"))
    tarjetas = re.split(r'<div class="col-md-6 mb-4 work-item', b)[1:]
    salida = []
    for orden, t in enumerate(tarjetas):
        eid = re.search(r'href="/portfolio/experience/(\d+)/"', t)
        logo = re.search(r'<img src="(/media/[^"]+)"[^>]*class="company-logo"', t)
        if not eid:
            continue
        salida.append({
            "id": int(eid.group(1)),
            "display_order": orden,
            "company_logo": ruta_media(logo.group(1)) if logo else None,
        })
    return salida


def detalle_experiencia(idioma: str, eid: int) -> dict:
    b = cuerpo(cargar(idioma, f"portfolio_experience_{eid}"))
    if not b:
        return {}
    puesto = re.search(r'<h1 class="display-4 fw-bold"[^>]*>(.*?)</h1>', b, re.S)
    empresa = re.search(r'<p class="lead text-orange mb-0"[^>]*>(.*?)</p>', b, re.S)
    fechas = re.search(r'<span class="badge bg-light text-dark p-2">(.*?)</span>', b, re.S)
    portada = re.search(r'<div class="work-detail-img[^"]*"[^>]*>\s*<img src="(/media/[^"]+)"', b)
    desc = re.search(r'<div class="work-detail-content"[^>]*>.*?<h3[^>]*>.*?</h3>\s*<p>(.*?)</p>\s*</div>', b, re.S)
    funciones = re.search(r'<div class="work-functions[^"]*"[^>]*>.*?<div class="p-4 bg-light rounded">\s*<p>(.*?)</p>', b, re.S)

    imagenes = []
    galeria = re.search(r'<div class="work-gallery[^"]*"[^>]*>(.*?)</section>', b, re.S)
    if galeria:
        for orden, (href, cap) in enumerate(
            re.findall(r'<a href="(/media/[^"]+)"[^>]*class="glightbox"[^>]*data-title="([^"]*)"', galeria.group(1))
        ):
            imagenes.append({"path": ruta_media(href), "caption": html_mod.unescape(cap) or None, "order": orden})

    crudo = texto(fechas.group(1)) if fechas else ""
    partes = [p.strip() for p in (crudo or "").split("-")]
    inicio = fecha_es(partes[0]) if partes else None
    fin_txt = partes[1] if len(partes) > 1 else ""
    actual = fin_txt.lower() in {"actualidad", "present", "currently"} or not fin_txt
    return {
        "id": eid,
        "position": texto(puesto.group(1)) if puesto else None,
        "company": texto(empresa.group(1)) if empresa else None,
        "description": texto(desc.group(1)) if desc else None,
        "keywords_raw": texto(funciones.group(1)) if funciones else None,
        "thumbnail": ruta_media(portada.group(1)) if portada else None,
        "start_date": inicio,
        "end_date": None if actual else fecha_es(fin_txt),
        "is_current": actual,
        "images": imagenes,
        "dates_raw": crudo,
    }


# --------------------------------------------------------------------------- #
# educacion / certificaciones / publicaciones / perfil / contactos
# --------------------------------------------------------------------------- #
def educacion(idioma: str) -> list[dict]:
    b = cuerpo(cargar(idioma, "portfolio_education"))
    tarjetas = re.split(r'<div class="education-card h-100">', b)[1:]
    salida = []
    for orden, t in enumerate(tarjetas):
        eid = re.search(r'data-target="education-description-(\d+)"', t)
        titulo = re.search(r"<h4>(.*?)</h4>", t, re.S)
        inst = re.search(r'<p class="mb-0">(.*?)</p>', t, re.S)
        anio = re.search(r'<span class="education-year">(.*?)</span>', t, re.S)
        desc = re.search(r'<div id="education-description-\d+"[^>]*>\s*<p>(.*?)</p>', t, re.S)
        salida.append({
            "id": int(eid.group(1)) if eid else None,
            "display_order": orden,
            "title": texto(titulo.group(1)) if titulo else None,
            "institution": texto(inst.group(1)) if inst else None,
            "graduation_year": int(texto(anio.group(1))) if anio and (texto(anio.group(1)) or "").isdigit() else None,
            "description": texto(desc.group(1)) if desc else None,
        })
    return salida


def certificaciones(idioma: str) -> list[dict]:
    b = cuerpo(cargar(idioma, "portfolio_certifications"))
    tarjetas = re.split(r'<div class="certification-card h-100">', b)[1:]
    salida = []
    for orden, t in enumerate(tarjetas):
        cid = re.search(r'data-target="description-(\d+)"', t)
        nombre = re.search(r"<h4>(.*?)</h4>", t, re.S)
        emisor = re.search(r'<p class="mb-0">(.*?)</p>', t, re.S)
        fecha = re.search(r'<span class="certification-date">(.*?)</span>', t, re.S)
        desc = re.search(r'<div id="description-\d+"[^>]*>\s*<p>(.*?)</p>', t, re.S)
        archivo = re.search(r'<a href="(/media/certificates/[^"]+)"', t)
        credencial = re.search(r'<a href="(https?://[^"]+)"[^>]*class="btn btn-sm btn-orange mb-2 ms-2"', t)
        expira = re.search(r"(?:Expira|Expires):\s*([\d/]+)", t)
        vence = None
        if expira:
            d, m, a = expira.group(1).split("/")
            vence = f"{a}-{m}-{d}"
        salida.append({
            "id": int(cid.group(1)) if cid else None,
            "display_order": orden,
            "name": texto(nombre.group(1)) if nombre else None,
            "issuer": texto(emisor.group(1)) if emisor else None,
            "issued_on": fecha_es(texto(fecha.group(1)) or "") if fecha else None,
            "issued_raw": texto(fecha.group(1)) if fecha else None,
            "expires_on": vence,
            "description": texto(desc.group(1)) if desc else None,
            "certificate_file": ruta_media(archivo.group(1)) if archivo else None,
            "credential_url": html_mod.unescape(credencial.group(1)) if credencial else None,
        })
    return salida


def publicaciones(idioma: str) -> list[dict]:
    b = cuerpo(cargar(idioma, "portfolio_publications"))
    secciones = re.findall(r'<h2 class="category-title"[^>]*>(.*?)</h2>(.*?)(?=<h2 class="category-title"|\Z)', b, re.S)
    salida = []
    orden = 0
    for etiqueta, bloque in secciones:
        for t in re.split(r'<div class="publication-card h-100">', bloque)[1:]:
            pid = re.search(r'data-target="description-(\d+)"', t)
            titulo = re.search(r"<h4>(.*?)</h4>", t, re.S)
            campos = re.findall(r'<p class="mb-0">(.*?)</p>', t, re.S)
            anio = re.search(r'<span class="publication-date">(.*?)</span>', t, re.S)
            desc = re.search(r'<div id="description-\d+"[^>]*>\s*<p>(.*?)</p>', t, re.S)
            img = re.search(r'<div id="image-\d+"[^>]*>\s*<img src="(/media/[^"]+)"', t)
            enlace = re.search(r'<a href="(https?://[^"]+)"[^>]*class="btn btn-sm btn-orange"', t)
            pdf = re.search(r'<a href="(/media/publications/[^"]+)"', t)
            salida.append({
                "id": int(pid.group(1)) if pid else None,
                "display_order": orden,
                "category": texto(etiqueta),
                "title": texto(titulo.group(1)) if titulo else None,
                "authors": texto(campos[0]) if campos else None,
                "venue": texto(campos[1]) if len(campos) > 1 else None,
                "year": int(texto(anio.group(1))) if anio and (texto(anio.group(1)) or "").isdigit() else None,
                "abstract": texto(desc.group(1)) if desc else None,
                "cover": ruta_media(img.group(1)) if img else None,
                "url": html_mod.unescape(enlace.group(1)) if enlace else None,
                "file": ruta_media(pdf.group(1)) if pdf else None,
            })
            orden += 1
    return salida


def perfil(idioma: str) -> dict:
    b = cuerpo(cargar(idioma, "portfolio"))
    nombre = re.search(r'<div class="hero-content"[^>]*>\s*<h1>(.*?)</h1>', b, re.S)
    subtitulo = re.search(r'<p class="subtitle">(.*?)</p>', b, re.S)
    bio = re.search(r'<div id="bioContainer"[^>]*>\s*<p>(.*?)</p>', b, re.S)
    foto = re.search(r'<img src="(/media/profile/[^"]+)"[^>]*class="hero-img"', b)
    prof = re.search(r'<img src="(/media/profile/professional/[^"]+)"', cargar(idioma, "portfolio"))
    return {
        "name": texto(nombre.group(1)) if nombre else None,
        "title": texto(subtitulo.group(1)) if subtitulo else None,
        "bio": texto(bio.group(1)) if bio else None,
        "photo": ruta_media(foto.group(1)) if foto else None,
        "professional_photo": ruta_media(prof.group(1)) if prof else None,
    }


def contactos(idioma: str) -> list[dict]:
    b = cuerpo(cargar(idioma, "portfolio_contact"))
    salida = []
    for orden, item in enumerate(re.split(r'<div class="contact-info-item">', b)[1:]):
        etiqueta = re.search(r"<h5>(.*?)</h5>", item, re.S)
        enlace = re.search(r'<a href="([^"]+)"', item)
        icono = re.search(r'<i class="([^"]+)"></i>', item)
        salida.append({
            "display_order": orden,
            "label": texto(etiqueta.group(1)) if etiqueta else None,
            "url": html_mod.unescape(enlace.group(1)) if enlace else None,
            "icon": icono.group(1) if icono else None,
        })
    return salida


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    datos = {
        "perfil": {i: perfil(i) for i in ("es", "en")},
        "proyectos_listado": {i: listado_proyectos(i) for i in ("es", "en")},
        "proyectos_detalle": {
            i: [detalle_proyecto(i, p) for p in ids_proyectos()] for i in ("es", "en")
        },
        "experiencias_listado": {i: listado_experiencias(i) for i in ("es", "en")},
        "experiencias_detalle": {
            i: [detalle_experiencia(i, e["id"]) for e in listado_experiencias("es")] for i in ("es", "en")
        },
        "educacion": {i: educacion(i) for i in ("es", "en")},
        "certificaciones": {i: certificaciones(i) for i in ("es", "en")},
        "publicaciones": {i: publicaciones(i) for i in ("es", "en")},
        "contactos": {i: contactos(i) for i in ("es", "en")},
    }
    destino = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "tools" / "live-parsed.json"
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"escrito {destino}")
