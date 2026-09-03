"""Tests de los objetos de valor del dominio."""

from __future__ import annotations

from datetime import date

import pytest

from src.domain.value_objects.date_range import DateRange
from src.domain.value_objects.localized_text import LocalizedText
from src.domain.value_objects.publication_status import PublicationStatus
from src.domain.value_objects.slug import Slug
from src.domain.value_objects.taxonomy_keys import AreaKey, SubareaKey


class TestLocalizedText:
    def test_resuelve_el_locale_pedido(self) -> None:
        text = LocalizedText.of("Hola", "Hello")
        assert text.resolve("en") == "Hello"
        assert text.resolve("es") == "Hola"

    def test_cae_a_es_cuando_falta_la_traduccion(self) -> None:
        text = LocalizedText.of("Hola")
        assert text.resolve("en") == "Hola"
        assert text.resolve("fr") == "Hola"
        assert text.resolve(None) == "Hola"

    def test_es_es_obligatorio(self) -> None:
        with pytest.raises(ValueError):
            LocalizedText({"en": "Hello"})

    def test_descarta_traducciones_vacias(self) -> None:
        # El contenido heredado trae decenas de campos `_en` en blanco.
        text = LocalizedText({"es": "Hola", "en": "   "})
        assert text.locales == ("es",)
        assert text.resolve("en") == "Hola"

    def test_optional_devuelve_none_si_no_hay_nada(self) -> None:
        assert LocalizedText.optional(None) is None
        assert LocalizedText.optional({}) is None
        assert LocalizedText.optional({"es": ""}) is None
        assert LocalizedText.optional({"es": "x"}) is not None

    def test_es_inmutable_frente_al_mapa_original(self) -> None:
        source = {"es": "Hola"}
        text = LocalizedText(source)
        source["es"] = "Adios"
        assert text.resolve() == "Hola"


class TestSlug:
    @pytest.mark.parametrize("value", ["abc", "a-b-c", "proyecto-1"])
    def test_acepta_slugs_validos(self, value: str) -> None:
        assert Slug(value).value == value

    @pytest.mark.parametrize("value", ["", "Abc", "a--b", "-abc", "abc-", "a b", "ñ"])
    def test_rechaza_slugs_invalidos(self, value: str) -> None:
        with pytest.raises(ValueError):
            Slug(value)

    def test_deriva_slug_de_texto_con_acentos(self) -> None:
        assert Slug.from_text("Predicción de Pandeo!").value == "prediccion-de-pandeo"

    def test_falla_si_no_queda_nada_utilizable(self) -> None:
        with pytest.raises(ValueError):
            Slug.from_text("¡¿!?")


class TestDateRange:
    def test_rango_abierto(self) -> None:
        rango = DateRange(date(2022, 5, 24))
        assert rango.is_open
        assert rango.contains(date(2030, 1, 1))

    def test_rechaza_fin_anterior_al_inicio(self) -> None:
        with pytest.raises(ValueError):
            DateRange(date(2022, 5, 24), date(2021, 1, 1))

    def test_solapamiento(self) -> None:
        a = DateRange(date(2020, 1, 1), date(2022, 1, 1))
        b = DateRange(date(2021, 6, 1))
        assert a.overlaps(b) and b.overlaps(a)
        c = DateRange(date(2023, 1, 1), date(2023, 6, 1))
        assert not a.overlaps(c)


class TestPublicationStatus:
    def test_parse_y_visibilidad(self) -> None:
        assert PublicationStatus.parse("published").is_public
        assert not PublicationStatus.parse("draft").is_public
        assert PublicationStatus.parse(None) is PublicationStatus.DRAFT

    def test_rechaza_valores_fuera_del_contrato(self) -> None:
        with pytest.raises(ValueError):
            PublicationStatus.parse("archived")


class TestTaxonomyKeys:
    def test_valida_formato(self) -> None:
        assert AreaKey("civil-bim").value == "civil-bim"
        assert SubareaKey("bim").value == "bim"
        with pytest.raises(ValueError):
            AreaKey("Civil BIM")
