"""
scheduler/ — Décorateurs et mixin pour planifier des tâches dans un plugin.

Usage:
    from xcore.sdk import ScheduledMixin, cron, interval

    class Plugin(ScheduledMixin, TrustedBase):

        @cron("0 9 * * MON-FRI")
        async def morning_sync(self):
            await do_sync()

        @interval(seconds=30)
        async def heartbeat(self):
            await ping_services()

        async def handle(self, action, payload):
            return ok()

Requiert que le service "scheduler" soit activé dans integration.yaml :
    services:
      scheduler:
        enabled: true
"""

from __future__ import annotations

from typing import Callable


# ── Décorateurs de marquage ───────────────────────────────────────────────────


def cron(expression: str, job_id: str | None = None) -> Callable:
    """
    Planifie une méthode avec une expression cron (5 champs).

    expression : "minute heure jour mois jour_semaine"
    Exemple : "0 9 * * MON-FRI"  (tous les jours ouvrés à 9h)

    Le job_id est généré automatiquement comme "<plugin>.<methode>" si absent.
    """

    def decorator(fn: Callable) -> Callable:
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(
                f"Expression cron invalide : {expression!r} "
                "(attendu 5 champs : minute heure jour mois jour_semaine)"
            )
        fn._xcore_cron = expression
        fn._xcore_cron_id = job_id
        return fn

    return decorator


def interval(**kwargs) -> Callable:
    """
    Planifie une méthode à intervalle régulier.

    Kwargs transmis à APScheduler : seconds=, minutes=, hours=, etc.
    Exemple : @interval(seconds=30)
    """
    if not kwargs:
        raise ValueError(
            "@interval requiert au moins un argument (ex: seconds=30, minutes=5)"
        )

    def decorator(fn: Callable) -> Callable:
        fn._xcore_interval = kwargs
        return fn

    return decorator


# ── Mixin ─────────────────────────────────────────────────────────────────────


class ScheduledMixin:
    """
    Mixin qui enregistre automatiquement les méthodes @cron et @interval
    dans le SchedulerService au on_load().

    Si le service "scheduler" n'est pas disponible, les tâches sont ignorées
    sans lever d'erreur (mode dégradé silencieux).
    """

    async def on_load(self) -> None:
        await super().on_load()
        if self.ctx is None:
            return
        try:
            scheduler = self.ctx.get_service("scheduler")
        except KeyError:
            return

        plugin_name = getattr(self.ctx, "name", self.__class__.__name__)

        for attr_name in dir(self.__class__):
            method = getattr(self.__class__, attr_name, None)

            if cron_expr := getattr(method, "_xcore_cron", None):
                bound = getattr(self, attr_name)
                job_id = (
                    getattr(method, "_xcore_cron_id", None)
                    or f"{plugin_name}.{attr_name}"
                )
                parts = cron_expr.split()
                minute, hour, day, month, day_of_week = parts
                scheduler.add_job(
                    bound,
                    trigger="cron",
                    job_id=job_id,
                    replace_existing=True,
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                )

            if interval_kwargs := getattr(method, "_xcore_interval", None):
                bound = getattr(self, attr_name)
                job_id = f"{plugin_name}.{attr_name}"
                scheduler.add_job(
                    bound,
                    trigger="interval",
                    job_id=job_id,
                    replace_existing=True,
                    **interval_kwargs,
                )

    async def on_unload(self) -> None:
        await super().on_unload()
        if self.ctx is None:
            return
        try:
            scheduler = self.ctx.get_service("scheduler")
        except KeyError:
            return

        plugin_name = getattr(self.ctx, "name", self.__class__.__name__)

        for attr_name in dir(self.__class__):
            method = getattr(self.__class__, attr_name, None)
            has_cron = getattr(method, "_xcore_cron", None)
            has_interval = getattr(method, "_xcore_interval", None)
            if has_cron or has_interval:
                job_id = f"{plugin_name}.{attr_name}"
                try:
                    scheduler.remove_job(job_id)
                except Exception:
                    pass


__all__ = [
    "cron",
    "interval",
    "ScheduledMixin",
]
