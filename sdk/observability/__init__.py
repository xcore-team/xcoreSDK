"""
observability/ — Logging, métriques, tracing et health checks pour les plugins.

Usage:
    from xcore.sdk import ObservabilityMixin, get_logger, traced, counted, health_check

    class Plugin(ObservabilityMixin, TrustedBase):

        @action("process")
        @traced("process")
        @counted("plugin.process.calls")
        async def process(self, payload: dict) -> dict:
            self.logger.info("processing %s", payload)
            return ok()

        @health_check("my_plugin.db")
        async def check_db(self) -> tuple[bool, str]:
            try:
                await self.get_service("db").execute("SELECT 1")
                return True, "ok"
            except Exception as e:
                return False, str(e)
"""

from __future__ import annotations

import functools
import logging
from typing import Callable


# ── Logger helper ─────────────────────────────────────────────────────────────


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger sous le namespace xcore.

    "my_plugin" → logger "xcore.my_plugin"
    "xcore.my_plugin" → logger "xcore.my_plugin" (inchangé)
    """
    from xcore.kernel.observability.logging import get_logger as _get_logger

    return _get_logger(name)


# ── Décorateurs ───────────────────────────────────────────────────────────────


def traced(span_name: str | None = None) -> Callable:
    """
    Enveloppe une méthode dans un span de tracing.

    Utilise self.ctx.tracer s'il est disponible, sinon passe sans effet.

    Usage:
        @action("process")
        @traced("process_item")
        async def process(self, payload: dict) -> dict:
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(self, *args, **kwargs):
            tracer = getattr(getattr(self, "ctx", None), "tracer", None)
            if tracer is None:
                return await fn(self, *args, **kwargs)
            with tracer.span(span_name or fn.__name__) as span:
                try:
                    return await fn(self, *args, **kwargs)
                except Exception as e:
                    span.set_status("error")
                    span.set_attribute("error.message", str(e))
                    raise

        return wrapper

    return decorator


def counted(metric_name: str, labels: dict | None = None) -> Callable:
    """
    Incrémente un compteur de métriques à chaque appel.

    Utilise self.ctx.metrics s'il est disponible, sinon passe sans effet.

    Usage:
        @action("send_email")
        @counted("plugin.emails.sent", labels={"type": "transactional"})
        async def send_email(self, payload: dict) -> dict:
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(self, *args, **kwargs):
            result = await fn(self, *args, **kwargs)
            metrics = getattr(getattr(self, "ctx", None), "metrics", None)
            if metrics is not None:
                metrics.counter(metric_name, labels).inc()
            return result

        return wrapper

    return decorator


def timed(metric_name: str) -> Callable:
    """
    Enregistre la durée d'exécution dans un histogram de métriques.

    Usage:
        @action("process")
        @timed("plugin.process.duration_seconds")
        async def process(self, payload: dict) -> dict:
            ...
    """
    import time

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(self, *args, **kwargs):
            start = time.monotonic()
            try:
                return await fn(self, *args, **kwargs)
            finally:
                duration = time.monotonic() - start
                metrics = getattr(getattr(self, "ctx", None), "metrics", None)
                if metrics is not None:
                    metrics.histogram(metric_name).observe(duration)

        return wrapper

    return decorator


def health_check(check_name: str) -> Callable:
    """
    Marque une méthode comme health check.

    La méthode doit retourner (bool, str) : (ok, message).
    Enregistrée automatiquement dans self.ctx.health au on_load()
    si le plugin hérite de ObservabilityMixin.

    Usage:
        @health_check("my_plugin.cache")
        async def check_cache(self) -> tuple[bool, str]:
            try:
                await self.get_service("cache").get("ping")
                return True, "ok"
            except Exception as e:
                return False, str(e)
    """

    def decorator(fn: Callable) -> Callable:
        fn._xcore_health_check = check_name
        return fn

    return decorator


# ── Mixin ─────────────────────────────────────────────────────────────────────


class ObservabilityMixin:
    """
    Mixin qui expose self.logger et enregistre les méthodes @health_check.

    Usage:
        class Plugin(ObservabilityMixin, TrustedBase):

            @health_check("my_plugin.db")
            async def check_db(self) -> tuple[bool, str]:
                ...

            async def handle(self, action, payload):
                self.logger.info("handling %s", action)
                return ok()
    """

    async def on_load(self) -> None:
        await super().on_load()
        if not (self.ctx and self.ctx.health):
            return
        for attr_name in dir(self.__class__):
            method = getattr(self.__class__, attr_name, None)
            check_name = getattr(method, "_xcore_health_check", None)
            if not check_name:
                continue
            bound = getattr(self, attr_name)
            self.ctx.health.register(check_name)(bound)

    @property
    def logger(self) -> "logging.Logger":
        plugin_name = (
            getattr(self.ctx, "name", "plugin") if self.ctx is not None else "plugin"
        )
        return get_logger(f"plugin.{plugin_name}")


__all__ = [
    "get_logger",
    "traced",
    "counted",
    "timed",
    "health_check",
    "ObservabilityMixin",
]
