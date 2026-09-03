"""Ruta de un objeto en el almacen de media (addendum A4).

La convencion es vinculante y tiene una trampa: la ruta se guarda **con el prefijo
del bucket**, `media/projects/videos/1-1080.mp4`, pero la API de Storage recibe el
bucket por separado y espera la clave **sin** ese primer segmento. Los dos usos
conviven aqui para que ningun adaptador se invente su propia variante.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_BUCKET = "media"
PUBLIC_OBJECT_PREFIX = "storage/v1/object/public"


@dataclass(frozen=True, slots=True)
class StoragePath:
    """Ruta verbatim tal y como viaja por la base y por el JSON de respuesta."""

    value: str

    def __post_init__(self) -> None:
        cleaned = (self.value or "").strip().lstrip("/")
        if not cleaned:
            raise ValueError("storage path vacio")
        if "//" in cleaned or ".." in cleaned.split("/"):
            raise ValueError(f"storage path invalido: {self.value!r}")
        object.__setattr__(self, "value", cleaned)

    @property
    def bucket(self) -> str:
        head, _, tail = self.value.partition("/")
        return head if tail else DEFAULT_BUCKET

    @property
    def object_key(self) -> str:
        """Clave dentro del bucket: lo que espera la API de Storage."""
        _, _, tail = self.value.partition("/")
        return tail or self.value

    def public_url(self, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/{PUBLIC_OBJECT_PREFIX}/{self.value}"

    @classmethod
    def in_bucket(cls, bucket: str, object_key: str) -> "StoragePath":
        return cls(f"{bucket.strip('/')}/{object_key.lstrip('/')}")

    def __str__(self) -> str:
        return self.value


def public_url_of(storage_path: str | None, base_url: str) -> str | None:
    """Atajo para los presentadores: None entra, None sale."""
    if not storage_path:
        return None
    return StoragePath(storage_path).public_url(base_url)
