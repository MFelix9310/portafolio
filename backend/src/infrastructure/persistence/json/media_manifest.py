"""Traduce las rutas heredadas a `storagePath` usando `content/media-manifest.json`.

Sin esto el adaptador JSON serviria las rutas del sitio antiguo
(`projects/videos/1.mp4`) y el de Supabase las del bucket
(`media/projects/videos/1-1080.mp4`): el mismo endpoint devolveria media distinta
segun el adaptador y el argumento hexagonal se quedaria en el papel. El manifiesto
es la unica fuente de esa correspondencia (addendum A4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class MediaEntry:
    kind: str
    storage_path: str
    poster_path: str | None = None
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    renditions: dict[str, dict[str, Any]] = field(default_factory=dict)


class MediaManifest:
    """Mapa `ruta heredada -> destino en Storage`. Vacio si no hay manifiesto."""

    def __init__(self, entries: dict[str, MediaEntry] | None = None) -> None:
        self._entries = entries or {}

    def __bool__(self) -> bool:
        return bool(self._entries)

    @classmethod
    def load(cls, path: Path | None) -> "MediaManifest":
        if path is None or not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries: dict[str, MediaEntry] = {}
        for legacy_path, item in (payload.get("entries") or {}).items():
            entries[legacy_path] = MediaEntry(
                kind=item.get("kind", "image"),
                storage_path=item["storagePath"],
                poster_path=item.get("posterPath"),
                duration_seconds=item.get("durationSeconds"),
                width=item.get("width"),
                height=item.get("height"),
                renditions={
                    label: {"path": data["storagePath"], "bytes": data.get("bytes", 0)}
                    for label, data in (item.get("renditions") or {}).items()
                },
            )
        return cls(entries)

    def entry(self, legacy_path: str | None) -> MediaEntry | None:
        return self._entries.get(legacy_path) if legacy_path else None

    def path(self, legacy_path: str | None) -> str | None:
        """Ruta final de un fichero suelto. Si no esta en el manifiesto, se conserva."""
        if not legacy_path:
            return None
        entry = self._entries.get(legacy_path)
        return entry.storage_path if entry else legacy_path
