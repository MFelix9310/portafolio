"""Puertos de salida de la capa de aplicacion."""

from .clock import ClockPort
from .media_storage import MediaStoragePort, UploadTicket
from .revalidation import FrontendRevalidationPort, RevalidationResult

__all__ = [
    "ClockPort",
    "FrontendRevalidationPort",
    "MediaStoragePort",
    "RevalidationResult",
    "UploadTicket",
]
