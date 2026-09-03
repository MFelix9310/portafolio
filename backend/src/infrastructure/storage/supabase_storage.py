"""Adaptador de Supabase Storage para MediaStoragePort.

Convencion A4: la ruta viaja y se guarda con el prefijo del bucket
(`media/projects/...`), pero la API de Storage recibe el bucket por separado y
espera la clave sin ese primer segmento. `StoragePath` es quien conoce las dos caras.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from supabase import AsyncClient

from ...application.errors import StorageError
from ...application.ports.media_storage import MediaStoragePort, UploadTicket
from ...domain.value_objects.storage_path import StoragePath

SIGNED_URL_TTL = timedelta(minutes=15)


class SupabaseMediaStorage(MediaStoragePort):
    def __init__(self, client: AsyncClient, bucket: str, public_base_url: str) -> None:
        self._client = client
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")

    def _bucket_api(self):
        return self._client.storage.from_(self._bucket)

    async def create_upload_url(self, filename: str, content_type: str) -> UploadTicket:
        # Prefijo aleatorio: dos subidas con el mismo nombre no deben pisarse.
        path = StoragePath.in_bucket(
            self._bucket, f"uploads/{uuid.uuid4().hex[:12]}/{filename}"
        )
        try:
            response = await self._bucket_api().create_signed_upload_url(path.object_key)
        except Exception as exc:  # storage3 lanza sus propios tipos de error
            raise StorageError(f"no se pudo firmar la subida: {exc}") from exc
        payload = response if isinstance(response, dict) else {}
        return UploadTicket(
            upload_url=payload.get("signed_url") or payload.get("signedURL", ""),
            storage_path=path.value,
            public_url=self.public_url(path.value),
            expires_at=datetime.now(UTC) + SIGNED_URL_TTL,
            token=payload.get("token"),
        )

    def public_url(self, storage_path: str) -> str:
        return StoragePath(storage_path).public_url(self._public_base_url)

    async def delete(self, storage_path: str) -> bool:
        try:
            await self._bucket_api().remove([StoragePath(storage_path).object_key])
        except Exception as exc:
            raise StorageError(f"no se pudo borrar {storage_path}: {exc}") from exc
        return True
