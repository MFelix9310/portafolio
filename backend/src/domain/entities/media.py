"""Recursos multimedia asociados a un proyecto (tabla project_media)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from ..value_objects.localized_text import LocalizedText


class MediaKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"

    @classmethod
    def parse(cls, raw: str) -> "MediaKind":
        try:
            return cls(str(raw).strip().lower())
        except ValueError as exc:
            raise ValueError(f"kind de media invalido: {raw!r}") from exc


@dataclass(frozen=True, slots=True)
class Rendition:
    """Salida de tools/media para un vinculo de calidad concreto (D6)."""

    label: str
    path: str
    bytes: int

    def __post_init__(self) -> None:
        if self.bytes < 0:
            raise ValueError("renditions.bytes no puede ser negativo")


@dataclass(slots=True)
class MediaAsset:
    kind: MediaKind
    storage_path: str
    id: UUID | None = None
    project_id: UUID | None = None
    poster_path: str | None = None
    caption: LocalizedText | None = None
    title: LocalizedText | None = None
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    renditions: tuple[Rendition, ...] = field(default_factory=tuple)
    display_order: int = 0

    def __post_init__(self) -> None:
        if not self.storage_path.strip():
            raise ValueError("storage_path es obligatorio")
        if self.kind is MediaKind.VIDEO and self.poster_path is None:
            # No es un error: el poster puede llegar despues de transcodificar.
            pass

    def rendition(self, label: str) -> Rendition | None:
        return next((r for r in self.renditions if r.label == label), None)
