"""Reconstruye `content/catalog.seed.json` desde el portafolio en vivo.

Fuente de verdad: el HTML crudo en `tools/live-html/`, descargado por
`scrape_live_portfolio.py` y parseado por `parse_live_html.py`.

El seed viejo (`content/catalog.seed.legacy.json`) solo se usa para rellenar
campos que el sitio no renderiza y que por tanto no se pueden leer de el:
`created_at` de proyecto, el dia exacto de una fecha que la web muestra solo con
mes, y `doi`/`isbn` de las publicaciones. Nunca para el contenido en si.

Regla de idioma: si el ingles falta o es identico al castellano se omite la clave
`en`, igual que hacia `export_legacy_content.py`. No se traduce nada aqui.
"""

from __future__ import annotations

import json
import pathlib
import sys

import parse_live_html as live

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SEED = RAIZ / "content" / "catalog.seed.json"
LEGACY = RAIZ / "content" / "catalog.seed.legacy.json"

# --------------------------------------------------------------------------- #
# Taxonomia. Clave = id del proyecto en el sitio en vivo.
#
# Criterio, documentado tambien en content/README.md:
#   - `data/engineer`   pipeline real de ingesta y transformacion por capas.
#   - `data/scientist`  hay un modelo entrenado y metricas de validacion.
#   - `data/analyst`    el entregable es analisis o reporting sobre datos.
#   - `developer/*`     forma del software entregado (escritorio, web, backend).
#   - `civil-bim/*`     el dominio del problema es ingenieria civil.
# Un proyecto lleva todas las parejas que le apliquen. El cruce civil + data es
# deliberado: es el argumento del portafolio, no un error de clasificacion.
# --------------------------------------------------------------------------- #
TAXONOMIA: dict[int, list[tuple[str, str]]] = {
    29: [("data", "engineer"), ("data", "scientist"), ("civil-bim", "structural")],
    28: [("data", "engineer"), ("data", "analyst")],
    27: [("data", "engineer"), ("data", "scientist")],
    26: [("data", "engineer"), ("data", "scientist")],
    25: [("civil-bim", "construction"), ("developer", "desktop")],
    24: [("civil-bim", "geotechnical"), ("developer", "desktop"), ("data", "analyst")],
    23: [("civil-bim", "structural"), ("developer", "desktop")],
    22: [("civil-bim", "structural"), ("data", "scientist")],
    21: [("civil-bim", "structural"), ("data", "scientist")],
    20: [("civil-bim", "structural"), ("data", "scientist")],
    19: [("civil-bim", "structural"), ("data", "scientist")],
    18: [("civil-bim", "structural"), ("data", "scientist")],
    17: [("developer", "fullstack"), ("developer", "backend"), ("data", "analyst")],
    16: [("civil-bim", "construction"), ("data", "scientist"), ("developer", "desktop")],
    15: [("civil-bim", "structural"), ("data", "scientist"), ("developer", "desktop")],
    14: [("civil-bim", "structural"), ("data", "scientist")],
    13: [("civil-bim", "structural"), ("data", "scientist"), ("data", "analyst")],
    12: [("data", "scientist"), ("developer", "desktop")],
    11: [("civil-bim", "structural"), ("data", "scientist")],
    10: [("civil-bim", "structural"), ("data", "scientist")],
    9: [("data", "scientist"), ("developer", "desktop")],
    8: [("developer", "fullstack"), ("developer", "backend")],
    7: [("developer", "desktop"), ("developer", "backend")],
}

JUSTIFICACION: dict[int, str] = {
    29: "Pipeline Medallion Bronze/Silver/Gold y modelo surrogate para fiabilidad de acero: ingenieria de datos, ciencia de datos y calculo estructural en el mismo proyecto.",
    28: "Pipeline end-to-end en Microsoft Fabric con Delta Lake y modelado Kimball; el entregable son tablas Gold para BI, sin dominio civil.",
    27: "Ingesta de cinco fuentes satelitales a arquitectura Medallion e indices de sequia derivados: ingenieria de datos con analitica cientifica encima.",
    26: "250M de ofertas leidas en streaming desde object storage con clustering no supervisado; infraestructura de datos y modelado en partes iguales.",
    25: "Planificacion de obra con ruta critica CPM entregada como aplicacion de escritorio PySide6; construccion, no calculo estructural.",
    24: "Procesado de ensayos CPT y clasificacion Robertson: geotecnia pura, entregada como escritorio y con analitica de perfiles y control de calidad.",
    23: "Calculo estructural de collar ties en cubierta de madera segun CBC 2022 y NDS 2018, empaquetado como escritorio; sin componente de datos.",
    22: "Modos de pandeo local, distorsional y global de perfil conformado en frio predichos con modelos entrenados sobre resultados FEM.",
    21: "Analisis elastoplastico de viga A36 con prediccion ML del comportamiento; mecanica computacional mas modelo.",
    20: "Gemelo digital sismico: clasificacion de dano con Random Forest sobre respuesta estructural. Civil y data a la vez por definicion.",
    19: "Graph Neural Networks que sustituyen FEM para campos de esfuerzos; deep learning aplicado a mecanica estructural.",
    18: "Gemelo digital sismico con LSTM sobre acelerograma Kanai-Tajimi e integracion Newmark-beta calibrada a NEC-15.",
    17: "Aplicacion web Django completa con panel de administracion y reporting PDF/Excel; fullstack con backend propio y analitica de uso.",
    16: "Predictor XGBoost de costos de construccion con GUI PySide6: estimacion de presupuesto de obra sobre un modelo entrenado.",
    15: "Prediccion de resistencia a compresion del hormigon clasificada segun NEC Ecuador, con Random Forest y GUI PyQt6.",
    14: "Prediccion de carga ultima en traccion de acero A36 a partir de dimensiones de probeta; ensayo de materiales modelado con ML.",
    13: "RandomForest sobre 124.639 ensayos de traccion de A36, S275 y S355; el volumen y el EDA justifican tambien la subarea de analisis.",
    12: "Prediccion de consumo y crecimiento avicola con GUI PyQt5; dominio agropecuario, sin componente civil.",
    11: "Curvas esfuerzo-deformacion de compuestos con relave segun tiempo de curado: caracterizacion de material estructural predicha con ML.",
    10: "Prediccion de pandeo en perfiles de acero con CatBoost validada contra metodos analiticos y normativa.",
    9: "Prediccion del tiempo de crecimiento de agave con RandomForest y GUI PySide6; dominio agricola.",
    8: "Sistema de gestion para tiendas de mascotas en Django con dashboard; aplicacion web de negocio.",
    7: "Gestion de laboratorios en PySide6 con ORM y generacion de PDF; escritorio con logica de servidor empaquetada dentro.",
}


# --------------------------------------------------------------------------- #
def bilingue(es, en):
    """{'es': …} y solo añade 'en' si existe y difiere. Nunca inventa traduccion."""
    if es is None and en is None:
        return None
    valor = {}
    if es is not None:
        valor["es"] = es
    if en is not None and en != es:
        valor["en"] = en
    return valor or None


def sin_nulos(lista):
    return [x for x in lista if x]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    heredado = json.loads(LEGACY.read_text(encoding="utf-8")) if LEGACY.exists() else {}
    avisos: list[str] = []

    # --- proyectos ---------------------------------------------------------
    lista_es = live.listado_proyectos("es")
    lista_en = {p["id"]: p for p in live.listado_proyectos("en")}
    # `created_at` no se renderiza en ninguna pagina del sitio: se recupera del
    # seed viejo emparejando por slug, y queda a null en los proyectos nuevos.
    creado = {}
    for p in heredado.get("projects", []):
        creado[live.slugify(p["title"]["es"])] = p["created_at"]

    proyectos = []
    for entrada in lista_es:
        pid = entrada["id"]
        det_es = live.detalle_proyecto("es", pid)
        det_en = live.detalle_proyecto("en", pid)
        entrada_en = lista_en.get(pid, {})

        titulo_es = det_es.get("title") or entrada["title"]
        slug = live.slugify(titulo_es)
        if pid not in TAXONOMIA:
            raise SystemExit(f"proyecto {pid} sin taxonomia asignada")

        # La galeria es identica en ambos idiomas salvo los pies de foto.
        imagenes = []
        pies_en = {i["path"]: i["caption"] for i in det_en.get("images", [])}
        for img in det_es.get("images", []):
            imagenes.append({
                "path": img["path"],
                "caption": bilingue(img["caption"], pies_en.get(img["path"])),
                "order": img["order"],
            })
        videos = []
        pies_v = {v["path"]: v["caption"] for v in det_en.get("videos", [])}
        for vid in det_es.get("videos", []):
            videos.append({
                "path": vid["path"],
                "caption": bilingue(vid["caption"], pies_v.get(vid["path"])),
                "order": vid["order"],
            })
        documentos = []
        titulos_d = {d["path"]: d["title"] for d in det_en.get("documents", [])}
        for doc in det_es.get("documents", []):
            documentos.append({
                "path": doc["path"],
                "title": bilingue(doc["title"], titulos_d.get(doc["path"])),
                "order": doc["order"],
            })

        if slug not in creado:
            avisos.append(f"proyecto {pid} ({slug}): sin created_at, el sitio no lo publica")

        proyectos.append({
            "legacy_id": pid,
            "slug": slug,
            "title": bilingue(titulo_es, det_en.get("title") or entrada_en.get("title")),
            "summary": bilingue(
                det_es.get("summary") or entrada["summary"],
                det_en.get("summary") or entrada_en.get("summary"),
            ),
            "technologies": entrada["technologies"],
            "technologies_en": entrada_en.get("technologies") or entrada["technologies"],
            "project_url": det_es.get("project_url"),
            "repository_url": det_es.get("repository_url"),
            "thumbnail": det_es.get("thumbnail") or entrada["thumbnail"],
            "created_at": creado.get(slug),
            "display_order": entrada["display_order"],
            "status": "published",
            "legacy_skills": entrada["legacy_skills"],
            "taxonomy": [{"area": a, "subarea": s} for a, s in TAXONOMIA[pid]],
            "images": imagenes,
            "videos": videos,
            "documents": documentos,
        })

    # --- experiencias ------------------------------------------------------
    inicio_heredado = {e["legacy_id"]: e["start_date"] for e in heredado.get("experiences", [])}
    experiencias = []
    for entrada in live.listado_experiencias("es"):
        eid = entrada["id"]
        es = live.detalle_experiencia("es", eid)
        en = live.detalle_experiencia("en", eid)
        pies_en = {i["path"]: i["caption"] for i in en.get("images", [])}
        # El sitio muestra "octubre 2025", sin dia. Donde el seed viejo tenia la
        # fecha exacta se conserva; en las nuevas queda el dia 1 del mes.
        inicio = inicio_heredado.get(eid)
        if inicio and inicio[:7] != (es["start_date"] or "")[:7]:
            avisos.append(f"experiencia {eid}: start_date heredado {inicio} no cuadra con el vivo {es['start_date']}")
            inicio = es["start_date"]
        if not inicio:
            inicio = es["start_date"]
            avisos.append(f"experiencia {eid}: start_date con precision de mes ({inicio}), el sitio no publica el dia")
        experiencias.append({
            "legacy_id": eid,
            "slug": live.slugify(f"{es['position']} {es['company']}"),
            "company": bilingue(es["company"], en.get("company")),
            "position": bilingue(es["position"], en.get("position")),
            "description": bilingue(es["description"], en.get("description")),
            "keywords": [k.strip() for k in (es["keywords_raw"] or "").split(",") if k.strip()],
            "keywords_en": [k.strip() for k in (en.get("keywords_raw") or es["keywords_raw"] or "").split(",") if k.strip()],
            "company_logo": entrada["company_logo"],
            "thumbnail": es["thumbnail"],
            "start_date": inicio,
            "end_date": es["end_date"],
            "is_current": es["is_current"],
            "display_order": entrada["display_order"],
            "status": "published",
            # Campo añadido: el sitio en vivo publica galeria en las experiencias
            # y el esquema heredado no la contemplaba. Ver content/README.md.
            "images": [
                {"path": i["path"], "caption": bilingue(i["caption"], pies_en.get(i["path"])), "order": i["order"]}
                for i in es.get("images", [])
            ],
        })

    # --- certificaciones ---------------------------------------------------
    emitido_heredado = {c["legacy_id"]: c["issued_on"] for c in heredado.get("certifications", [])}
    certificaciones = []
    cert_en = {c["id"]: c for c in live.certificaciones("en")}
    for c in live.certificaciones("es"):
        e = cert_en.get(c["id"], {})
        emitido = emitido_heredado.get(c["id"])
        if not emitido:
            emitido = c["issued_on"]
            avisos.append(f"certificacion {c['id']} ({c['name']}): issued_on con precision de mes ({emitido})")
        certificaciones.append({
            "legacy_id": c["id"],
            "slug": live.slugify(c["name"]),
            "name": bilingue(c["name"], e.get("name")),
            "issuer": bilingue(c["issuer"], e.get("issuer")),
            "description": bilingue(c["description"], e.get("description")),
            "issued_on": emitido,
            "expires_on": c["expires_on"],
            "credential_url": c["credential_url"],
            "certificate_file": c["certificate_file"],
            "display_order": c["display_order"],
            "status": "published",
        })

    # --- educacion ---------------------------------------------------------
    edu_en = {e["id"]: e for e in live.educacion("en")}
    educacion = []
    for e in live.educacion("es"):
        t = edu_en.get(e["id"], {})
        educacion.append({
            "legacy_id": e["id"],
            "institution": bilingue(e["institution"], t.get("institution")),
            "title": bilingue(e["title"], t.get("title")),
            "description": bilingue(e["description"], t.get("description")),
            "graduation_year": e["graduation_year"],
            "display_order": e["display_order"],
            "status": "published",
        })

    # --- publicaciones -----------------------------------------------------
    TIPO = {"Libros": "book", "Books": "book", "Artículos": "article", "Articles": "article",
            "Congresos": "conference", "Conferences": "conference", "Tesis": "thesis", "Thesis": "thesis"}
    fecha_heredada = {p["legacy_id"]: p for p in heredado.get("publications", [])}
    pub_en = {p["id"]: p for p in live.publicaciones("en")}
    publicaciones = []
    for p in live.publicaciones("es"):
        t = pub_en.get(p["id"], {})
        viejo = fecha_heredada.get(p["id"], {})
        publicado = viejo.get("published_on")
        if publicado and publicado[:4] != str(p["year"]):
            avisos.append(f"publicacion {p['id']}: published_on heredado {publicado} no cuadra con el año vivo {p['year']}")
            publicado = f"{p['year']}-01-01"
        if not publicado:
            publicado = f"{p['year']}-01-01"
            avisos.append(f"publicacion {p['id']}: published_on con precision de año ({publicado})")
        publicaciones.append({
            "legacy_id": p["id"],
            "slug": live.slugify(p["title"]),
            "kind": TIPO.get(p["category"], "other"),
            "title": bilingue(p["title"], t.get("title")),
            "authors": bilingue(p["authors"], t.get("authors")),
            "venue": bilingue(p["venue"], t.get("venue")),
            "abstract": bilingue(p["abstract"], t.get("abstract")),
            "published_on": publicado,
            "doi": viejo.get("doi"),
            "isbn": viejo.get("isbn"),
            "url": p["url"],
            "pdf_file": p["file"],
            "thumbnail": p["cover"],
            "display_order": p["display_order"],
            "status": "published",
        })

    # --- perfil y contactos ------------------------------------------------
    pes, pen = live.perfil("es"), live.perfil("en")
    perfil = {
        "name": pes["name"],
        "legacy_title": bilingue(pes["title"], pen["title"]),
        "bio": bilingue(pes["bio"], pen["bio"]),
        "photo": pes["photo"],
        "professional_photo": pes["professional_photo"],
    }

    ICONO = {"fab fa-linkedin": "linkedin", "fab fa-instagram": "instagram",
             "fab fa-github": "github", "fas fa-envelope": "email", "fas fa-phone": "phone"}
    contactos = [
        {
            "kind": ICONO.get(c["icon"], live.slugify(c["label"] or "otro")),
            "value": c["url"],
            "display_order": c["display_order"] + 1,
            "status": "published",
        }
        for c in live.contactos("es")
    ]

    seed = {
        "_generated_by": "tools/build_catalog_seed.py",
        "_source": "https://gambito93.pythonanywhere.com/portfolio/ (HTML en tools/live-html/)",
        "_legacy_seed": "content/catalog.seed.legacy.json",
        "profile": perfil,
        "projects": proyectos,
        "experiences": experiencias,
        "certifications": certificaciones,
        "education": educacion,
        "publications": publicaciones,
        "contacts": contactos,
    }
    SEED.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"escrito {SEED}")
    for clave in ("projects", "experiences", "certifications", "education", "publications", "contacts"):
        print(f"  {clave}: {len(seed[clave])}")
    if avisos:
        print("\navisos:")
        for a in avisos:
            print("  -", a)


if __name__ == "__main__":
    main()
