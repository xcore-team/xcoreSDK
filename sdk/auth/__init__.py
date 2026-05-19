"""
auth/ — Contrats et helpers d'authentification pour les plugins xcore.

Usage (plugin qui implémente l'auth) :
    from xcore.sdk import AuthBackend, AuthPayload, register_auth_backend

    class JWTAuthBackend:
        async def decode_token(self, token: str) -> AuthPayload | None:
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            return AuthPayload(
                sub=payload["sub"],
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
            )

        async def extract_token(self, request) -> str | None:
            header = request.headers.get("Authorization", "")
            return header.removeprefix("Bearer ") or None

        async def has_permission(self, payload: AuthPayload, permission: str) -> bool:
            return permission in payload.get("permissions", [])

    class Plugin(TrustedBase):
        async def on_load(self):
            register_auth_backend(JWTAuthBackend())

        async def on_unload(self):
            unregister_auth_backend()

        async def handle(self, action, payload):
            return ok()

Usage (plugin qui consomme l'auth) :
    from xcore.sdk import get_auth_backend, has_auth_backend

    backend = get_auth_backend()
    if backend:
        user = await backend.decode_token(token)
"""

from xcore.kernel.api.auth import (
    AuthBackend,
    AuthPayload,
    get_auth_backend,
    has_auth_backend,
    register_auth_backend,
    unregister_auth_backend,
)

__all__ = [
    "AuthBackend",
    "AuthPayload",
    "register_auth_backend",
    "unregister_auth_backend",
    "get_auth_backend",
    "has_auth_backend",
]
