# Iikocloud-manager MVP — Design

Date: 2026-07-23  
Status: approved in discussion; awaiting final review of this document  
Reference: `/home/ivan/programming/Iikoserver-manager` + current `/home/ivan/programming/Iikocloud-py-sdk`

## Goal

Rewrite `Iikocloud-manager` as a full structural analogue of `Iikoserver-manager`: Multitone facade, TokenManager with 401 dedup, domain mixins (`core` + `helpers`), dual-server real API tests — while keeping Cloud-specific dual rate limiting and retargeting the **current** semantic `iikocloud-client` API.

**Phasing**

| Phase | Scope |
|-------|--------|
| **MVP (this spec)** | Architecture + auth v2 + rate limits + 5 domains already in use + unit + real integration tests |
| **Later (B)** | Wrap remaining public SDK API modules with the same patterns |

## Decisions (locked)

1. Approach: **big-bang mirror** of Iikoserver-manager layout (not incremental strangler).
2. Auth: **only v2** — `api_key` + `app_id` + `client_secret` → SDK `authenticate_v2`.
3. Rate limiting: keep **per-method token bucket + global** (= freest method rate); auth limited separately; wired through `execute_with_retry`.
4. Integration tests: `config.test.yml` with top-level `read` / `write` sections; env `IIKOCLOUD_TEST_CONFIG`; marker-driven routing (like Iikoserver).
5. Credentials: two full v2 triples supplied by the user in local `config.test.yml` (gitignored).

## Package architecture

```
iikocloud/
  __init__.py                 # public re-exports
  api_client_manager.py       # thin MRO facade: *HelpersMixin + _ManagerBase
  token_manager.py            # Multitone; authenticate_v2; 401 dedup
  rate_limiter.py             # TokenBucketRateLimiter + GlobalRateLimiter
  config_reader.py            # YAML + dotenv + Pydantic SecretStr
  exceptions.py               # IikoCloudException, IikoCloudAuthException
  mixins/
    _base.py                  # ApiCredentials, _ManagerBase, execute_with_retry
    organizations/{core,helpers}.py
    customers/{core,helpers}.py
    terminal_groups/{core,helpers}.py
    menu/{core,helpers}.py
    dictionaries/{core,helpers}.py
```

### Call flow

```
helper → core → execute_with_retry
                 → acquire global + method rate limit
                 → SDK call
                 → on 401: TokenManager.refresh (deduped) → one retry
```

Rules (mirror Iikoserver):

- Core methods: exactly one SDK call inside `api_call`, always via `execute_with_retry`.
- Helpers: call core only (no direct SDK, no second `execute_with_retry`).
- Lazy `get_*_api()` getters live on `_ManagerBase`.
- One manager instance per credentials fingerprint (`key_id`); no manual `key_id` in consumer config.
- One process / one event loop; `close_all()` between `asyncio.run()` cycles.

### Lifecycle

```python
config = get_iikocloud_config()
manager = await IikoCloudApiClientManager.from_config(config)
try:
    ...
finally:
    await IikoCloudApiClientManager.close_all()
```

`close_all()`: clear TokenManager instances, close HTTP clients, reset class locks and global rate limiter.

## Config

### Consumer — `config.yml` (env `IIKOCLOUD_CONFIG`)

```yaml
iikocloud:
  api_key: "..."
  app_id: "..."
  client_secret: "..."
  rate_limits:
    auth:
      max_requests: 1
      time_window_seconds: 5.0
    get_organizations:
      max_requests: 1
      time_window_seconds: 10.0
    # ... one entry per ApiMethod / rate-limited facade
```

- Remove legacy `api_login` and explicit `key_id`.
- `key_id` computed from credentials fingerprint (e.g. hash of api_key + app_id).
- Defaults for missing rate-limit keys preserved in code (as today).

### Tests — `config.test.yml` (env `IIKOCLOUD_TEST_CONFIG`)

Top-level sections only (no `iikocloud:` wrapper, no rate_limits):

```yaml
read:
  api_key: "..."
  app_id: "..."
  client_secret: "..."

write:
  api_key: "..."
  app_id: "..."
  client_secret: "..."
```

- Tests **never** use `get_iikocloud_config()` / `IIKOCLOUD_CONFIG`.
- Missing env/file/section → `pytest.skip`.
- Templates in repo: `config.example.yml`, `config.test.example.yml`, `.env.example`.
- Gitignore: `config.yml`, `config.test.yml`, `.env`, `*.secret`, `app.secret`.

## Auth (TokenManager)

- Fetch token via `AuthorizationApi.authenticate_v2(GetAccessTokenV2Request(...))`.
- Store Bearer on `ApiClient` configuration the same way the current SDK expects.
- Lazy first token; refresh only on 401.
- Concurrent 401s: `token_version` + `Lock` + `Event` → one refresh, waiters reuse result.
- Auth failures → `IikoCloudAuthException` (no retry loop).
- Auth calls go through auth rate-limit callbacks (as today).

## Rate limiting

Keep current semantics:

- `ApiMethod` enum (or equivalent) keys per-method buckets.
- Global limiter capacity = freest (highest RPS) configured method.
- `execute_with_retry` acquires global then method limit before the SDK call.
- Auth path uses its own limit, separate from business methods.

## Naming principles (public API)

Do **not** invent names only from SDK method strings. Prefer names that match **what the method returns / does**, consistent with Iikoserver helper conventions:

| Form | Meaning |
|------|---------|
| `get_X` / `get_all_X` | Returns collection or primary read payload of X |
| `get_X_by_<field>` | Same payload narrowed by one field |
| `find_X_by_<field>` | Lookup by literal search field |
| `create_or_update_X` / `delete_X` / `restore_X` | Mutating ops named by effect |
| `check_X` | Boolean/availability-style result, not a full entity list |

During implementation, for each wrap:

1. Read SDK method + response model.
2. Choose manager name from return/effect semantics (core may align with SDK when the SDK name already matches semantics).
3. Helpers unwrap/assemble for convenience (`get_customer_by_phone`, `get_terminal_groups_by_organization`, …) and name by the value the caller actually cares about.

Legacy short aliases (`organizations()`, `terminal_groups_alive()`, …) are **dropped** in MVP (breaking OK).

### MVP domain surface (indicative; final names follow the principle above)

Domains and SDK anchors (not final public names):

- **organizations** — `get_organizations`, `get_organization_settings` (settings included if trivial wrap)
- **customers** — `create_or_update_customer`, `get_customer_info`, `delete_customers`, `restore_customers` + phone helper
- **terminal_groups** — `get_terminal_groups`, `check_terminal_groups_availability`
- **menu** — `get_external_menus`, `get_external_menu_by_id`, `get_stop_lists` (+ org-scoped helpers if still useful)
- **dictionaries** — cancel causes, delivery order types, payment types, discounts, removal types (+ tips if already trivial)

Out of MVP: deliveries, orders facades, employees, webhooks, invoice processing, reports, etc. (phase B).

## Dependency / packaging

- `iikocloud-client @ git+https://github.com/UserVanya/Iikocloud-py-sdk.git` (direct dep, latest; refresh lock).
- Runtime: pydantic, pyyaml, python-dotenv (declare explicitly).
- Dev: pytest, pytest-asyncio in dependency-group.
- `requires-python >= 3.12`, hatchling package `iikocloud`.
- Align with Iikoserver: `allow-direct-references` if needed for git dep.

## Testing

### Layout

```
tests/
  unit/                 # mocks, no network
  integration/
    conftest.py         # read/write routing, manager fixtures, loop_scope=session
    session/            # auth / concurrency (@test_server)
    organizations/
    customers/
    terminal_groups/
    menu/
    dictionaries/
```

### Markers

`unit`, `integration`, `slow`, `write`, `lifecycle`, `test_server`

Routing: `write` or `test_server` → `write` section; else → `read`.

### Real API coverage (MVP)

- **read**: organizations, terminal groups, menus, stop lists, dictionaries; token reuse.
- **write / lifecycle**: customer create → get → delete → restore (+ cleanup).
- **test_server**: auth concurrency / 401 refresh against write credentials.
- Prefer dynamic fixtures (e.g. first organization id from API) over hardcoded UUIDs where possible; skip if data absent.
- Unit tests migrate/adapt from existing mock suites (multitone, retry, rate limiter, token manager).

Commands:

```bash
uv run pytest -m unit -v
uv run pytest -m integration -v   # needs IIKOCLOUD_TEST_CONFIG
uv run pytest -m "integration and not slow" -v
```

## Docs (MVP minimum)

- Fill `README.md`: install, config v2, quick start, test commands.
- Keep existing flow mermaid docs if still relevant; no full Iikoserver-scale docs set required in MVP.
- Ship `config.example.yml`, `config.test.example.yml`, `.env.example`.

## Non-goals (MVP)

- Full SDK coverage (phase B).
- Supporting auth v1 (`api_login` / `authenticate`).
- Dual-maintaining old path-style SDK method names.
- Perfect eventual-consistency assertions on Cloud; assert on operation responses / returned entities.

## Risks / notes

- Bumping SDK switches transport (aiohttp → httpx) and renames models/methods — unit mocks must be rewritten against new symbols.
- Cloud rate limits are real; integration tests must respect configured limits or use generous test defaults.
- Write-key customer tests must clean up created customers to avoid polluting loyalty data.
- Secrets must never enter git (`config.test.yml` gitignored).

## Success criteria

1. Package structure mirrors Iikoserver-manager (mixins + thin facade + TokenManager).
2. Auth uses v2 only; consumer and test configs use the new fields.
3. Existing MVP domains callable through manager with rate limit + 401 retry.
4. `pytest -m unit` green without network.
5. `pytest -m integration` runs real API calls against `read`/`write` from `config.test.yml` when present; skips cleanly when absent.
6. Ready for phase B: adding a domain = new mixin folder + tests, no redesign.
