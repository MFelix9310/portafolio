"""Adaptador de persistencia Supabase: el de produccion."""

from .client import create_supabase_client
from .repositories import (
    SupabaseContentRepository,
    SupabaseMediaRepository,
    SupabaseMessageRepository,
    SupabaseProfileRepository,
    SupabaseProjectRepository,
    SupabaseTaxonomyRepository,
)

__all__ = [
    "SupabaseContentRepository",
    "SupabaseMediaRepository",
    "SupabaseMessageRepository",
    "SupabaseProfileRepository",
    "SupabaseProjectRepository",
    "SupabaseTaxonomyRepository",
    "create_supabase_client",
]
