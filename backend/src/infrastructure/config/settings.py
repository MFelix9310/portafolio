"""Configuracion del proceso: `from_env` + `validate`."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = BACKEND_ROOT.parent


class PersistenceBackend(StrEnum):
    JSON = "json"
    SUPABASE = "supabase"


class AuthBackend(StrEnum):
    DEV = "dev"
    SUPABASE = "supabase"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SettingsError(RuntimeError):
    """Configuracion incoherente. Aborta el arranque antes de servir nada."""


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _env_list(name: str, default: str = "") -> tuple[str, ...]:
    raw = _env(name, default)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name)
    return raw.lower() in {"1", "true", "yes", "on"} if raw else default


@dataclass(frozen=True, slots=True)
class Settings:
    environment: Environment = Environment.DEVELOPMENT
    persistence_backend: PersistenceBackend = PersistenceBackend.JSON
    auth_backend: AuthBackend = AuthBackend.DEV

    api_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = ()
    log_level: str = "INFO"

    # --- adaptador JSON ---
    seed_path: Path = REPO_ROOT / "content" / "catalog.seed.json"
    media_manifest_path: Path = REPO_ROOT / "content" / "media-manifest.json"
    json_write_path: Path = BACKEND_ROOT / "data" / "catalog.local.json"

    # Base publica de media. Debe valer lo mismo con json y con supabase: si cambia,
    # cambian las URLs del frontend al cambiar de adaptador (addendum A4).
    media_public_base_url: str = ""

    # --- Supabase ---
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "media"

    # --- auth ---
    supabase_jwt_secret: str = ""
    supabase_jwt_audience: str = "authenticated"
    admin_user_ids: frozenset[str] = field(default_factory=frozenset)
    dev_admin_token: str = ""

    # --- revalidacion ISR ---
    frontend_revalidate_url: str = ""
    frontend_revalidate_secret: str = ""

    @classmethod
    def from_env(cls, *, load_dotenv_file: bool = True) -> "Settings":
        if load_dotenv_file:
            load_dotenv(BACKEND_ROOT / ".env")
        seed = _env("CATALOG_SEED_PATH")
        manifest = _env("MEDIA_MANIFEST_PATH")
        write = _env("CATALOG_WRITE_PATH")
        return cls(
            environment=Environment(_env("ENVIRONMENT", "development").lower()),
            persistence_backend=PersistenceBackend(
                _env("PERSISTENCE_BACKEND", "json").lower()
            ),
            auth_backend=AuthBackend(_env("AUTH_BACKEND", "dev").lower()),
            api_prefix=_env("API_PREFIX", "/api/v1"),
            cors_origins=_env_list("CORS_ORIGINS", "http://localhost:3000"),
            log_level=_env("LOG_LEVEL", "INFO").upper(),
            seed_path=Path(seed) if seed else REPO_ROOT / "content" / "catalog.seed.json",
            media_manifest_path=(
                Path(manifest) if manifest else REPO_ROOT / "content" / "media-manifest.json"
            ),
            media_public_base_url=_env("MEDIA_PUBLIC_BASE_URL") or _env("SUPABASE_URL"),
            json_write_path=(
                Path(write) if write else BACKEND_ROOT / "data" / "catalog.local.json"
            ),
            supabase_url=_env("SUPABASE_URL"),
            supabase_anon_key=_env("SUPABASE_ANON_KEY"),
            supabase_service_role_key=_env("SUPABASE_SERVICE_ROLE_KEY"),
            supabase_storage_bucket=_env("SUPABASE_STORAGE_BUCKET", "media"),
            supabase_jwt_secret=_env("SUPABASE_JWT_SECRET"),
            supabase_jwt_audience=_env("SUPABASE_JWT_AUDIENCE", "authenticated"),
            admin_user_ids=frozenset(_env_list("ADMIN_USER_IDS")),
            dev_admin_token=_env("DEV_ADMIN_TOKEN"),
            frontend_revalidate_url=_env("FRONTEND_REVALIDATE_URL"),
            frontend_revalidate_secret=_env("FRONTEND_REVALIDATE_SECRET"),
        )

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION

    def validate(self) -> "Settings":
        """Aborta el arranque ante cualquier combinacion peligrosa o incompleta."""
        problems: list[str] = []

        # La barrera principal: un modo de auth de desarrollo en produccion es el
        # fallo que no queremos, asi que ni siquiera arranca.
        if self.is_production and self.auth_backend is AuthBackend.DEV:
            problems.append(
                "AUTH_BACKEND=dev es inadmisible con ENVIRONMENT=production; "
                "usa AUTH_BACKEND=supabase"
            )
        if self.is_production and self.persistence_backend is PersistenceBackend.JSON:
            problems.append(
                "PERSISTENCE_BACKEND=json es inadmisible con ENVIRONMENT=production; "
                "usa PERSISTENCE_BACKEND=supabase"
            )
        if self.auth_backend is AuthBackend.DEV and not self.dev_admin_token:
            problems.append("AUTH_BACKEND=dev exige DEV_ADMIN_TOKEN")
        if self.auth_backend is AuthBackend.SUPABASE and not self.supabase_url:
            problems.append("AUTH_BACKEND=supabase exige SUPABASE_URL")
        if self.persistence_backend is PersistenceBackend.SUPABASE:
            if not self.supabase_url:
                problems.append("PERSISTENCE_BACKEND=supabase exige SUPABASE_URL")
            if not self.supabase_service_role_key:
                problems.append(
                    "PERSISTENCE_BACKEND=supabase exige SUPABASE_SERVICE_ROLE_KEY"
                )
        if self.is_production and "*" in self.cors_origins:
            problems.append("CORS_ORIGINS=* es inadmisible en produccion")
        if not self.api_prefix.startswith("/"):
            problems.append("API_PREFIX debe empezar por '/'")
        if self.is_production and not self.media_public_base_url:
            problems.append(
                "MEDIA_PUBLIC_BASE_URL (o SUPABASE_URL) es obligatoria en produccion"
            )

        if problems:
            raise SettingsError(
                "configuracion invalida:\n  - " + "\n  - ".join(problems)
            )
        return self


__all__ = [
    "AuthBackend",
    "Environment",
    "PersistenceBackend",
    "Settings",
    "SettingsError",
]
