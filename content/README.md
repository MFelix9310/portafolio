# content/

Catálogo del portafolio. Todo lo de esta carpeta se genera desde el sitio
desplegado en <https://gambito93.pythonanywhere.com/portfolio/>, no desde el
`db.sqlite3` del repo de GitHub, que está desactualizado.

| Archivo | Qué es |
|---|---|
| `catalog.seed.json` | Catálogo vivo. Lo genera `tools/build_catalog_seed.py`. |
| `catalog.seed.legacy.json` | El seed anterior, salido de `db.sqlite3` (6 proyectos, 1 experiencia). Se conserva **solo para diferenciar** y demostrar que no se perdió nada. No lo consume nadie. |
| `media-manifest.json` | Mapa `ruta del sitio → clave de Supabase Storage`. Lo genera `tools/media/manifest.mjs`. |
| `media-manifest.legacy.json` | El manifiesto del media heredado, por el mismo motivo que el seed legacy. |
| `live-portfolio.json` | Índice de las 33 páginas descargadas del sitio en vivo, con la ruta al HTML crudo de cada una en `tools/live-html/`. |
| `copy/` | Copy estático del sitio. Ver su propio README. |

## Cómo se regenera

```bash
python tools/scrape_live_portfolio.py     # descarga HTML crudo (es + en)
python tools/build_catalog_seed.py        # reconstruye catalog.seed.json
python tools/download_live_media.py       # baja el media a tools/media/live/
cd tools/media
node images.mjs    live out/images
node transcode.mjs live/projects/videos out/videos
node manifest.mjs  live out
cd ../..
python tools/verify_catalog_seed.py       # falla ruidosamente si algo no cuadra
```

El idioma **no** se selecciona con la cookie `django_language`: el sitio usa
`/set-language/?lang=xx` y lo guarda en sesión. El scraper mantiene un cookie jar
por idioma. Si esto se rompe, todas las páginas «en» vuelven a salir en
castellano sin avisar.

---

## Taxonomía: criterio de asignación

Las áreas y subáreas válidas son las de `docs/02-contrato-datos.md` §A13:

| área | subáreas |
|---|---|
| `data` | `analyst`, `scientist`, `engineer` |
| `developer` | `fullstack`, `backend`, `desktop` |
| `civil-bim` | `structural`, `geotechnical`, `bim`, `construction` |

La asignación vive en `TAXONOMIA` dentro de `tools/build_catalog_seed.py`, con
una línea de justificación por proyecto en `JUSTIFICACION`, para poder auditarla
y corregirla desde el panel sin adivinar por qué está donde está.

### Regla por subárea

- **`data/engineer`** — hay un *pipeline* real: ingesta de una fuente externa,
  transformación por capas y una salida consumible. No basta con «usa pandas».
- **`data/scientist`** — hay un modelo entrenado y métricas de validación
  reportadas (R², precisión, Brier, ROC AUC…).
- **`data/analyst`** — el entregable es análisis, *reporting* o exploración sobre
  datos, no un modelo desplegado.
- **`developer/fullstack`** — aplicación web con frontend y backend propios.
- **`developer/backend`** — hay capa de servidor, ORM o persistencia con lógica
  de negocio, la sirva un navegador o no.
- **`developer/desktop`** — se entrega como aplicación de escritorio (PySide6,
  PyQt5/6). Se separó de `backend` porque llamar «backend» a una GUI empaquetada
  con PyInstaller era inexacto.
- **`civil-bim/structural`** — el problema es cálculo o comportamiento
  estructural: pandeo, esfuerzos, resistencia, respuesta sísmica.
- **`civil-bim/geotechnical`** — suelos y ensayos de campo (CPT, SPT).
- **`civil-bim/construction`** — planificación, costos y gestión de obra.
- **`civil-bim/bim`** — modelado BIM e interoperabilidad IFC.

### El cruce civil + data es deliberado

Los gemelos digitales sísmicos (18, 20), los predictores de resistencia de
hormigón (15) y de carga última en acero (13, 14), el pandeo (10, 22) y los
campos de esfuerzos con GNN (19) están en `civil-bim` **y** en `data` a la vez.
No es una clasificación indecisa: es el argumento del portafolio. Aplanarlos a
una sola área destruye justo lo que los diferencia.

### Reparto resultante

| área/subárea | nº | proyectos (id del sitio en vivo) |
|---|---:|---|
| `data/analyst` | 4 | 13, 17, 24, 28 |
| `data/scientist` | 16 | 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 26, 27, 29 |
| `data/engineer` | 4 | 26, 27, 28, 29 |
| `developer/fullstack` | 2 | 8, 17 |
| `developer/backend` | 3 | 7, 8, 17 |
| `developer/desktop` | 8 | 7, 9, 12, 15, 16, 23, 24, 25 |
| `civil-bim/structural` | 12 | 10, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 29 |
| `civil-bim/geotechnical` | 1 | 24 |
| `civil-bim/bim` | **0** | — |
| `civil-bim/construction` | 2 | 16, 25 |

**`civil-bim/bim` se queda sin proyectos, y es correcto.** El trabajo BIM del
portafolio está en las experiencias, no en los proyectos publicados: 8base
(Computer Vision → IFC, desde octubre 2025) y Upwork (Revit API, Dynamo, IFC).
Si más adelante se publica un proyecto BIM, esta es la subárea que lo espera.
El estado vacío que ya contempla `copy/copy.es.json`
(`areas.civil_bim.empty_state`) sigue siendo necesario.

---

## Anomalías del sitio en vivo

Se reproducen tal cual, sin corregirlas en silencio. Cada una es arreglable
desde el panel de administración.

1. **Educación id 2 tiene título e institución intercambiados.** El sitio
   muestra «Universidad Internacional SEK» como título y «Maestría en Salud y
   Seguridad Ocupacional…» como institución. El seed viejo los tenía al derecho
   para este registro (y al revés para el id 6, que en el vivo está bien). El
   seed nuevo copia lo que muestra el sitio.
2. **Proyecto 8 (PetShop ADM) apunta a un repositorio equivocado.** El sitio
   enlaza `MFelix9310/REGISTROS_LABS`, que es el repo del proyecto 7. El seed
   viejo tenía `MFelix9310/PETSHOP_ADM`. Se emite lo que está publicado: la
   instrucción es no deducir URLs.
3. **`created_at` no existe para 17 de los 23 proyectos.** El sitio no publica
   la fecha de creación en ninguna página. Los 6 proyectos que ya venían del
   seed viejo la conservan; los 17 nuevos quedan a `null`. Si el orden de la
   parrilla depende de esta columna, hay que apoyarse en `display_order`, que sí
   refleja el orden real de la parrilla en vivo.
4. **Fechas con precisión de mes.** El sitio renderiza «octubre 2025», sin día.
   Afecta a `experiences[2].start_date`, `experiences[3].start_date` y a
   `certifications[3].issued_on` y `[4].issued_on`, que quedan en el día 1. Los
   registros que ya existían en el seed viejo conservan su día exacto.
5. **`copy/copy.es.json` y `copy.en.json` solo tienen entrada de `projects` para
   los 6 slugs antiguos.** Faltan 17. No se han tocado: son traducción
   profesional, no se generan.
6. **Tres miniaturas distintas se llaman igual salvo por las mayúsculas.**
   `projects/MINIATURA.jpg` (proyecto 16), `projects/Miniatura.png`
   (proyecto 8) y `projects/miniatura.jpg` (proyecto 15). Las dos `.jpg`
   chocan además en NTFS, así que la descarga las separa con `_casemap.json`;
   y las tres chocan en la clave de Storage, porque `slugify` pasa a
   minúsculas. El manifiesto emite `projects/miniatura.webp`,
   `miniatura-2.webp` y `miniatura-3.webp`. Sin esa desambiguación se perdían
   dos de las tres miniaturas en silencio. Renombrarlas desde el panel elimina
   la trampa para siempre.

## Extensiones de esquema

Respecto a `catalog.seed.legacy.json`, solo hay una adición, y es aditiva (nada
que leyera el esquema anterior se rompe):

- `experiences[].images[]` — el sitio en vivo publica galería en las
  experiencias (la de 8base tiene una imagen). El esquema heredado no la
  contemplaba y omitirla habría perdido el archivo.

En `media-manifest.json`, las entradas de GIF animado llevan además
`animated`, `frames` y `video`. Siguen siendo `kind: "image"` y entran en un
`<img>` tal cual; `video` es una rendition H.264 opcional, mucho más ligera,
para quien pueda usar `<video autoplay loop muted playsinline>`.
