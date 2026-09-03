"""Claves de area y subarea.

El contrato fija la semilla ('data', 'developer', 'civil-bim' y sus subareas) pero
tambien expone `POST /admin/areas` y `POST /admin/subareas`. Un Enum cerrado haria
imposible crecer sin migrar codigo, asi que estas claves se validan por forma
(mismo formato que un slug) y la semilla queda como constantes de clase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class AreaKey:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _KEY_RE.match(self.value):
            raise ValueError(f"area key invalida: {self.value!r}")

    def __str__(self) -> str:
        return self.value


# Constantes de la semilla. Se asignan fuera de la clase para que `dataclass` no las
# confunda con campos.
AREA_DATA = AreaKey("data")
AREA_DEVELOPER = AreaKey("developer")
AREA_CIVIL_BIM = AreaKey("civil-bim")

SEED_AREA_KEYS: tuple[AreaKey, ...] = (AREA_DATA, AREA_DEVELOPER, AREA_CIVIL_BIM)


@dataclass(frozen=True, slots=True)
class SubareaKey:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _KEY_RE.match(self.value):
            raise ValueError(f"subarea key invalida: {self.value!r}")

    def __str__(self) -> str:
        return self.value


# Semilla del contrato. La unicidad real es (area_id, key) en base de datos.
SEED_SUBAREA_KEYS: dict[str, tuple[str, ...]] = {
    "data": ("analyst", "scientist", "engineer"),
    "developer": ("fullstack", "backend", "desktop"),
    "civil-bim": ("structural", "geotechnical", "bim", "construction"),
}


@dataclass(frozen=True, slots=True)
class TaxonomyTag:
    """Pertenencia de un proyecto a un par area+subarea (tabla project_subareas)."""

    area: AreaKey
    subarea: SubareaKey

    @classmethod
    def of(cls, area: str, subarea: str) -> "TaxonomyTag":
        return cls(AreaKey(area), SubareaKey(subarea))
