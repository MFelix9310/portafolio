"""Texto multilingue con fallback obligatorio a espanol (D5)."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

DEFAULT_LOCALE = "es"


@dataclass(frozen=True, slots=True)
class LocalizedText:
    """Mapa locale -> texto. `es` es obligatorio; el resto es opcional."""

    translations: Mapping[str, str]

    def __post_init__(self) -> None:
        cleaned = {
            locale: text.strip()
            for locale, text in dict(self.translations).items()
            if isinstance(text, str) and text.strip()
        }
        if DEFAULT_LOCALE not in cleaned:
            raise ValueError("LocalizedText requiere al menos el locale 'es'")
        object.__setattr__(self, "translations", MappingProxyType(cleaned))

    @classmethod
    def of(cls, es: str, en: str | None = None) -> "LocalizedText":
        payload = {DEFAULT_LOCALE: es}
        if en:
            payload["en"] = en
        return cls(payload)

    @classmethod
    def optional(cls, translations: Mapping[str, str] | None) -> "LocalizedText | None":
        """Devuelve None en vez de reventar cuando el campo entero es opcional."""
        if not translations:
            return None
        if not any(str(v).strip() for v in translations.values()):
            return None
        return cls(translations)

    # El mapa interno es un MappingProxyType, que `copy.deepcopy` no sabe replicar.
    # Como el objeto es inmutable, compartirlo es correcto y ademas evita copias.
    def __copy__(self) -> "LocalizedText":
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> "LocalizedText":
        return self

    def __reduce__(self) -> tuple[object, tuple[dict[str, str]]]:
        return (LocalizedText, (dict(self.translations),))

    def resolve(self, locale: str | None = None) -> str:
        """Texto en el locale pedido, cayendo a 'es' si no existe traduccion."""
        if locale and locale in self.translations:
            return self.translations[locale]
        return self.translations[DEFAULT_LOCALE]

    def has(self, locale: str) -> bool:
        return locale in self.translations

    @property
    def locales(self) -> tuple[str, ...]:
        return tuple(sorted(self.translations))

    def to_dict(self) -> dict[str, str]:
        return dict(self.translations)
