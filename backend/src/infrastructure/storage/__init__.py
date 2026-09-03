"""Adaptadores de salida no relacionales: storage, revalidacion y reloj."""

from .local_storage import LocalMediaStorage
from .revalidation import HttpFrontendRevalidation, NoopRevalidation
from .supabase_storage import SupabaseMediaStorage
from .system_clock import SystemClock

__all__ = [
    "HttpFrontendRevalidation",
    "LocalMediaStorage",
    "NoopRevalidation",
    "SupabaseMediaStorage",
    "SystemClock",
]
