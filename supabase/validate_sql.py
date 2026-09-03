"""Valida la sintaxis de las migraciones sin levantar ningun servidor (D7).

Dos parsers, con pesos distintos:

  pglast   -> libpg_query, el parser REAL de Postgres. Es el que manda: si falla,
              el fichero no se aplicaria. Un error aqui es un error de verdad.
  sqlglot  -> segunda opinion, en Python puro. Su cobertura de DDL de Postgres
              (create policy, do $$...$$, grants) es parcial, asi que sus quejas
              se reportan como aviso y no tumban la validacion.

Esto valida SINTAXIS, no comportamiento. Que un fichero parsee no dice nada sobre
si una politica RLS deja pasar lo que debe. Ver la lista de comprobacion manual
en supabase/README.md.

Uso:
    python supabase/validate_sql.py
    python supabase/validate_sql.py --strict-sqlglot   # sqlglot tambien tumba
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def validar_pglast(sql: str) -> str | None:
    """None si parsea; el mensaje de error si no."""
    try:
        import pglast
    except ImportError:
        return "SKIP: pglast no instalado (pip install pglast)"
    try:
        pglast.parse_sql(sql)
    except Exception as exc:  # pglast.parser.ParseError y derivados
        return f"{type(exc).__name__}: {exc}"
    return None


def validar_sqlglot(sql: str) -> tuple[str | None, int, int]:
    """(error, sentencias, sentencias_no_entendidas).

    sqlglot degrada a `exp.Command` lo que no sabe parsear (create policy, do $$,
    grant...) en vez de fallar. Esas sentencias NO quedan validadas por sqlglot,
    asi que se cuentan y se reportan: decir "OK" sobre ellas seria mentir.
    """
    try:
        import sqlglot
        from sqlglot import expressions as exp
    except ImportError:
        return "SKIP: sqlglot no instalado (pip install sqlglot)", 0, 0
    # sqlglot avisa por logger de cada degradacion; el recuento ya lo dice.
    logging.getLogger("sqlglot").setLevel(logging.ERROR)
    try:
        arbol = sqlglot.parse(sql, dialect="postgres")
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}", 0, 0
    degradadas = sum(1 for s in arbol if isinstance(s, exp.Command))
    return None, len(arbol), degradadas


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida la sintaxis de supabase/migrations.")
    parser.add_argument(
        "--strict-sqlglot",
        action="store_true",
        help="tratar los avisos de sqlglot como errores",
    )
    args = parser.parse_args()

    ficheros = sorted(MIGRATIONS.glob("*.sql"))
    if not ficheros:
        print(f"ERROR: no hay migraciones en {MIGRATIONS}", file=sys.stderr)
        return 1

    fallos = 0
    total_sentencias = 0
    total_degradadas = 0

    for fichero in ficheros:
        sql = fichero.read_text(encoding="utf-8")

        error_pg = validar_pglast(sql)
        if error_pg and not error_pg.startswith("SKIP:"):
            print(f"FALLO   {fichero.name}\n        pglast: {error_pg}", file=sys.stderr)
            fallos += 1
            continue

        error_sg, _, degradadas = validar_sqlglot(sql)
        if error_sg and not error_sg.startswith("SKIP:"):
            destino = sys.stderr if args.strict_sqlglot else sys.stdout
            etiqueta = "FALLO  " if args.strict_sqlglot else "AVISO  "
            print(f"{etiqueta} {fichero.name}\n        sqlglot: {error_sg}", file=destino)
            fallos += int(args.strict_sqlglot)
            continue

        sentencias = _contar_sentencias(sql)
        total_sentencias += sentencias
        total_degradadas += degradadas
        detalle = f"{sentencias} sentencias"
        if degradadas:
            detalle += f", {degradadas} que sqlglot no valida (solo pglast)"
        print(f"OK      {fichero.name} ({detalle})")

    print(f"\n{len(ficheros)} ficheros, {total_sentencias} sentencias, {fallos} fallos.")
    if total_degradadas:
        print(
            f"{total_degradadas} sentencias (create policy, grant, do $$...$$) las valida "
            "solo pglast: sqlglot no cubre ese DDL."
        )
    print("Esto es SINTAXIS. El comportamiento de RLS no queda probado:")
    print("ver la lista de comprobacion de supabase/README.md tras el primer db push.")
    return 1 if fallos else 0


def _contar_sentencias(sql: str) -> int:
    try:
        import pglast

        return len(pglast.parse_sql(sql))
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
