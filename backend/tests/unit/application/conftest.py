"""Fixture de repositorios parametrizada por adaptador.

El mismo conjunto de tests de casos de uso corre contra los dos adaptadores. El de
JSON se ejecuta siempre; el de Supabase se salta si no hay credenciales, pero el
codigo del test es identico. Que ninguno de estos tests sepa cual esta debajo es la
prueba ejecutable de que el dominio no depende de la infraestructura.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import pytest

from src.infrastructure.persistence import serialization as ser
from src.infrastructure.persistence.json.repositories import (
    JsonContentRepository,
    JsonMediaRepository,
    JsonMessageRepository,
    JsonProfileRepository,
    JsonProjectRepository,
    JsonTaxonomyRepository,
)
from src.infrastructure.persistence.json.store import JsonCatalogStore

UNIFORM = (
    ("experiences", ser.experience_from_row, ser.experience_to_row),
    ("certifications", ser.certification_from_row, ser.certification_to_row),
    ("education", ser.education_from_row, ser.education_to_row),
    ("publications", ser.publication_from_row, ser.publication_to_row),
    ("contacts", ser.contact_from_row, ser.contact_to_row),
)

SUPABASE_READY = bool(
    os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY")
) and os.getenv("RUN_SUPABASE_TESTS", "").lower() in {"1", "true", "yes"}


@dataclass(slots=True)
class RepositoryBundle:
    backend: str
    projects: Any
    profile: Any
    messages: Any
    taxonomy: Any
    media: Any
    content: dict[str, Any]


def _json_bundle(tmp_path: Path) -> RepositoryBundle:
    # Sin seed y con un fichero de escritura nuevo: el store arranca vacio pero con
    # la taxonomia del contrato ya sembrada.
    store = JsonCatalogStore(seed_path=None, write_path=tmp_path / "catalog.local.json")
    return RepositoryBundle(
        backend="json",
        projects=JsonProjectRepository(store),
        profile=JsonProfileRepository(store),
        messages=JsonMessageRepository(store),
        taxonomy=JsonTaxonomyRepository(store),
        media=JsonMediaRepository(store),
        content={
            name: JsonContentRepository(store, name, to_entity, to_row)
            for name, to_entity, to_row in UNIFORM
        },
    )


async def _supabase_bundle() -> RepositoryBundle:
    from src.infrastructure.persistence.supabase.client import create_supabase_client
    from src.infrastructure.persistence.supabase.repositories import (
        SupabaseContentRepository,
        SupabaseMediaRepository,
        SupabaseMessageRepository,
        SupabaseProfileRepository,
        SupabaseProjectRepository,
        SupabaseTaxonomyRepository,
    )

    client = await create_supabase_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    return RepositoryBundle(
        backend="supabase",
        projects=SupabaseProjectRepository(client),
        profile=SupabaseProfileRepository(client),
        messages=SupabaseMessageRepository(client),
        taxonomy=SupabaseTaxonomyRepository(client),
        media=SupabaseMediaRepository(client),
        content={
            name: SupabaseContentRepository(client, name, to_entity, to_row)
            for name, to_entity, to_row in UNIFORM
        },
    )


@pytest.fixture(
    params=[
        pytest.param("json", id="json"),
        pytest.param(
            "supabase",
            id="supabase",
            marks=pytest.mark.skipif(
                not SUPABASE_READY,
                reason="sin credenciales de Supabase (define RUN_SUPABASE_TESTS=1)",
            ),
        ),
    ]
)
async def repos(request: pytest.FixtureRequest, tmp_path: Path) -> AsyncIterator[RepositoryBundle]:
    if request.param == "json":
        yield _json_bundle(tmp_path)
        return
    yield await _supabase_bundle()
