"""Incorpora un proyecto destacado desde `content/incoming/<slug>/`.

Cada carpeta trae dos ficheros escritos a mano o por un agente de capturas:

* `project.json`  ficha del proyecto en el formato del catalogo.
* `captures.json` capturas con su pie de foto y cual es la portada.

El script convierte las imagenes a WebP con el mismo criterio que
`tools/media/images.mjs`, las registra en `content/media-manifest.json` con la
convencion de rutas del contrato A4, y hace upsert del proyecto en
`content/catalog.seed.json`. Es idempotente: se puede repetir.

    python tools/ingest_incoming.py            # todas las carpetas
    python tools/ingest_incoming.py built-roster
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
INCOMING = RAIZ / "content" / "incoming"
CATALOGO = RAIZ / "content" / "catalog.seed.json"
MANIFIESTO = RAIZ / "content" / "media-manifest.json"
SALIDA_IMG = RAIZ / "tools" / "media" / "out" / "images"

# ffmpeg viene con el paquete de tools/media; se reutiliza en vez de pedir uno global.
FFMPEG = RAIZ / "tools" / "media" / "node_modules" / "ffmpeg-static" / "ffmpeg.exe"


def cargar(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def guardar(path: pathlib.Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def a_webp(origen: pathlib.Path, destino: pathlib.Path) -> int:
    """WebP calidad 82 con tope de 1920 px de ancho, como el resto del catalogo."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(FFMPEG), "-y", "-i", str(origen),
            "-vf", "scale='min(1920,iw)':-2:flags=lanczos",
            "-c:v", "libwebp", "-quality", "82",
            str(destino),
        ],
        check=True,
        capture_output=True,
    )
    return destino.stat().st_size


def ingerir(carpeta: pathlib.Path) -> dict:
    slug = carpeta.name
    proyecto = cargar(carpeta / "project.json")
    capturas = cargar(carpeta / "captures.json")

    catalogo = cargar(CATALOGO)
    manifiesto = cargar(MANIFIESTO)
    entradas = manifiesto["entries"]

    portada = capturas.get("thumbnail")
    imagenes: list[dict] = []
    antes = despues = 0

    for orden, shot in enumerate(sorted(capturas["shots"], key=lambda s: s.get("order", 0))):
        origen = carpeta / shot["file"]
        if not origen.is_file():
            raise SystemExit(f"falta {origen}")

        nombre = pathlib.Path(shot["file"]).stem + ".webp"
        # Ruta heredada: la clave con la que el catalogo referencia esta imagen.
        legacy = f"projects/{slug}/{shot['file']}"
        storage = f"projects/{slug}/{nombre}"
        destino = SALIDA_IMG / storage

        antes += origen.stat().st_size
        despues += a_webp(origen, destino)

        entradas[legacy] = {
            "kind": "image",
            "storagePath": f"media/{storage}",
            "localFile": str(pathlib.Path("out") / "images" / storage),
            "bytes": destino.stat().st_size,
        }
        if shot["file"] != portada:
            imagenes.append({"path": legacy, "caption": shot.get("caption"), "order": orden})

    proyecto = dict(proyecto)
    # Un proyecto puede entrar sin capturas todavia: el texto ya vale por si
    # solo y la miniatura se anade despues sin tocar la ficha.
    proyecto["thumbnail"] = f"projects/{slug}/{portada}" if portada else None
    proyecto["images"] = imagenes
    proyecto.setdefault("videos", [])
    proyecto.setdefault("documents", [])
    proyecto.setdefault("legacy_id", None)
    proyecto.setdefault("created_at", None)

    # Upsert por slug, conservando el orden del resto.
    proyectos = [p for p in catalogo["projects"] if p["slug"] != slug]
    proyectos.append(proyecto)
    proyectos.sort(key=lambda p: (p.get("display_order", 0), p["slug"]))
    catalogo["projects"] = proyectos

    guardar(CATALOGO, catalogo)
    guardar(MANIFIESTO, manifiesto)
    return {"slug": slug, "imagenes": len(capturas["shots"]), "antes": antes, "despues": despues}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pedidos = sys.argv[1:]
    carpetas = [
        d for d in sorted(INCOMING.iterdir())
        if d.is_dir() and (d / "project.json").is_file() and (not pedidos or d.name in pedidos)
    ]
    if not carpetas:
        raise SystemExit("nada que ingerir en content/incoming")

    for carpeta in carpetas:
        r = ingerir(carpeta)
        mb = lambda b: b / 1024 / 1024
        print(f"{r['slug']}: {r['imagenes']} imagenes, {mb(r['antes']):.1f} MB -> {mb(r['despues']):.1f} MB")

    total = len(cargar(CATALOGO)["projects"])
    print(f"catalogo: {total} proyectos")


if __name__ == "__main__":
    main()
