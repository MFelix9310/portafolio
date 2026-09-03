"""URL firmada de subida para el panel.

El binario nunca atraviesa este backend: el panel sube directo al bucket con la URL
que devuelve el adaptador de storage.
"""

from __future__ import annotations

import posixpath
import re

from ...dto.commands import UploadUrlCommand
from ...errors import ValidationError
from ...ports.media_storage import MediaStoragePort, UploadTicket

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
ALLOWED_CONTENT_TYPE_PREFIXES = ("image/", "video/", "application/pdf")


class CreateUploadUrl:
    def __init__(self, storage: MediaStoragePort) -> None:
        self._storage = storage

    async def execute(self, command: UploadUrlCommand) -> UploadTicket:
        filename = command.filename.strip()
        # Se rechaza, no se sanea: un nombre con separadores o con '..' es un error
        # del cliente y silenciarlo con basename() esconderia el intento de escribir
        # fuera del prefijo del bucket.
        if not filename or filename != posixpath.basename(filename):
            raise ValidationError(
                f"el nombre de fichero no puede contener rutas: {command.filename!r}"
            )
        if not _SAFE_NAME_RE.match(filename) or filename in {'.', '..'}:
            raise ValidationError(f"nombre de fichero invalido: {command.filename!r}")
        content_type = command.content_type.strip().lower()
        if not content_type.startswith(ALLOWED_CONTENT_TYPE_PREFIXES):
            raise ValidationError(f"content_type no permitido: {content_type!r}")
        return await self._storage.create_upload_url(filename, content_type)
