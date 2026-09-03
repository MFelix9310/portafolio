"""Slug: identificador estable y legible de una entidad publicable."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class Slug:
    """Minusculas ASCII con guiones, sin guiones dobles ni en los extremos."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _SLUG_RE.match(self.value):
            raise ValueError(f"slug invalido: {self.value!r}")

    @classmethod
    def from_text(cls, text: str, *, max_length: int = 80) -> "Slug":
        """Deriva un slug de texto libre; usado al crear contenido desde el panel."""
        normalized = unicodedata.normalize("NFKD", text)
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
        candidate = _NON_ALNUM_RE.sub("-", ascii_only).strip("-")[:max_length].strip("-")
        if not candidate:
            raise ValueError(f"no se puede derivar un slug de {text!r}")
        return cls(candidate)

    def __str__(self) -> str:
        return self.value
