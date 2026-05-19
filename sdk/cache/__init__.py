"""
cache/ — Décorateur @cached pour les actions et méthodes de plugin.

Usage:
    from xcore.sdk import cached

    class Plugin(TrustedBase):

        @action("get_user")
        @cached(ttl=300, key=lambda self, p: f"user:{p['id']}")
        async def get_user(self, payload: dict) -> dict:
            user = await self.get_service("db").session()
            ...
            return ok(user=user)

        # Clé automatique basée sur le nom de la méthode + payload
        @action("list_products")
        @cached(ttl=60)
        async def list_products(self, payload: dict) -> dict:
            ...

Requiert que le service "cache" soit activé dans integration.yaml.
Si le service est absent, le décorateur passe en mode passthrough.
"""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable


def cached(
    ttl: int | None = None,
    key: Callable | str | None = None,
) -> Callable:
    """
    Met en cache le résultat d'une méthode de plugin.

    Args:
        ttl:  Durée de vie en secondes (None = pas d'expiration).
        key:  Clé de cache.
              - Callable(self, payload) → str  : clé personnalisée
              - str                            : clé fixe
              - None (défaut)                 : hash stable du nom + payload

    Si le service "cache" est absent, la méthode est exécutée normalement.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(self, payload: dict, *args, **kwargs) -> Any:
            cache_svc = _get_cache(self)
            if cache_svc is None:
                return await fn(self, payload, *args, **kwargs)

            cache_key = _resolve_key(fn, self, payload, key)
            cached_value = await cache_svc.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await fn(self, payload, *args, **kwargs)
            await cache_svc.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


def invalidate(key: Callable | str) -> Callable:
    """
    Invalide une clé de cache après l'exécution de la méthode.

    Usage:
        @action("update_user")
        @invalidate(key=lambda self, p: f"user:{p['id']}")
        async def update_user(self, payload: dict) -> dict:
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(self, payload: dict, *args, **kwargs) -> Any:
            result = await fn(self, payload, *args, **kwargs)
            cache_svc = _get_cache(self)
            if cache_svc is not None:
                cache_key = (
                    key(self, payload) if callable(key) else key
                )
                await cache_svc.delete(cache_key)
            return result

        return wrapper

    return decorator


# ── Helpers internes ──────────────────────────────────────────────────────────


def _get_cache(plugin_instance: Any) -> Any | None:
    ctx = getattr(plugin_instance, "ctx", None)
    if ctx is None:
        return None
    try:
        return ctx.get_service("cache")
    except KeyError:
        return None


def _resolve_key(fn: Callable, self: Any, payload: dict, key: Any) -> str:
    if callable(key):
        return key(self, payload)
    if isinstance(key, str):
        return key
    raw = json.dumps({"fn": fn.__qualname__, **payload}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


__all__ = [
    "cached",
    "invalidate",
]
