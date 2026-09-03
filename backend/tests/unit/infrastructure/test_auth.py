"""Verificacion de tokens.

Los tokens HS256 se firman de verdad con PyJWT: se comprueba que la firma, la
audiencia, el emisor y la caducidad se validan, no que exista una cabecera.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from src.infrastructure.auth.dev_token import DEV_USER_ID, DevTokenVerifier
from src.infrastructure.auth.identity import AuthError
from src.infrastructure.auth.supabase_jwt import SupabaseJwtVerifier

PROJECT_URL = "https://xyzcompany.supabase.co"
ISSUER = f"{PROJECT_URL}/auth/v1"
SECRET = "un-secreto-de-proyecto-suficientemente-largo"
USER_ID = "2f1c1a34-0d3a-4b2f-9a1e-7c9a1b2c3d4e"


def _token(*, secret: str = SECRET, **overrides) -> str:
    claims = {
        "sub": USER_ID,
        "aud": "authenticated",
        "iss": ISSUER,
        "role": "authenticated",
        "email": "felix@example.com",
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    claims.update(overrides)
    return jwt.encode(claims, secret, algorithm="HS256")


def _verifier(**overrides) -> SupabaseJwtVerifier:
    kwargs = {"project_url": PROJECT_URL, "jwt_secret": SECRET}
    kwargs.update(overrides)
    return SupabaseJwtVerifier(**kwargs)


class TestSupabaseJwtVerifier:
    async def test_token_valido(self) -> None:
        identity = await _verifier().verify(_token())
        assert identity.user_id == USER_ID
        assert identity.email == "felix@example.com"
        assert identity.issued_by == "supabase"

    async def test_firma_invalida(self) -> None:
        with pytest.raises(AuthError):
            await _verifier().verify(_token(secret="otro-secreto-distinto"))

    async def test_token_caducado(self) -> None:
        caducado = _token(exp=datetime.now(UTC) - timedelta(minutes=1))
        with pytest.raises(AuthError, match="caducado"):
            await _verifier().verify(caducado)

    async def test_audiencia_incorrecta(self) -> None:
        with pytest.raises(AuthError, match="[Aa]udiencia"):
            await _verifier().verify(_token(aud="otra-cosa"))

    async def test_emisor_incorrecto(self) -> None:
        with pytest.raises(AuthError, match="[Ee]misor"):
            await _verifier().verify(_token(iss="https://atacante.example/auth/v1"))

    async def test_token_sin_exp_se_rechaza(self) -> None:
        sin_exp = jwt.encode(
            {"sub": USER_ID, "aud": "authenticated", "iss": ISSUER}, SECRET, algorithm="HS256"
        )
        with pytest.raises(AuthError):
            await _verifier().verify(sin_exp)

    async def test_algoritmo_none_se_rechaza(self) -> None:
        # El ataque clasico: alg=none para saltarse la verificacion de firma.
        atacante = jwt.encode(
            {"sub": USER_ID, "aud": "authenticated", "iss": ISSUER}, None, algorithm="none"
        )
        with pytest.raises(AuthError, match="algoritmo no admitido"):
            await _verifier().verify(atacante)

    async def test_basura_no_es_un_token(self) -> None:
        with pytest.raises(AuthError):
            await _verifier().verify("no-es-un-jwt")

    async def test_hs256_sin_secreto_configurado(self) -> None:
        with pytest.raises(AuthError, match="SUPABASE_JWT_SECRET"):
            await _verifier(jwt_secret=None).verify(_token())

    async def test_lista_blanca_de_administradores(self) -> None:
        verifier = _verifier(admin_user_ids=frozenset({"otro-uuid"}))
        with pytest.raises(AuthError, match="no es administrador"):
            await verifier.verify(_token())

    async def test_lista_blanca_que_incluye_al_usuario(self) -> None:
        verifier = _verifier(admin_user_ids=frozenset({USER_ID}))
        assert (await verifier.verify(_token())).user_id == USER_ID

    def test_sin_url_de_proyecto_no_se_puede_construir(self) -> None:
        with pytest.raises(ValueError):
            SupabaseJwtVerifier(project_url="")


class TestDevTokenVerifier:
    async def test_token_correcto(self) -> None:
        identity = await DevTokenVerifier("secreto-dev").verify("secreto-dev")
        assert identity.user_id == DEV_USER_ID
        assert identity.issued_by == "dev"

    async def test_token_incorrecto(self) -> None:
        with pytest.raises(AuthError):
            await DevTokenVerifier("secreto-dev").verify("otro")

    async def test_sin_token_configurado_rechaza_todo(self) -> None:
        # Sin DEV_ADMIN_TOKEN el verificador no abre la puerta a nadie, ni con "".
        verifier = DevTokenVerifier("")
        with pytest.raises(AuthError, match="DEV_ADMIN_TOKEN"):
            await verifier.verify("")
        with pytest.raises(AuthError, match="DEV_ADMIN_TOKEN"):
            await verifier.verify("cualquier-cosa")
