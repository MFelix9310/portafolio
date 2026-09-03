"""Almacen JSON en proceso.

Lee de `content/catalog.seed.json` la primera vez y a partir de ahi trabaja sobre un
fichero local escribible. El seed nunca se modifica: es contenido versionado del repo.
"""

from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from .seed_loader import empty_catalog, load_seed


class JsonCatalogStore:
    """Estado compartido por todos los repositorios JSON.

    El lock protege el ciclo leer-modificar-escribir; sin el, dos peticiones
    concurrentes del panel podrian perder una escritura.
    """

    def __init__(
        self,
        *,
        seed_path: Path | None,
        write_path: Path | None,
        manifest_path: Path | None = None,
    ) -> None:
        self._write_path = write_path
        self._lock = threading.RLock()
        self._data = self._bootstrap(seed_path, write_path, manifest_path)

    @staticmethod
    def _bootstrap(
        seed_path: Path | None,
        write_path: Path | None,
        manifest_path: Path | None,
    ) -> dict[str, Any]:
        if write_path is not None and write_path.exists():
            return json.loads(write_path.read_text(encoding="utf-8"))
        if seed_path is not None and seed_path.exists():
            return load_seed(seed_path, manifest_path)
        return empty_catalog()

    # ------------------------------------------------------------------ lectura

    def collection(self, name: str) -> list[dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._data.get(name) or [])

    def singleton(self, name: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._data.get(name)
            return copy.deepcopy(value) if value else None

    # ----------------------------------------------------------------- escritura

    def upsert(self, name: str, row: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            rows = self._data.setdefault(name, [])
            stored = copy.deepcopy(row)
            if not stored.get("id"):
                stored["id"] = str(uuid4())
            for index, existing in enumerate(rows):
                if existing.get("id") == stored["id"]:
                    rows[index] = stored
                    break
            else:
                rows.append(stored)
            self._flush()
            return copy.deepcopy(stored)

    def remove(self, name: str, row_id: UUID) -> bool:
        with self._lock:
            rows = self._data.setdefault(name, [])
            target = str(row_id)
            remaining = [row for row in rows if row.get("id") != target]
            if len(remaining) == len(rows):
                return False
            self._data[name] = remaining
            self._flush()
            return True

    def replace_collection(self, name: str, rows: list[dict[str, Any]]) -> None:
        with self._lock:
            self._data[name] = copy.deepcopy(rows)
            self._flush()

    def set_singleton(self, name: str, row: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            stored = copy.deepcopy(row)
            if not stored.get("id"):
                stored["id"] = str(uuid4())
            self._data[name] = stored
            self._flush()
            return copy.deepcopy(stored)

    def _flush(self) -> None:
        if self._write_path is None:
            return
        self._write_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._write_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # Reemplazo atomico: un fallo a mitad de escritura no deja el catalogo roto.
        temporary.replace(self._write_path)
