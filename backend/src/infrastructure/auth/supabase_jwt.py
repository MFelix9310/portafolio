"""Verificacion real del JWT de Supabase.

Dos modos, ambos con verificacion criptografica de la firma:

- Proyectos con claves asimetricas (ES256/RS256): se resuelve la clave publica en el
  JWKS del proyecto y se cachea por TTL, indexando por `kid`.
- Proyectos legacy (HS256): se verifica con el secreto compartido del proyecto.

En los dos casos se comprueban firma, `aud` y `exp`. No hay ninguna rama que acepte
un token por el mero hecho de existir.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from .identity import AdminIdentity, AdminTokenVerifier, AuthError

ASYMMETRIC_ALGORITHMS = ("ES256", "RS256")
JWKS_CACHE_TTL_SECONDS = 600
REQUEST_TIMEOUT = httpx.Timeout(5.0, connect=2.0)


class SupabaseJwtVerifier(AdminTokenVerifier):
    def __init__(
        self,
        *,
        project_url: str,
        audience: str = "authenticated",
        jwt_secret: str | None = None,
        admin_user_ids: frozenset[str] = frozenset(),
    ) -> None:
        if not project_url:
            raise ValueError("SUPABASE_URL es obligatoria para verificar tokens")
        self._issuer = f"{project_url.rstrip('/')}/auth/v1"
        self._jwks_url = f"{self._issuer}/.well-known/jwks.json"
        self._audience = audience
        self._jwt_secret = jwt_secret or None
        self._admin_user_ids = admin_user_ids
        self._jwk_client: PyJWKClient | None = None
        self._jwk_client_loaded_at = 0.0

    def _jwks(self) -> PyJWKClient:
        # PyJWKClient cachea claves; se recrea por TTL para recoger rotaciones.
        now = time.monotonic()
        if self._jwk_client is None or now - self._jwk_client_loaded_at > JWKS_CACHE_TTL_SECONDS:
            self._jwk_client = PyJWKClient(self._jwks_url, cache_keys=True)
            self._jwk_client_loaded_at = now
        return self._jwk_client

    def _decode(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise AuthError(f"token malformado: {exc}") from exc

        algorithm = header.get("alg")
        options = {"require": ["exp", "sub"], "verify_aud": True, "verify_exp": True}

        if algorithm in ASYMMETRIC_ALGORITHMS:
            try:
                key = self._jwks().get_signing_key_from_jwt(token).key
            except Exception as exc:
                raise AuthError(f"no se pudo resolver la clave publica: {exc}") from exc
            algorithms = [algorithm]
        elif algorithm == "HS256":
            if not self._jwt_secret:
                raise AuthError("token HS256 sin SUPABASE_JWT_SECRET configurado")
            key = self._jwt_secret
            algorithms = ["HS256"]
        else:
            raise AuthError(f"algoritmo no admitido: {algorithm}")

        try:
            return jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience=self._audience,
                issuer=self._issuer,
                options=options,
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("token caducado") from exc
        except jwt.InvalidAudienceError as exc:
            raise AuthError("audiencia invalida") from exc
        except jwt.InvalidIssuerError as exc:
            raise AuthError("emisor invalido") from exc
        except jwt.PyJWTError as exc:
            raise AuthError(f"token invalido: {exc}") from exc

    async def verify(self, token: str) -> AdminIdentity:
        claims = self._decode(token)
        user_id = str(claims.get("sub") or "")
        if not user_id:
            raise AuthError("token sin sujeto")
        # Segunda barrera sobre la tabla admin_users de RLS: si hay lista blanca,
        # un usuario autenticado cualquiera no basta para entrar al panel.
        if self._admin_user_ids and user_id not in self._admin_user_ids:
            raise AuthError("el usuario no es administrador")
        return AdminIdentity(
            user_id=user_id,
            email=claims.get("email"),
            role=claims.get("role"),
            issued_by="supabase",
        )
