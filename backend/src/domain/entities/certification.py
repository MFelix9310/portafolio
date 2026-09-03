"""Certificacion profesional."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ..value_objects.localized_text import LocalizedText
from ..value_objects.publication_status import PublicationStatus
from ..value_objects.slug import Slug


@dataclass(slots=True)
class Certification:
    slug: Slug
    name: LocalizedText
    issuer: LocalizedText
    issued_on: date
    id: UUID | None = None
    description: LocalizedText | None = None
    expires_on: date | None = None
    credential_url: str | None = None
    certificate_path: str | None = None
    legacy_id: int | None = None
    status: PublicationStatus = PublicationStatus.DRAFT
    display_order: int = 0

    def __post_init__(self) -> None:
        if self.expires_on is not None and self.expires_on < self.issued_on:
            raise ValueError("expires_on anterior a issued_on")

    def is_expired_on(self, moment: date) -> bool:
        return self.expires_on is not None and moment > self.expires_on
