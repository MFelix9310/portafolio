"""Adaptador de persistencia JSON: por defecto en desarrollo, sin infraestructura."""

from .repositories import (
    JsonContentRepository,
    JsonMediaRepository,
    JsonMessageRepository,
    JsonProfileRepository,
    JsonProjectRepository,
    JsonTaxonomyRepository,
)
from .store import JsonCatalogStore

__all__ = [
    "JsonCatalogStore",
    "JsonContentRepository",
    "JsonMediaRepository",
    "JsonMessageRepository",
    "JsonProfileRepository",
    "JsonProjectRepository",
    "JsonTaxonomyRepository",
]
