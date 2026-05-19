# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`xcoreSDK` is the developer-facing SDK for building plugins on top of the `xcore` framework. The `sdk/` directory here is the source of truth for `xcore/sdk/` — changes are developed here and synced into the `xcore` package.

The `xcore` kernel is a dependency installed from `https://github.com/traoreera/xcore.git`. All imports in `sdk/` use absolute `xcore.*` paths (not relative) so the code works both standalone and when installed inside `xcore`.

## Setup

```bash
uv sync          # install dependencies
```

> Note: the `makefile` contains `poetry` commands left over from xcore — those are stale. Use `uv` directly.

## Running / testing

```bash
uv run pytest                        # run all tests
uv run pytest tests/path/test_x.py  # single test file
```

When testing locally (outside `xcore`), prefix imports with `sys.path.insert(0, '.')` to load the local `sdk/` as a top-level module since the installed `xcore.sdk` won't include local changes.

## Architecture

```
sdk/
  __init__.py         re-exports everything — single import surface for plugin authors
  plugin_base.py      PluginManifest, ResourceConfig, RuntimeConfig dataclasses
  decorators.py       core: @action, @route, @sandboxed, @trusted, @require_service,
                      @validate_payload, RoutedPlugin, AutoDispatchMixin
  routers.py          RouterRegistry (FastAPI router wrapper)
  adapter/
    asyncsql.py       BaseAsyncRepository — SQLAlchemy async CRUD
    syncsql.py        BaseSyncRepository  — SQLAlchemy sync CRUD
    mongodb.py        BaseMongoRepository — Motor (MongoDB async)
    redis.py          BaseRedisRepository — Redis with JSON serialization + key prefix
  events/             EventMixin, HookMixin, @on_event, @on_hook, Event, HookResult
  observability/      ObservabilityMixin, get_logger, @traced, @counted, @timed,
                      @health_check
  scheduler/          ScheduledMixin, @cron, @interval
  cache/              @cached, @invalidate
  auth/               AuthBackend, AuthPayload, register_auth_backend, get_auth_backend
```

## Plugin authoring model

A plugin class inherits from `TrustedBase`. Mixins are composable and chain through Python MRO — each mixin's `on_load` calls `await super().on_load()`.

```python
from xcore.sdk import (
    TrustedBase, AutoDispatchMixin,
    EventMixin, HookMixin, ObservabilityMixin, ScheduledMixin,
    action, on_event, on_hook, cron, interval,
    traced, counted, health_check, cached,
    ok, error, Event,
)

class Plugin(EventMixin, HookMixin, ObservabilityMixin, ScheduledMixin,
             AutoDispatchMixin, TrustedBase):

    # HTTP route (mounted at /plugins/<name>/status)
    @route("/status", method="GET")
    async def status_http(self):
        return {"state": "running"}

    # Action dispatch via handle()
    @action("process")
    @traced("process")          # span in self.ctx.tracer
    @counted("process.calls")  # counter in self.ctx.metrics
    @cached(ttl=60, key=lambda self, p: f"result:{p['id']}")
    async def process(self, payload: dict) -> dict:
        self.logger.info("processing %s", payload["id"])
        return ok(done=True)

    # Event bus subscription (registered in on_load)
    @on_event("user.created")
    async def welcome(self, event: Event):
        await self.call_plugin("email", "send", {"to": event.data["email"]})

    # Lifecycle hook
    @on_hook("plugin.*.loaded", priority=10)
    async def after_plugin_load(self, event: Event): ...

    # Scheduled tasks (require scheduler service in integration.yaml)
    @cron("0 9 * * MON-FRI")
    async def morning_sync(self): ...

    @interval(seconds=30)
    async def heartbeat(self): ...

    # Health check (registered in on_load, exposed at /health)
    @health_check("my_plugin.db")
    async def check_db(self) -> tuple[bool, str]:
        try:
            await self.get_service("db").execute("SELECT 1")
            return True, "ok"
        except Exception as e:
            return False, str(e)
```

## Key contracts

### Mixin execution order

Recommended MRO (left to right): `EventMixin, HookMixin, ObservabilityMixin, ScheduledMixin, AutoDispatchMixin, TrustedBase`. Each mixin calls `await super().on_load()` and `await super().on_unload()` to chain.

### Decorator semantics

| Decorator | Registered at | Uses |
|---|---|---|
| `@action("name")` | class definition | `AutoDispatchMixin.handle()` |
| `@route(path, method)` | class definition | `RoutedPlugin.RouterIn()` |
| `@on_event("user.*")` | `on_load` via `EventMixin` | `self.ctx.events` |
| `@on_hook("plugin.*")` | `on_load` via `HookMixin` | `self.ctx.hooks` |
| `@cron("0 9 * * *")` | `on_load` via `ScheduledMixin` | `self.ctx.get_service("scheduler")` |
| `@interval(seconds=30)` | `on_load` via `ScheduledMixin` | `self.ctx.get_service("scheduler")` |
| `@health_check("name")` | `on_load` via `ObservabilityMixin` | `self.ctx.health` |
| `@traced("span")` | call time | `self.ctx.tracer` |
| `@counted("metric")` | call time | `self.ctx.metrics` |
| `@timed("metric")` | call time | `self.ctx.metrics` |
| `@cached(ttl=60)` | call time | `self.ctx.get_service("cache")` |

All runtime decorators (`@traced`, `@counted`, `@timed`, `@cached`) are silent no-ops if the relevant service is absent from context.

### Available services via `self.get_service(name)`

| Key | Type | Notes |
|---|---|---|
| `"db"` | `AsyncSQLAdapter` | async SQLAlchemy |
| `"syncdb"` | `SQLAdapter` | sync SQLAlchemy |
| `"mongodb"` | `MongoDBAdapter` | Motor |
| `"redisAdapter"` | `RedisAdapter` | raw Redis client |
| `"cache"` | `CacheService` | unified cache (memory or Redis) |
| `"scheduler"` | `SchedulerService` | APScheduler |

### DB repositories

Subclass the base repository and set the class attribute:

```python
class UserRepo(BaseAsyncRepository):       # SQL async
    ...  # pass model to __init__

class OrderRepo(BaseMongoRepository):      # MongoDB
    collection_name = "orders"

class SessionRepo(BaseRedisRepository):    # Redis
    prefix = "session"
```

### Auth plugin pattern

```python
from xcore.sdk import AuthBackend, AuthPayload, register_auth_backend, unregister_auth_backend

class Plugin(TrustedBase):
    async def on_load(self):
        register_auth_backend(MyJWTBackend())

    async def on_unload(self):
        unregister_auth_backend()
```

### Manifest schema (`sdk/manifest_schema.json`)

Required fields: `name` (pattern `^[a-z][a-z0-9_-]*$`), `version` (semver). Execution modes: `trusted`, `sandboxed`, `legacy`. Version constraints use semver expressions: `">=2.0,<3.0"`.
