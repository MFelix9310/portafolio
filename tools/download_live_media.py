"""Descarga a `tools/media/live/` los ficheros de media que referencia el seed.

Se conserva la ruta relativa tal cual (`projects/images/1_ab.png`) porque es la
clave con la que `catalog.seed.json` referencia el media y con la que
`tools/media/manifest.mjs` construye el manifiesto.

Los 404 se registran y se listan al final; no se silencian.

Colisiones de mayusculas: el sitio publica `projects/MINIATURA.jpg` y
`projects/miniatura.jpg` como dos ficheros distintos. En NTFS son el mismo
nombre, asi que el segundo se guarda como `miniatura~1.jpg` y la equivalencia
queda en `tools/media/live/_casemap.json`, que leen `images.mjs` y `manifest.mjs`
para reconstruir la ruta real del sitio.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://gambito93.pythonanywhere.com/media/"
DESTINO = RAIZ / "tools" / "media" / "live"
INFORME = RAIZ / "tools" / "media" / "live-download.json"

sys.path.insert(0, str(RAIZ / "tools"))
from verify_catalog_seed import rutas_media  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    seed = json.loads((RAIZ / "content" / "catalog.seed.json").read_text(encoding="utf-8"))
    referencias = rutas_media(seed)

    ok: list[dict] = []
    fallos: list[dict] = []
    reservados: dict[str, str] = {}   # ruta local en minusculas -> ruta del sitio
    casemap: dict[str, str] = {}      # ruta local -> ruta del sitio (solo si difieren)

    for ruta in sorted(referencias):
        # NTFS no distingue mayusculas: si otra ruta del sitio ya ocupo este
        # nombre, se desambigua en disco y se anota la equivalencia.
        local = ruta
        if reservados.get(local.lower(), ruta) != ruta:
            base, punto, ext = ruta.rpartition(".")
            n = 1
            while reservados.get(f"{base}~{n}{punto}{ext}".lower(), ruta) != ruta:
                n += 1
            local = f"{base}~{n}{punto}{ext}"
            casemap[local] = ruta
            print(f"  colision de mayusculas: {ruta} -> {local}")
        reservados[local.lower()] = ruta

        destino = DESTINO / local
        url = BASE + urllib.parse.quote(ruta)
        if destino.exists() and destino.stat().st_size > 0:
            ok.append({"path": ruta, "local": local, "bytes": destino.stat().st_size, "cached": True})
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        try:
            peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(peticion, timeout=180) as respuesta:
                datos = respuesta.read()
            destino.write_bytes(datos)
            ok.append({"path": ruta, "local": local, "bytes": len(datos), "cached": False})
            print(f"  ok   {ruta}  ({len(datos)/1024:.0f} KB)")
        except urllib.error.HTTPError as error:
            fallos.append({"path": ruta, "url": url, "status": error.code,
                           "referenced_by": referencias[ruta]})
            print(f"  {error.code}  {ruta}")
        except Exception as error:
            fallos.append({"path": ruta, "url": url, "status": str(error),
                           "referenced_by": referencias[ruta]})
            print(f"  fallo {ruta}: {error}")
        time.sleep(0.15)

    total = sum(x["bytes"] for x in ok)
    (DESTINO / "_casemap.json").write_text(
        json.dumps(casemap, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    INFORME.write_text(
        json.dumps({"ok": ok, "fallos": fallos, "casemap": casemap}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n{len(ok)} descargados ({total/1024/1024:.1f} MB), {len(fallos)} fallos")
    for f in fallos:
        print(f"  ! {f['status']}  {f['path']}  <- {', '.join(f['referenced_by'])}")
    print(f"informe: {INFORME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
