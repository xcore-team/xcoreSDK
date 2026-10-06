"""
sdk/ — Kit de développement pour les auteurs de plugins xcore.

Import minimal :
    from xcore.sdk import TrustedBase, action, ok, error

Imports par domaine :
    from xcore.sdk import EventMixin, on_event, Event
    from xcore.sdk import HookMixin, on_hook
    from xcore.sdk import ObservabilityMixin, get_logger, traced, counted, timed, health_check
    from xcore.sdk import ScheduledMixin, cron, interval
    from xcore.sdk import cached, invalidate
    from xcore.sdk import AuthBackend, AuthPayload, register_auth_backend
    from xcore.sdk import BaseAsyncRepository, BaseSyncRepository
    from xcore.sdk import BaseMongoRepository, BaseRedisRepository
"""

# ── Kernel contracts ──────────────────────────────────────────────────────────
from xcore.kernel.api.contract import BasePlugin, ExecutionMode, TrustedBase, error, ok
from xcore.kernel.api.rbac import RBACChecker, require_permission, require_role
from xcore.kernel.permissions.engine import PermissionDenied
from xcore.kernel.runtime.state_machine import PluginState

# ── Auth ─────────────────────────────────────────────────────────────────────
from .auth import (
    AuthBackend,
    AuthPayload,
    get_auth_backend,
    has_auth_backend,
    register_auth_backend,
    unregister_auth_backend,
)

# ── DB Adapters ───────────────────────────────────────────────────────────────
from .adapter import (
    BaseAsyncRepository,
    BaseMongoRepository,
    BaseRedisRepository,
    BaseSyncRepository,
)

# ── Cache ─────────────────────────────────────────────────────────────────────
from .cache import cached, invalidate

# ── Core decorators ───────────────────────────────────────────────────────────
from .decorators import (
    AutoDispatchMixin,
    RoutedPlugin,
    action,
    require_service,
    route,
    sandboxed,
    schema,
    trusted,
    validate_payload,
)

# ── Events & Hooks ────────────────────────────────────────────────────────────
from .events import Event, EventMixin, HookMixin, HookResult, on_event, on_hook

# ── Observability ─────────────────────────────────────────────────────────────
from .observability import (
    ObservabilityMixin,
    counted,
    get_logger,
    health_check,
    timed,
    traced,
)

# ── AutoMixin ─────────────────────────────────────────────────────────────────
from .mixins import AutoMixin

# ── Plugin manifest ───────────────────────────────────────────────────────────
from .plugin_base import PluginManifest, ResourceConfig, RuntimeConfig

# ── Router ────────────────────────────────────────────────────────────────────
from .routers import RouterRegistry

# ── Scheduler ─────────────────────────────────────────────────────────────────
from .scheduler import ScheduledMixin, cron, interval

__all__ = [
    # Kernel
    "TrustedBase",
    "BasePlugin",
    "ok",
    "error",
    "ExecutionMode",
    "PermissionDenied",
    "PluginState",
    # RBAC
    "RBACChecker",
    "require_permission",
    "require_role",
    # Auth
    "AuthBackend",
    "AuthPayload",
    "register_auth_backend",
    "unregister_auth_backend",
    "get_auth_backend",
    "has_auth_backend",
    # Manifest
    "PluginManifest",
    "ResourceConfig",
    "RuntimeConfig",
    # Core decorators
    "action",
    "schema",
    "sandboxed",
    "trusted",
    "require_service",
    "validate_payload",
    "route",
    "RoutedPlugin",
    "AutoDispatchMixin",
    "RouterRegistry",
    # DB adapters
    "BaseAsyncRepository",
    "BaseSyncRepository",
    "BaseMongoRepository",
    "BaseRedisRepository",
    # Events & Hooks
    "on_event",
    "on_hook",
    "EventMixin",
    "HookMixin",
    "Event",
    "HookResult",
    # Observability
    "get_logger",
    "traced",
    "counted",
    "timed",
    "health_check",
    "ObservabilityMixin",
    # Scheduler
    "cron",
    "interval",
    "ScheduledMixin",
    # Cache
    "cached",
    "invalidate",
    # All-in-one
    "AutoMixin",
]
