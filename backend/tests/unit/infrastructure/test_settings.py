"""Vallas de `Settings.validate()`.

La mas importante: un modo de auth de desarrollo colandose en produccion.
"""

from __future__ import annotations

import pytest

from src.infrastructure.config.settings import (
    AuthBackend,
    Environment,
    PersistenceBackend,
    Settings,
    SettingsError,
)


def _settings(**overrides) -> Settings:
    base = {
        "environment": Environment.DEVELOPMENT,
        "persistence_backend": PersistenceBackend.JSON,
        "auth_backend": AuthBackend.DEV,
        "dev_admin_token": "token-de-desarrollo",
        "cors_origins": ("http://localhost:3000",),
    }
    return Settings(**{**base, **overrides})


class TestProductionFences:
    def test_auth_dev_en_produccion_aborta_el_arranque(self) -> None:
        settings = _settings(
            environment=Environment.PRODUCTION,
            persistence_backend=PersistenceBackend.SUPABASE,
            supabase_url="https://x.supabase.co",
            supabase_service_role_key="k",
            media_public_base_url="https://x.supabase.co",
        )
        with pytest.raises(SettingsError) as exc:
            settings.validate()
        assert "AUTH_BACKEND=dev" in str(exc.value)

    def test_persistencia_json_en_produccion_aborta(self) -> None:
        settings = _settings(
            environment=Environment.PRODUCTION,
            auth_backend=AuthBackend.SUPABASE,
            supabase_url="https://x.supabase.co",
            media_public_base_url="https://x.supabase.co",
        )
        with pytest.raises(SettingsError) as exc:
            settings.validate()
        assert "PERSISTENCE_BACKEND=json" in str(exc.value)

    def test_cors_abierto_en_produccion_aborta(self) -> None:
        settings = _settings(
            environment=Environment.PRODUCTION,
            auth_backend=AuthBackend.SUPABASE,
            persistence_backend=PersistenceBackend.SUPABASE,
            supabase_url="https://x.supabase.co",
            supabase_service_role_key="k",
            media_public_base_url="https://x.supabase.co",
            cors_origins=("*",),
        )
        with pytest.raises(SettingsError) as exc:
            settings.validate()
        assert "CORS_ORIGINS" in str(exc.value)

    def test_produccion_bien_configurada_pasa(self) -> None:
        settings = _settings(
            environment=Environment.PRODUCTION,
            auth_backend=AuthBackend.SUPABASE,
            persistence_backend=PersistenceBackend.SUPABASE,
            supabase_url="https://x.supabase.co",
            supabase_service_role_key="service-role",
            media_public_base_url="https://x.supabase.co",
            cors_origins=("https://felixruiz.dev",),
        )
        assert settings.validate() is settings

    def test_el_error_acumula_todos_los_problemas(self) -> None:
        settings = _settings(
            environment=Environment.PRODUCTION,
            cors_origins=("*",),
            dev_admin_token="",
        )
        with pytest.raises(SettingsError) as exc:
            settings.validate()
        message = str(exc.value)
        assert "AUTH_BACKEND=dev" in message
        assert "PERSISTENCE_BACKEND=json" in message
        assert "CORS_ORIGINS" in message


class TestDevelopmentDefaults:
    def test_por_defecto_json_y_dev(self) -> None:
        settings = Settings()
        assert settings.persistence_backend is PersistenceBackend.JSON
        assert settings.auth_backend is AuthBackend.DEV
        assert not settings.is_production

    def test_auth_dev_sin_token_no_arranca(self) -> None:
        with pytest.raises(SettingsError) as exc:
            _settings(dev_admin_token="").validate()
        assert "DEV_ADMIN_TOKEN" in str(exc.value)

    def test_persistencia_supabase_exige_credenciales(self) -> None:
        with pytest.raises(SettingsError) as exc:
            _settings(persistence_backend=PersistenceBackend.SUPABASE).validate()
        message = str(exc.value)
        assert "SUPABASE_URL" in message
        assert "SUPABASE_SERVICE_ROLE_KEY" in message

    def test_desarrollo_por_defecto_es_valido(self) -> None:
        assert _settings().validate() is not None
