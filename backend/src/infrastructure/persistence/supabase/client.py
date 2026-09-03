"""Cliente Supabase. Unico punto del backend que conoce la libreria."""

from __future__ import annotations

from typing import Any

from supabase import AsyncClient, acreate_client


async def create_supabase_client(url: str, service_role_key: str) -> AsyncClient:
    """El backend usa la service_role key; nunca sale de aqui (contrato, RLS)."""
    if not url or not service_role_key:
        raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY son obligatorias")
    return await acreate_client(url, service_role_key)


def rows_of(response: Any) -> list[dict[str, Any]]:
    """PostgREST devuelve `data`; normaliza el caso de respuesta vacia."""
    return list(getattr(response, "data", None) or [])


def first_row(response: Any) -> dict[str, Any] | None:
    rows = rows_of(response)
    return rows[0] if rows else None
