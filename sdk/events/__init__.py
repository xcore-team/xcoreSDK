"""
events/ — Décorateurs et mixins pour les events et hooks xcore.

Usage:
    from xcore.sdk import EventMixin, HookMixin, on_event, on_hook, Event

    class Plugin(EventMixin, HookMixin, TrustedBase):

        @on_event("user.created")
        async def welcome(self, event: Event):
            print(event.data["email"])

        @on_event("order.*")          # wildcards supportés
        async def on_any_order(self, event: Event):
            ...

        @on_hook("plugin.*.loaded", priority=10)
        async def after_plugin_load(self, event: Event):
            ...

        async def handle(self, action, payload):
            return ok()
"""

from __future__ import annotations

from typing import Callable

from xcore.kernel.events.section import Event, HookResult

# ── Décorateurs de marquage ───────────────────────────────────────────────────


def on_event(event_name: str, priority: int = 50, once: bool = False) -> Callable:
    """
    Marque une méthode comme handler d'un event du bus.

    Enregistré automatiquement dans self.ctx.events au on_load()
    si le plugin hérite de EventMixin.

    Supporte les wildcards : "user.*", "plugin.*.loaded"
    """

    def decorator(fn: Callable) -> Callable:
        fn._xcore_event = event_name
        fn._xcore_event_priority = priority
        fn._xcore_event_once = once
        return fn

    return decorator


def on_hook(
    hook_name: str,
    priority: int = 50,
    once: bool = False,
    timeout: float | None = None,
) -> Callable:
    """
    Marque une méthode comme handler d'un hook (HookManager).

    Enregistré automatiquement dans self.ctx.hooks au on_load()
    si le plugin hérite de HookMixin.
    """

    def decorator(fn: Callable) -> Callable:
        fn._xcore_hook = hook_name
        fn._xcore_hook_priority = priority
        fn._xcore_hook_once = once
        fn._xcore_hook_timeout = timeout
        return fn

    return decorator


# ── Mixins ────────────────────────────────────────────────────────────────────


class EventMixin:
    """
    Mixin qui abonne automatiquement les méthodes @on_event au bus d'événements.

    Usage:
        class Plugin(EventMixin, TrustedBase):

            @on_event("user.created")
            async def on_user_created(self, event: Event):
                ...
    """

    async def on_load(self) -> None:
        await super().on_load()
        if not (self.ctx and self.ctx.events):
            return
        for attr_name in dir(self.__class__):
            method = getattr(self.__class__, attr_name, None)
            event_name = getattr(method, "_xcore_event", None)
            if not event_name:
                continue
            bound = getattr(self, attr_name)
            self.ctx.events.subscribe(
                event_name,
                bound,
                priority=getattr(method, "_xcore_event_priority", 50),
                once=getattr(method, "_xcore_event_once", False),
            )

    async def on_unload(self) -> None:
        await super().on_unload()
        if not (self.ctx and self.ctx.events):
            return
        for attr_name in dir(self.__class__):
            method = getattr(self.__class__, attr_name, None)
            event_name = getattr(method, "_xcore_event", None)
            if not event_name:
                continue
            bound = getattr(self, attr_name)
            self.ctx.events.unsubscribe(event_name, bound)


class HookMixin:
    """
    Mixin qui enregistre automatiquement les méthodes @on_hook dans le HookManager.

    Usage:
        class Plugin(HookMixin, TrustedBase):

            @on_hook("plugin.*.loaded", priority=10)
            async def after_plugin_load(self, event: Event):
                ...
    """

    async def on_load(self) -> None:
        await super().on_load()
        if not (self.ctx and self.ctx.hooks):
            return
        for attr_name in dir(self.__class__):
            method = getattr(self.__class__, attr_name, None)
            hook_name = getattr(method, "_xcore_hook", None)
            if not hook_name:
                continue
            bound = getattr(self, attr_name)
            self.ctx.hooks.register(
                hook_name,
                bound,
                priority=getattr(method, "_xcore_hook_priority", 50),
                once=getattr(method, "_xcore_hook_once", False),
                timeout=getattr(method, "_xcore_hook_timeout", None),
            )

    async def on_unload(self) -> None:
        await super().on_unload()
        if not (self.ctx and self.ctx.hooks):
            return
        for attr_name in dir(self.__class__):
            method = getattr(self.__class__, attr_name, None)
            hook_name = getattr(method, "_xcore_hook", None)
            if not hook_name:
                continue
            bound = getattr(self, attr_name)
            self.ctx.hooks.unregister(hook_name, bound)


__all__ = [
    "on_event",
    "on_hook",
    "EventMixin",
    "HookMixin",
    "Event",
    "HookResult",
]
