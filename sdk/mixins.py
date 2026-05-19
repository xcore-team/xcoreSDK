"""
mixins.py — AutoMixin : composition unique de tous les mixins SDK.

Usage :
    from xcore.sdk import AutoMixin

    class Plugin(AutoMixin):

        @action("hello")
        async def hello(self, payload: dict) -> dict:
            return ok(msg="hello")

        @route("/hello", method="GET")
        async def hello_http(self):
            return {"msg": "hello"}

        @on_event("user.created")
        async def welcome(self, event):
            ...

AutoMixin regroupe, dans l'ordre MRO recommandé :
    EventMixin → HookMixin → ObservabilityMixin → ScheduledMixin
    → RoutedPlugin → AutoDispatchMixin → TrustedBase
"""

from xcore.kernel.api.contract import TrustedBase

from .decorators import AutoDispatchMixin, RoutedPlugin
from .events import EventMixin, HookMixin
from .observability import ObservabilityMixin
from .scheduler import ScheduledMixin


class AutoMixin(
    EventMixin,
    HookMixin,
    ObservabilityMixin,
    ScheduledMixin,
    RoutedPlugin,
    AutoDispatchMixin,
    TrustedBase,
):
    """
    Composition de tous les mixins SDK en une seule classe de base.

    Capacités incluses :
      EventMixin        @on_event("evt") → abonné au bus dans on_load
      HookMixin         @on_hook("h")   → enregistré dans HookManager dans on_load
      ObservabilityMixin @health_check  → enregistré dans on_load ; self.logger disponible
      ScheduledMixin    @cron / @interval → jobs APScheduler dans on_load / on_unload
      RoutedPlugin      @route          → RouterIn() monte les routes FastAPI
      AutoDispatchMixin @action         → handle() généré automatiquement
      TrustedBase       self.ctx, get_service(), get_service_as(), call_plugin()

    get_router() est pré-câblé sur RouterIn() : les routes @route sont montées
    automatiquement sans avoir à surcharger get_router() dans le plugin.

    Pour un plugin ultra-léger sans toutes ces capacités, hériter directement
    de TrustedBase + les mixins nécessaires.
    """

    def get_router(self):
        """Expose les routes @route au kernel. Retourne None si aucune route."""
        return self.RouterIn()
