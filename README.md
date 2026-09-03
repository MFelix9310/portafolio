# Portafolio — Félix Ruiz M.

Reemplazo del portafolio Django/Bootstrap anterior. Backend Python hexagonal,
frontend Next.js con dirección de arte propia, contenido editable desde un panel
sin tocar código.

> **Posicionamiento**: *Ingeniero que automatiza — de obra a datos.*

## Mapa del repositorio

```
backend/    FastAPI + arquitectura hexagonal (dominio sin framework)
web/        Next.js App Router + Tailwind + GSAP/ScrollTrigger + Lenis
supabase/   migraciones, políticas RLS y cargador del seed
content/    contenido real exportado del sitio antiguo + copy por ruta
tools/      exportador de contenido legacy y pipeline de media
docs/       decisiones de arquitectura, dirección de arte y contrato de datos
```

## Documentos que mandan

Léelos antes de tocar nada; el código se somete a ellos, no al revés.

| Documento | Qué fija |
|---|---|
| [`docs/00-decisiones.md`](docs/00-decisiones.md) | Por qué FastAPI y no Node, la regla de dependencia, Supabase como adaptador, la estrategia de vídeo |
| [`docs/01-direccion-de-arte.md`](docs/01-direccion-de-arte.md) | La idea "Cota": tipografía, paleta, retícula y los cuatro gestos de movimiento |
| [`docs/02-contrato-datos.md`](docs/02-contrato-datos.md) | Tablas, políticas RLS, endpoints y puertos del dominio |

## Contenido

`content/catalog.seed.json` **no se edita a mano**. Se genera desde el portafolio
desplegado en producción:

```bash
python tools/scrape_live_portfolio.py   # descarga las 33 paginas, ES y EN
python tools/build_catalog_seed.py      # reconstruye el catalogo
python tools/verify_catalog_seed.py     # comprueba que no falta nada
```

Contiene 23 proyectos, 3 experiencias, 4 certificaciones, 6 estudios, 1
publicación y 3 contactos, todos reales.

> El seed original salió de `db.sqlite3` del repo de GitHub y estaba
> desactualizado: traía 6 proyectos y 1 experiencia. Queda como
> `content/catalog.seed.legacy.json` para poder diferenciar. Los 6 proyectos
> heredados siguen todos en el catálogo nuevo.

La única subárea sin contenido es `civil-bim/bim`: el trabajo BIM está en las
experiencias de 8base y Upwork, no hay ningún proyecto publicado de eso. Se
puebla desde el panel de administración.

## Media

Los vídeos heredados eran screencasts a ~8 Mbps. El pipeline los recodifica y
normaliza los nombres (los originales llevaban tildes y espacios, que rompen las
claves de Storage):

```bash
cd tools/media && npm install
node transcode.mjs   # vídeo: 217.5 MB -> 26.1 MB, dos renditions + póster
node images.mjs      # imágenes: 2.7 MB -> 0.9 MB en WebP, nombres normalizados
node manifest.mjs    # escribe content/media-manifest.json
```

## Supabase

El proyecto en la nube **no está creado**: se trabaja contra el stack local y las
migraciones se aplican al proyecto propio cuando exista. Ver
[`supabase/README.md`](supabase/README.md).
