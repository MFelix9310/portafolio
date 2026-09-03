"""Storage de desarrollo: no sube nada, pero respeta la convencion de rutas.

Acompana al adaptador de persistencia JSON para que la API arranque y responda sin
ninguna infraestructura. Produce exactamente las mismas `storage_path` y `public_url`
que el adaptador de Supabase (addendum A4), de modo que cambiar `PERSISTENCE_BACKEND`
no mueve una sola URL del frontend. Nunca debe usarse en produccion: `Settings.validate()`
lo impide junto con el backend de persistencia.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from ...application.ports.media_storage import MediaStoragePort, UploadTicket
from ...domain.value_objects.storage_path import DEFAULT_BUCKET, StoragePath

SIGNED_URL_TTL = timedelta(minutes=15)


class LocalMediaStorage(MediaStoragePort):
    def __init__(
        self,
        public_base_url: str = "http://localhost:8000",
        bucket: str = DEFAULT_BUCKET,
    ) -> None:
        self._public_base_url = (public_base_url or "http://localhost:8000").rstrip("/")
        self._bucket = bucket
        self.deleted: list[str] = []
        self.issued: list[str] = []

    async def create_upload_url(self, filename: str, content_type: str) -> UploadTicket:
        path = StoragePath.in_bucket(
            self._bucket, f"uploads/{uuid.uuid4().hex[:12]}/{filename}"
        )
        self.issued.append(path.value)
        return UploadTicket(
            # No hay endpoint real de subida: el panel en modo dev no sube nada.
            upload_url=f"{self._public_base_url}/dev-upload/{path.object_key}",
            storage_path=path.value,
            public_url=self.public_url(path.value),
            expires_at=datetime.now(UTC) + SIGNED_URL_TTL,
            token=None,
        )

    def public_url(self, storage_path: str) -> str:
        return StoragePath(storage_path).public_url(self._public_base_url)

    async def delete(self, storage_path: str) -> bool:
        self.deleted.append(storage_path)
        return True
