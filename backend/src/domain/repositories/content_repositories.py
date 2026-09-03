"""Puertos de los recursos que comparten la firma generica del contrato."""

from __future__ import annotations

from ..entities.certification import Certification
from ..entities.contact import Contact
from ..entities.education import Education
from ..entities.experience import Experience
from ..entities.publication import Publication
from .base import ContentRepository


class ExperienceRepository(ContentRepository[Experience]):
    """list, get, save, delete, reorder."""


class CertificationRepository(ContentRepository[Certification]):
    """list, get, save, delete, reorder."""


class EducationRepository(ContentRepository[Education]):
    """list, get, save, delete, reorder."""


class PublicationRepository(ContentRepository[Publication]):
    """list, get, save, delete, reorder."""


class ContactRepository(ContentRepository[Contact]):
    """list, save, delete, reorder. `get` se hereda por coherencia del puerto."""
