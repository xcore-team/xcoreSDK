# xcoreSDK

SDK Python pour developper des plugins `xcore`.

`xcoreSDK` fournit les bases, mixins, decorateurs et utilitaires necessaires pour construire des plugins `xcore` avec des actions, routes HTTP, evenements, hooks, scheduling, cache, observabilite et integrations de services.

## Ce que le SDK apporte

- Une base de plugin prete a l'emploi avec `AutoMixin`
- Des decorateurs comme `@action`, `@route`, `@trusted`, `@sandboxed`
- La gestion des evenements et hooks avec `@on_event` et `@on_hook`
- Le scheduling avec `@cron` et `@interval`
- Le cache avec `@cached` et `@invalidate`
- Des helpers d'observabilite comme `@traced`, `@timed`, `@counted`, `@health_check`
- Des adaptateurs de repository pour SQL async/sync, MongoDB et Redis

## Prerequis

- Python `3.12+`
- `uv`
- Le noyau `xcore` disponible dans l'environnement

Le projet depend de `xcore`, qui doit etre importable au runtime.

## Installation

Pour travailler localement sur le SDK :

```bash
git clone https://github.com/traoreera/xcoreSDK
cd xcoreSDK
uv sync
```

## Structure minimale d'un plugin

```text
my_plugin/
├── plugin.yaml
└── src/
    └── main.py
```

### `plugin.yaml`

```yaml
name: my_plugin
version: 1.0.0
execution_mode: trusted
```

### `src/main.py`

```python
from xcore.sdk import AutoMixin, action, ok


class Plugin(AutoMixin):
    @action("ping")
    async def ping(self, payload: dict) -> dict:
        return ok(pong=True)
```

## Exemple rapide

Le SDK expose un point d'entree central :

```python
from xcore.sdk import (
    AutoMixin,
    action,
    route,
    on_event,
    cron,
    cached,
    ok,
)
```

Exemple avec action, route et evenement :

```python
from xcore.sdk import AutoMixin, Event, action, ok, on_event, route


class Plugin(AutoMixin):
    @action("ping")
    async def ping(self, payload: dict) -> dict:
        return ok(pong=True, plugin=self.ctx.name)

    @route("/ping", method="GET")
    async def ping_route(self):
        return {"pong": True}

    @on_event("user.created")
    async def on_user_created(self, event: Event) -> None:
        self.logger.info("new user: %s", event.data.get("user_id"))
```

## Developpement

```bash
# Synchroniser l'environnement
uv sync

# Lancer la documentation locale
uv run mkdocs serve
```

## Documentation

La documentation du projet est dans `docs/` :

- `docs/installation.md` pour l'installation
- `docs/concepts.md` pour l'architecture et les concepts
- `docs/examples/demo-plugin.md` pour un plugin de demonstration complet
- `docs/api/` pour les references des decorateurs, manifest, auth, cache, scheduler, observabilite et evenements

## Export principal

Le module `xcore.sdk` reexporte notamment :

- `AutoMixin`
- `TrustedBase`
- `action`, `route`, `trusted`, `sandboxed`, `validate_payload`
- `on_event`, `on_hook`
- `cron`, `interval`
- `cached`, `invalidate`
- `traced`, `timed`, `counted`, `health_check`
- `ok`, `error`

## Licence

Ce projet est distribue sous licence `LICENSE`.
