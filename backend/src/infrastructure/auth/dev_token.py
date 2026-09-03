"""Verificador de desarrollo.

Existe para poder ejercitar `/admin` sin Supabase. Es deliberadamente incapaz de
activarse por accidente en produccion: `Settings.validate()` aborta el arranque si
ENVIRONMENT=production con AUTH_BACKEND=dev, y sin token configurado este
verificador rechaza todo.
"""

from __future__ import annotations

import hmac

from .identity import AdminIdentity, AdminTokenVerifier, AuthError

DEV_USER_ID = "00000000-0000-0000-0000-00000000dev0"


class DevTokenVerifier(AdminTokenVerifier):
    def __init__(self, expected_token: str, user_id: str = DEV_USER_ID) -> None:
        self._expected_token = expected_token or ""
        self._user_id = user_id

    async def verify(self, token: str) -> AdminIdentity:
        if not self._expected_token:
            raise AuthError("AUTH_BACKEND=dev sin DEV_ADMIN_TOKEN configurado")
        # Comparacion en tiempo constante: aunque sea un modo de desarrollo, no se
        # ensena a filtrar el token por temporizacion.
        if not hmac.compare_digest(token, self._expected_token):
            raise AuthError("token de desarrollo invalido")
        return AdminIdentity(
            user_id=self._user_id,
            email="dev@localhost",
            role="admin",
            issued_by="dev",
        )
