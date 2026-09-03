"""Estado de publicacion. El contrato solo admite estos dos valores."""

from __future__ import annotations

from enum import StrEnum


class PublicationStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"

    @classmethod
    def parse(cls, raw: str | None) -> "PublicationStatus":
        if raw is None:
            return cls.DRAFT
        try:
            return cls(str(raw).strip().lower())
        except ValueError as exc:
            raise ValueError(f"status invalido: {raw!r}") from exc

    @property
    def is_public(self) -> bool:
        return self is PublicationStatus.PUBLISHED
