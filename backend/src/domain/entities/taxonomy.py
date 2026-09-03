"""Areas y subareas: la unica taxonomia del catalogo (D4).

Las tres areas son fijas: `/data`, `/developer` y `/civil-bim` son rutas del App
Router del front. Crear un area desde el panel produciria un area sin ruta que la
renderice, asi que el dominio no ofrece forma de crearla ni de borrarla. Solo se
edita su contenido y su visibilidad. Las subareas si crecen libremente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ..value_objects.localized_text import LocalizedText
from ..value_objects.publication_status import PublicationStatus
from ..value_objects.taxonomy_keys import AreaKey, SubareaKey


@dataclass(slots=True)
class Subarea:
    key: SubareaKey
    name: LocalizedText
    area_key: AreaKey
    id: UUID | None = None
    area_id: UUID | None = None
    display_order: int = 0


@dataclass(slots=True)
class Area:
    key: AreaKey
    name: LocalizedText
    id: UUID | None = None
    blurb: LocalizedText | None = None
    display_order: int = 0
    # Un area despublicada oculta su ruta del sitio; util para `civil-bim` mientras
    # no tenga proyectos. Por defecto publicada: las tres existen desde el dia uno.
    status: PublicationStatus = PublicationStatus.PUBLISHED
    subareas: tuple[Subarea, ...] = field(default_factory=tuple)

    def subarea(self, key: SubareaKey) -> Subarea | None:
        return next((s for s in self.subareas if s.key == key), None)
