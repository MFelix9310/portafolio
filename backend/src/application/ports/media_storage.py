"""Puerto de almacenamiento de media.

Es una salida de aplicacion, no del dominio: el dominio no sabe que existen ficheros
subidos. Hoy lo implementa Supabase Storage; manana puede ser Bunny o Cloudflare
Stream sin tocar dominio ni casos de uso (D6).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UploadTicket:
    """Todo lo que el panel necesita para subir un fichero sin pasar por el backend."""

    upload_url: str
    storage_path: str
    public_url: str
    expires_at: datetime
    token: str | None = None


class MediaStoragePort(ABC):
    @abstractmethod
    async def create_upload_url(self, filename: str, content_type: str) -> UploadTicket:
        """URL firmada de subida. El backend nunca recibe el binario."""

    @abstractmethod
    def public_url(self, storage_path: str) -> str:
        """URL de lectura publica del bucket."""

    @abstractmethod
    async def delete(self, storage_path: str) -> bool: ...
