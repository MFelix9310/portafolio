#!/usr/bin/env python3
"""Prueba de humo de RLS contra una instancia real de Supabase.

Ejecutalo UNA VEZ despues del primer `supabase db push`, y de nuevo cada vez que
toques una politica. Comprueba automaticamente lo que el README describia en prosa:
que `anon` no ve borradores, no ve sus medios ni sus subareas, no puede escribir en
ninguna tabla, puede insertar en `messages` pero no leerlos, y que el admin si ve
los borradores.

Se monta sus propios datos temporales (proyecto borrador, proyecto publicado, area
y subarea de prueba), los usa y los borra en un `finally`. **No toca tu contenido
real**: los intentos de escritura de `anon` van siempre contra las filas temporales,
nunca contra un proyecto tuyo.

Uso:
    export SUPABASE_URL="https://<ref>.supabase.co"
    export SUPABASE_ANON_KEY="<anon key>"
    export SUPABASE_ADMIN_EMAIL="tu@email"
    export SUPABASE_ADMIN_PASSWORD="..."
    # opcional, para la comprobacion 7 (usuario autenticado que NO es admin):
    export SUPABASE_TEST_EMAIL="prueba@email"
    export SUPABASE_TEST_PASSWORD="..."

    python supabase/rls_smoke_test.py

Sale con codigo 0 solo si todo pasa. Solo libreria estandar.

Usa la ANON key a proposito. Con la service_role saltarias RLS por diseno y
obtendrias un verde falso; por eso aqui no se usa en ningun momento.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any

TIMEOUT = 30
DENEGADO = (401, 403)


class SmokeError(RuntimeError):
    """Fallo de configuracion o de transporte: no es un fallo de politica."""


# ------------------------------------------------------------------- transporte


def _cuerpo(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode("utf-8", errors="replace")


def http(method: str, url: str, headers: dict, payload: Any = None) -> tuple:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, _cuerpo(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, _cuerpo(exc.read())
    except urllib.error.URLError as exc:
        raise SmokeError(f"{method} {url}: sin conexion ({exc.reason})") from exc


class Cliente:
    """Cliente PostgREST con una identidad concreta (anon, admin o usuario normal)."""

    def __init__(self, url: str, anon_key: str, token: str | None = None) -> None:
        self.rest = f"{url.rstrip('/')}/rest/v1"
        self.anon_key = anon_key
        self.token = token or anon_key

    def _cabeceras(self, extra: dict | None = None) -> dict:
        cabeceras = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if extra:
            cabeceras.update(extra)
        return cabeceras

    def get(self, consulta: str) -> tuple:
        return http("GET", f"{self.rest}/{consulta}", self._cabeceras())

    def post(self, tabla: str, filas: Any, devolver: bool = False) -> tuple:
        prefer = "return=representation" if devolver else "return=minimal"
        return http("POST", f"{self.rest}/{tabla}", self._cabeceras({"Prefer": prefer}), filas)

    def patch(self, consulta: str, payload: Any) -> tuple:
        return http("PATCH", f"{self.rest}/{consulta}", self._cabeceras(), payload)

    def delete(self, consulta: str) -> tuple:
        return http("DELETE", f"{self.rest}/{consulta}", self._cabeceras())


def iniciar_sesion(url: str, anon_key: str, email: str, password: str) -> str:
    estado, cuerpo = http(
        "POST",
        f"{url.rstrip('/')}/auth/v1/token?grant_type=password",
        {"apikey": anon_key, "Content-Type": "application/json"},
        {"email": email, "password": password},
    )
    if estado != 200 or not isinstance(cuerpo, dict) or "access_token" not in cuerpo:
        raise SmokeError(f"No se pudo iniciar sesion como {email}: {estado} {cuerpo}")
    return cuerpo["access_token"]


# ----------------------------------------------------------------------- fixtures


def crear_fixtures(admin: Cliente, sufijo: str) -> dict:
    """Datos temporales propios. Nada de esto toca el contenido real."""
    ctx: dict = {"sufijo": sufijo}

    estado, filas = admin.post(
        "projects",
        {
            "slug": f"zz-smoke-borrador-{sufijo}",
            "title": {"es": "Smoke test (borrador)"},
            "status": "draft",
        },
        devolver=True,
    )
    if estado not in (200, 201) or not filas:
        raise SmokeError(
            f"El admin no pudo crear el proyecto de prueba: {estado} {filas}. "
            "Revisa que tu usuario este en admin_users."
        )
    ctx["borrador"] = filas[0]

    estado, filas = admin.post(
        "projects",
        {
            "slug": f"zz-smoke-publicado-{sufijo}",
            "title": {"es": "Smoke test (publicado)"},
            "status": "published",
        },
        devolver=True,
    )
    if estado not in (200, 201) or not filas:
        raise SmokeError(f"No se pudo crear el proyecto publicado de prueba: {estado} {filas}")
    ctx["publicado"] = filas[0]

    # Un medio colgado del proyecto borrador.
    admin.post(
        "project_media",
        {
            "project_id": ctx["borrador"]["id"],
            "kind": "image",
            "storage_path": f"media/zz-smoke/{sufijo}.webp",
        },
    )

    # Enlace a una subarea REAL y publicada: asi lo unico que puede ocultar la fila
    # de project_subareas es el estado del proyecto, no el de la subarea.
    estado, subareas = admin.get("subareas?select=id&status=eq.published&limit=1")
    if estado != 200 or not subareas:
        raise SmokeError(
            "No hay ninguna subarea publicada; falta aplicar las migraciones de taxonomia."
        )
    admin.post(
        "project_subareas",
        {"project_id": ctx["borrador"]["id"], "subarea_id": subareas[0]["id"]},
    )

    # Area y subarea temporales para la comprobacion de taxonomia.
    estado, filas = admin.post(
        "areas",
        {
            "key": f"zz-smoke-area-{sufijo}",
            "name": {"es": "Area de prueba"},
            "status": "draft",
        },
        devolver=True,
    )
    if estado not in (200, 201) or not filas:
        raise SmokeError(
            f"No se pudo crear el area de prueba: {estado} {filas}. "
            "Si el error menciona la columna 'status', falta aplicar "
            "20260829090000_taxonomia_status.sql."
        )
    ctx["area"] = filas[0]

    estado, filas = admin.post(
        "subareas",
        {
            "area_id": ctx["area"]["id"],
            "key": f"zz-smoke-sub-{sufijo}",
            "name": {"es": "Subarea de prueba"},
            "status": "published",
        },
        devolver=True,
    )
    if estado not in (200, 201) or not filas:
        raise SmokeError(f"No se pudo crear la subarea de prueba: {estado} {filas}")
    ctx["subarea"] = filas[0]

    ctx["email_mensaje"] = f"zz-smoke-{sufijo}@example.invalid"
    return ctx


def borrar_fixtures(admin: Cliente, ctx: dict) -> list:
    """Limpieza. Devuelve lo que no se pudo borrar, para avisar en pantalla."""
    restos = []
    objetivos = [
        ("proyecto borrador", f"projects?id=eq.{ctx.get('borrador', {}).get('id')}"),
        ("proyecto publicado", f"projects?id=eq.{ctx.get('publicado', {}).get('id')}"),
        ("proyecto intruso", f"projects?slug=eq.zz-smoke-intruso-{ctx.get('sufijo')}"),
        ("area de prueba", f"areas?id=eq.{ctx.get('area', {}).get('id')}"),
        ("mensaje de prueba", f"messages?email=eq.{ctx.get('email_mensaje')}"),
    ]
    for etiqueta, consulta in objetivos:
        if "None" in consulta:
            continue
        estado, cuerpo = admin.delete(consulta)
        if estado not in (200, 204):
            restos.append(f"{etiqueta} ({estado} {cuerpo})")
    return restos


# ---------------------------------------------------------------- comprobaciones


def c1_anon_no_ve_borradores(anon: Cliente, ctx: dict) -> tuple:
    slug_b = ctx["borrador"]["slug"]
    slug_p = ctx["publicado"]["slug"]
    estado, borrador = anon.get(f"projects?slug=eq.{slug_b}&select=slug,status")
    estado_p, publicado = anon.get(f"projects?slug=eq.{slug_p}&select=slug,status")

    if estado != 200:
        return False, f"la lectura publica de projects fallo: {estado} {borrador}"
    if borrador:
        return False, f"anon VE el borrador {slug_b}: {borrador}"
    # Control: si tampoco viera el publicado, el vacio de arriba no probaria nada.
    if estado_p != 200 or len(publicado or []) != 1:
        return False, f"anon no ve el proyecto publicado (control roto): {estado_p} {publicado}"
    return True, "anon ve el publicado y no ve el borrador"


def c2_anon_no_ve_hijos_de_borrador(anon: Cliente, ctx: dict) -> tuple:
    pid = ctx["borrador"]["id"]
    e1, medios = anon.get(f"project_media?project_id=eq.{pid}&select=storage_path")
    e2, enlaces = anon.get(f"project_subareas?project_id=eq.{pid}&select=subarea_id")
    if e1 != 200 or e2 != 200:
        return False, f"lectura fallida: project_media {e1}, project_subareas {e2}"
    if medios:
        return False, f"anon VE los medios de un borrador: {medios}"
    if enlaces:
        return False, f"anon VE las subareas de un borrador: {enlaces}"
    return True, "medios y subareas del borrador ocultos"


def c3_anon_no_escribe(anon: Cliente, admin: Cliente, ctx: dict) -> tuple:
    slug_p = ctx["publicado"]["slug"]
    sufijo = ctx["sufijo"]
    intentos = {
        "insert": anon.post(
            "projects", {"slug": f"zz-smoke-intruso-{sufijo}", "title": {"es": "intruso"}}
        )[0],
        "update": anon.patch(f"projects?slug=eq.{slug_p}", {"status": "draft"})[0],
        "delete": anon.delete(f"projects?slug=eq.{slug_p}")[0],
    }

    # Verificacion real: mire lo que mire el codigo HTTP, nada puede haber cambiado.
    estado, filas = admin.get(f"projects?slug=eq.{slug_p}&select=slug,status")
    if estado != 200 or len(filas or []) != 1:
        return False, f"anon BORRO el proyecto publicado (intentos: {intentos})"
    if filas[0]["status"] != "published":
        return False, f"anon MODIFICO el proyecto publicado (intentos: {intentos})"
    _, intrusos = admin.get(f"projects?slug=eq.zz-smoke-intruso-{sufijo}&select=slug")
    if intrusos:
        return False, f"anon INSERTO una fila (intentos: {intentos})"

    no_denegados = {op: cod for op, cod in intentos.items() if cod not in DENEGADO}
    if no_denegados:
        return True, (
            f"sin efecto en la base, pero estos no devolvieron 401/403: {no_denegados} "
            "(revisa los grants)"
        )
    return True, f"insert/update/delete rechazados con {sorted(set(intentos.values()))}"


def c4_anon_inserta_mensajes(anon: Cliente, ctx: dict) -> tuple:
    estado, cuerpo = anon.post(
        "messages",
        {
            "name": "Smoke test",
            "email": ctx["email_mensaje"],
            "subject": "Prueba de RLS",
            "body": "Insertado por supabase/rls_smoke_test.py",
        },
    )
    if estado not in (200, 201, 204):
        return False, f"el formulario de contacto NO funciona para anon: {estado} {cuerpo}"
    return True, f"anon puede insertar en messages ({estado})"


def c5_anon_no_lee_mensajes(anon: Cliente, ctx: dict) -> tuple:
    estado, cuerpo = anon.get("messages?select=email,body")
    if estado in DENEGADO:
        return True, f"lectura de messages rechazada ({estado})"
    if estado == 200 and cuerpo == []:
        return True, "lectura de messages devuelve vacio"
    return False, f"anon LEE messages: {estado} {cuerpo}"


def c6_admin_ve_borradores(admin: Cliente, ctx: dict) -> tuple:
    slug_b = ctx["borrador"]["slug"]
    estado, filas = admin.get(f"projects?slug=eq.{slug_b}&select=slug,status")
    if estado != 200:
        return False, f"la lectura del admin fallo: {estado} {filas}"
    if len(filas or []) != 1 or filas[0]["status"] != "draft":
        return False, (
            f"el admin NO ve su propio borrador ({filas}). Falta la politica "
            "*_select_admin: el panel seria inutil."
        )
    return True, "el admin ve el borrador"


def c7_usuario_no_admin_no_escribe(usuario: Cliente, admin: Cliente, ctx: dict) -> tuple:
    sufijo = ctx["sufijo"]
    slug = f"zz-smoke-intruso-{sufijo}"
    estado, cuerpo = usuario.post("projects", {"slug": slug, "title": {"es": "intruso"}})
    _, intrusos = admin.get(f"projects?slug=eq.{slug}&select=slug")
    if intrusos:
        return False, "un usuario autenticado que NO esta en admin_users pudo insertar"
    if estado not in DENEGADO:
        return True, f"sin efecto, pero devolvio {estado} en vez de 401/403: {cuerpo}"
    return True, f"usuario autenticado no-admin rechazado ({estado})"


def c8_taxonomia_por_status(anon: Cliente, admin: Cliente, ctx: dict) -> tuple:
    area_id, area_key = ctx["area"]["id"], ctx["area"]["key"]
    sub_id, sub_key = ctx["subarea"]["id"], ctx["subarea"]["key"]

    # El area nace 'draft' y su subarea 'published': ninguna debe verse.
    _, areas = anon.get(f"areas?key=eq.{area_key}&select=key")
    _, subs = anon.get(f"subareas?key=eq.{sub_key}&select=key")
    if areas:
        return False, f"anon VE un area en borrador: {areas}"
    if subs:
        return False, "anon VE una subarea publicada cuya area esta en borrador (chip huerfano)"

    # Publicando el area, ambas aparecen.
    admin.patch(f"areas?id=eq.{area_id}", {"status": "published"})
    _, areas = anon.get(f"areas?key=eq.{area_key}&select=key")
    _, subs = anon.get(f"subareas?key=eq.{sub_key}&select=key")
    if len(areas or []) != 1 or len(subs or []) != 1:
        return False, f"tras publicar el area, anon no las ve: areas={areas} subareas={subs}"

    # Despublicando solo la subarea, desaparece ella y el area sigue.
    admin.patch(f"subareas?id=eq.{sub_id}", {"status": "draft"})
    _, subs = anon.get(f"subareas?key=eq.{sub_key}&select=key")
    if subs:
        return False, "anon VE una subarea en borrador"
    _, vista_admin = admin.get(f"subareas?id=eq.{sub_id}&select=key,status")
    if len(vista_admin or []) != 1:
        return False, "el admin no ve la subarea que acaba de despublicar"
    return True, "areas y subareas respetan status, y la subarea hereda el del area"


# ---------------------------------------------------------------------------- main


def entorno(nombre: str, obligatoria: bool = True) -> str:
    valor = os.environ.get(nombre, "").strip()
    if obligatoria and not valor:
        raise SmokeError(f"Falta la variable de entorno {nombre}.")
    return valor


def preparar() -> tuple:
    url = entorno("SUPABASE_URL").rstrip("/")
    anon_key = entorno("SUPABASE_ANON_KEY")
    admin_email = entorno("SUPABASE_ADMIN_EMAIL")
    admin_password = entorno("SUPABASE_ADMIN_PASSWORD")
    test_email = entorno("SUPABASE_TEST_EMAIL", obligatoria=False)
    test_password = entorno("SUPABASE_TEST_PASSWORD", obligatoria=False)

    if "service_role" in anon_key:
        raise SmokeError(
            "SUPABASE_ANON_KEY parece ser la service_role: saltaria RLS y daria un falso verde."
        )

    print(f"Instancia: {url}\n")
    anon = Cliente(url, anon_key)
    admin = Cliente(url, anon_key, iniciar_sesion(url, anon_key, admin_email, admin_password))
    usuario = None
    if test_email and test_password:
        usuario = Cliente(url, anon_key, iniciar_sesion(url, anon_key, test_email, test_password))
    return anon, admin, usuario


def main() -> int:
    try:
        anon, admin, usuario = preparar()
        ctx = crear_fixtures(admin, uuid.uuid4().hex[:8])
    except SmokeError as exc:
        print(f"ERROR DE CONFIGURACION: {exc}", file=sys.stderr)
        return 2

    comprobaciones = [
        ("anon no ve borradores", lambda: c1_anon_no_ve_borradores(anon, ctx)),
        (
            "anon no ve medios ni subareas de un borrador",
            lambda: c2_anon_no_ve_hijos_de_borrador(anon, ctx),
        ),
        ("anon no puede escribir", lambda: c3_anon_no_escribe(anon, admin, ctx)),
        ("anon puede insertar en messages", lambda: c4_anon_inserta_mensajes(anon, ctx)),
        ("anon no puede leer messages", lambda: c5_anon_no_lee_mensajes(anon, ctx)),
        ("el admin si ve borradores", lambda: c6_admin_ve_borradores(admin, ctx)),
        (
            "usuario autenticado no-admin no escribe",
            (lambda: c7_usuario_no_admin_no_escribe(usuario, admin, ctx)) if usuario else None,
        ),
        ("areas y subareas respetan status", lambda: c8_taxonomia_por_status(anon, admin, ctx)),
    ]

    fallos = omitidas = correctas = 0
    try:
        for indice, (nombre, funcion) in enumerate(comprobaciones, start=1):
            if funcion is None:
                omitidas += 1
                print(f"{indice}. OMITIDA {nombre}")
                print("            define SUPABASE_TEST_EMAIL y SUPABASE_TEST_PASSWORD")
                continue
            try:
                ok, detalle = funcion()
            except SmokeError as exc:
                ok, detalle = False, str(exc)
            if ok:
                correctas += 1
                print(f"{indice}. OK      {nombre}")
            else:
                fallos += 1
                print(f"{indice}. FALLO   {nombre}")
            print(f"            {detalle}")
    finally:
        restos = borrar_fixtures(admin, ctx)
        if restos:
            print("\nAVISO: no se pudieron borrar estos datos de prueba:")
            for resto in restos:
                print(f"  {resto}")
            print("  Busca las filas cuyo slug o key empiece por 'zz-smoke-' y borralas a mano.")

    ejecutadas = correctas + fallos
    resumen = f"\nRESUMEN: {correctas}/{ejecutadas} OK"
    print(resumen + (f", {omitidas} omitida(s)" if omitidas else ""))
    if fallos:
        print("Hay politicas RLS que NO se comportan como dice el contrato. No publiques asi.")
        return 1
    if omitidas:
        print("Todo lo ejecutado pasa, pero quedan comprobaciones sin cubrir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
