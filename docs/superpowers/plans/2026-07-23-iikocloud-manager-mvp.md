# Iikocloud-manager MVP Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `Iikocloud-manager` as an Iikoserver-manager analogue: mixins + Multitone + auth v2 + dual rate limits + real read/write API tests for the five MVP domains.

**Architecture:** Thin `IikoCloudApiClientManager` inherits domain `*HelpersMixin`s and `_ManagerBase`. Core methods wrap one SDK call via `execute_with_retry` (rate limit → call → 401 refresh once). TokenManager uses `authenticate_v2`. Integration tests load only `IIKOCLOUD_TEST_CONFIG` (`read`/`write` sections).

**Tech Stack:** Python ≥3.12, `iikocloud-client` (git, latest semantic API / httpx), pydantic v2, pyyaml, python-dotenv, pytest + pytest-asyncio, uv.

**Spec:** `docs/superpowers/specs/2026-07-23-iikocloud-manager-mvp-design.md`  
**Reference:** `/home/ivan/programming/Iikoserver-manager`  
**SDK:** `/home/ivan/programming/Iikocloud-py-sdk`  
**Branch:** `feature/iikocloud-manager-mvp-rewrite`

## Global Constraints

- Auth **v2 only**: credentials fields `api_key`, `app_id`, `client_secret` (SecretStr in config).
- No `api_login`, no manual `key_id` in consumer config; `key_id` = fingerprint `sha1(f"{api_key}:{app_id}")[:16]`.
- Core → always `execute_with_retry`; helpers → core only; no direct SDK in helpers.
- Public method names follow **return/effect semantics** (see Locked Names below), not legacy short aliases.
- Dual rate limits: per-method + global (= freest method RPS); auth separate.
- Tests never use `IIKOCLOUD_CONFIG`; integration uses `IIKOCLOUD_TEST_CONFIG`.
- One process / one event loop; always `close_all()` between runs / in fixtures teardown.
- Do not commit `config.yml`, `config.test.yml`, `.env`, secrets.
- Prefer Ubuntu WSL 22.04 / `uv run` for all commands.
- Absolute imports from package root (`iikocloud....`), no relative `..` in package modules.

## Locked public names (MVP)

Chosen from SDK return/effect semantics (implementer: verify against response models before coding):

| Domain | Manager method | SDK call | Returns (conceptually) |
|--------|----------------|----------|------------------------|
| auth | (TokenManager) | `authenticate_v2` | JWT bearer token |
| organizations | `get_organizations` | `OrganizationsApi.get_organizations` | `GetOrganizationsResponse` |
| organizations | `get_organization_settings` | `get_organization_settings` | settings response |
| customers | `create_or_update_customer` | same | create/update response |
| customers | `get_customer_info` | same | customer info response |
| customers | `delete_customers` / `restore_customers` | same | delete/restore response |
| customers | `get_customer_by_phone` (helper) | via `get_customer_info` + phone request | customer info |
| terminal_groups | `get_terminal_groups` | same | terminal groups response |
| terminal_groups | `check_terminal_groups_availability` | same | availability response |
| menu | `get_external_menus` | same | menus list response |
| menu | `get_external_menu_by_id` | same | external menu response |
| menu | `get_stop_lists` | same | stop lists response |
| dictionaries | `get_cancel_causes` | same | cancel causes |
| dictionaries | `get_delivery_order_types` | same | delivery order types |
| dictionaries | `get_payment_types` / `get_discounts` / `get_removal_types` / `get_tips_types` | same | respective lists |

Rate-limit / `ApiMethod` keys **must match** these names (rename legacy: `check_terminal_groups_alive` → `check_terminal_groups_availability`, `get_menu_by_id` → `get_external_menu_by_id`, `get_delivery_cancel_causes` → `get_cancel_causes`, `get_order_types` → `get_delivery_order_types`).

Helpers (org-scoped convenience) allowed:

- `get_organizations` with default empty request (helper overload or default arg)
- `get_terminal_groups_by_organization(organization_id)`
- `get_stop_lists_by_organization(organization_id)`
- `get_*_by_organization` for dictionaries as needed

Drop legacy: `organizations()`, `terminal_groups()`, `terminal_groups_alive()`, `external_menus()`, `menu_by_id()`, `delivery_cancel_causes()`, `order_types()`, menu v2/v3/v4 helpers unless new SDK still exposes versioned responses via the same `get_external_menu_by_id` (then name by what is returned).

## File map

| Path | Responsibility |
|------|----------------|
| `pyproject.toml` / `uv.lock` | Deps, markers, hatch allow-direct-references |
| `config.example.yml` / `config.test.example.yml` / `.env.example` | Templates |
| `iikocloud/exceptions.py` | Keep thin hierarchy |
| `iikocloud/rate_limiter.py` | Keep TokenBucket + GlobalRateLimiter |
| `iikocloud/config_reader.py` | v2 fields + rate limit key renames |
| `iikocloud/token_manager.py` | auth v2 Multitone |
| `iikocloud/_log_adapter.py` | optional KeyId logger (copy pattern from iikoserver if useful) |
| `iikocloud/mixins/_base.py` | ApiCredentials, ApiMethod, MethodRateLimits, _ManagerBase |
| `iikocloud/mixins/{domain}/core.py` | 1:1 SDK wraps |
| `iikocloud/mixins/{domain}/helpers.py` | convenience |
| `iikocloud/api_client_manager.py` | Multitone facade + MRO only |
| `iikocloud/__init__.py` | public exports |
| `main.py` | v2 demo |
| `README.md` | install / config / tests |
| `tests/unit/...` | mocks |
| `tests/integration/...` | real API |
| Delete after migration | flat `tests/test_*.py`, mega-file logic |

---

### Task 1: Packaging, markers, example configs

**Files:**
- Modify: `pyproject.toml`
- Create: `config.test.example.yml`, `.env.example`
- Modify: `config.example.yml`
- Modify: `.gitignore` (already has secrets; verify)
- Run: `uv lock` / `uv sync`

**Interfaces:**
- Produces: installable project depending on latest git `iikocloud-client`; pytest markers `unit`, `integration`, `slow`, `lifecycle`, `write`, `test_server`

- [ ] **Step 1: Update `pyproject.toml`**

Align with Iikoserver-manager:

```toml
dependencies = [
    "iikocloud-client @ git+https://github.com/UserVanya/Iikocloud-py-sdk.git",
    "pydantic>=2.0.0",
    "python-dotenv>=1.2.1",
    "pyyaml>=6.0.3",
]

[tool.hatch.metadata]
allow-direct-references = true

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=1.3.0",
    "types-pyyaml>=6.0.12",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
pythonpath = ["."]
markers = [
    "unit: Unit tests (fast, no external dependencies)",
    "integration: Integration tests (require real API access)",
    "slow: Slow tests",
    "lifecycle: Full create-edit-delete-restore cycles",
    "write: Write tests that modify Cloud state",
    "test_server: Route non-write integration test to config.test.yml 'write' section",
]
```

Remove obsolete `[tool.uv.sources]` if dependency uses direct git URL. Keep hatch packages = `["iikocloud"]`.

- [ ] **Step 2: Sync lockfile**

```bash
cd /home/ivan/programming/Iikocloud-manager
uv lock
uv sync --all-groups
```

Expected: `iikocloud-client` resolves to current SDK; `uv run python -c "from iikocloud_client import AuthorizationApi; import inspect; print('authenticate_v2' in dir(AuthorizationApi))"` → `True`.

- [ ] **Step 3: Write example configs**

`config.example.yml`:

```yaml
iikocloud:
  api_key: "your_api_key"
  app_id: "your_app_id"
  client_secret: "your_client_secret"
  rate_limits:
    auth:
      max_requests: 1
      time_window_seconds: 5.0
    get_organizations:
      max_requests: 1
      time_window_seconds: 10.0
    get_organization_settings:
      max_requests: 1
      time_window_seconds: 10.0
    create_or_update_customer:
      max_requests: 100
      time_window_seconds: 60.0
    get_customer_info:
      max_requests: 100
      time_window_seconds: 60.0
    delete_customers:
      max_requests: 100
      time_window_seconds: 60.0
    restore_customers:
      max_requests: 100
      time_window_seconds: 60.0
    get_terminal_groups:
      max_requests: 10
      time_window_seconds: 60.0
    check_terminal_groups_availability:
      max_requests: 10
      time_window_seconds: 60.0
    get_external_menus:
      max_requests: 1
      time_window_seconds: 1800.0
    get_external_menu_by_id:
      max_requests: 5
      time_window_seconds: 60.0
    get_stop_lists:
      max_requests: 10
      time_window_seconds: 60.0
    get_cancel_causes:
      max_requests: 1
      time_window_seconds: 60.0
    get_delivery_order_types:
      max_requests: 1
      time_window_seconds: 60.0
    get_payment_types:
      max_requests: 1
      time_window_seconds: 60.0
    get_discounts:
      max_requests: 1
      time_window_seconds: 60.0
    get_removal_types:
      max_requests: 1
      time_window_seconds: 60.0
    get_tips_types:
      max_requests: 1
      time_window_seconds: 60.0
```

`config.test.example.yml`:

```yaml
read:
  api_key: "read_api_key"
  app_id: "read_app_id"
  client_secret: "read_client_secret"

write:
  api_key: "write_api_key"
  app_id: "write_app_id"
  client_secret: "write_client_secret"
```

`.env.example`:

```bash
IIKOCLOUD_CONFIG=config.yml
IIKOCLOUD_TEST_CONFIG=config.test.yml
```

Ensure local `.env` also has `IIKOCLOUD_TEST_CONFIG=config.test.yml` (do not commit `.env`).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock config.example.yml config.test.example.yml .env.example
git commit -m "chore: bump iikocloud-client and add v2 config templates"
```

---

### Task 2: Config reader (auth v2 + rate limit keys)

**Files:**
- Modify: `iikocloud/config_reader.py`
- Create: `tests/unit/test_config_reader.py`
- Delete later: old assumptions in flat tests

**Interfaces:**
- Produces:
  - `IikoCloudConfig(api_key: SecretStr, app_id: str, client_secret: SecretStr, rate_limits: MethodRateLimitsSettings)`
  - `MethodRateLimitsSettings` fields matching Locked Names
  - `get_iikocloud_config()`, `clear_config_cache()` (add if missing — needed for tests)
  - `compute_global_limit()` includes all methods

- [ ] **Step 1: Write failing unit test**

```python
# tests/unit/test_config_reader.py
import pytest
from pydantic import SecretStr

from iikocloud.config_reader import IikoCloudConfig, MethodRateLimitsSettings

pytestmark = pytest.mark.unit


def test_config_requires_v2_fields() -> None:
    cfg = IikoCloudConfig(
        api_key=SecretStr("k"),
        app_id="app",
        client_secret=SecretStr("secret"),
    )
    assert cfg.api_key.get_secret_value() == "k"
    assert cfg.app_id == "app"
    assert "api_login" not in IikoCloudConfig.model_fields
    assert "key_id" not in IikoCloudConfig.model_fields


def test_rate_limits_use_semantic_keys() -> None:
    s = MethodRateLimitsSettings()
    assert hasattr(s, "check_terminal_groups_availability")
    assert hasattr(s, "get_external_menu_by_id")
    assert hasattr(s, "get_cancel_causes")
    assert hasattr(s, "get_delivery_order_types")
    assert hasattr(s, "get_tips_types")
    assert not hasattr(s, "check_terminal_groups_alive")
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
uv run pytest tests/unit/test_config_reader.py -v
```

Expected: FAIL (old fields / missing module path).

- [ ] **Step 3: Implement `config_reader.py`**

Replace `api_login`/`key_id` with v2 fields; rename rate-limit attributes per Locked Names; keep `parse_config_file` / `get_config` / `get_iikocloud_config`; add:

```python
def clear_config_cache() -> None:
    parse_config_file.cache_clear()
    get_config.cache_clear()
```

- [ ] **Step 4: Run test — expect PASS**

```bash
uv run pytest tests/unit/test_config_reader.py -v
```

- [ ] **Step 5: Commit**

```bash
git add iikocloud/config_reader.py tests/unit/test_config_reader.py
git commit -m "feat: switch config to auth v2 and semantic rate-limit keys"
```

---

### Task 3: TokenManager auth v2

**Files:**
- Rewrite: `iikocloud/token_manager.py`
- Create: `tests/unit/test_token_manager.py` (migrate from old `tests/test_token_manager.py`)

**Interfaces:**
- Consumes: `AuthorizationApi.authenticate_v2`, `GetAccessTokenV2Request`, rate-limit callbacks
- Produces:
  - `TokenManager(api_client, api_key, app_id, client_secret, key_id)`
  - `await TokenManager.get_instance(...)`
  - `await ensure_token_with_limits(acquire_global, acquire_auth)`
  - `await refresh_token_if_401(error, acquire_global, acquire_auth, version_before=None) -> bool`
  - `token_version: int`
  - `await TokenManager.close_all()`
  - Sets `api_client.configuration.access_token = token` (Bearer via SDK Configuration)

- [ ] **Step 1: Write failing unit tests** (mock `authenticate_v2`)

Cover: get_instance multitone; ensure fetches once; concurrent ensure; 401 on auth → `IikoCloudAuthException`; refresh_token_if_401 dedup with version; close_all clears instances.

Key fetch body:

```python
request = GetAccessTokenV2Request(
    apiKey=self._api_key,
    appId=self._app_id,
    clientSecret=self._client_secret,
)
response = await self._authorization_api.authenticate_v2(
    get_access_token_v2_request=request
)
return response.token
```

- [ ] **Step 2: Run — FAIL**

```bash
uv run pytest tests/unit/test_token_manager.py -v
```

- [ ] **Step 3: Implement TokenManager**

Port concurrency logic from current file; replace `api_login` + `access_token_post` / `AuthGetAccessTokenRequest` with v2 fields + `authenticate_v2` / `GetAccessTokenV2Request`. Keep rate-limit callback injection.

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit**

```bash
git add iikocloud/token_manager.py tests/unit/test_token_manager.py
git commit -m "feat: TokenManager authenticate_v2 with 401 dedup"
```

---

### Task 4: `_ManagerBase` + thin facade shell

**Files:**
- Create: `iikocloud/mixins/__init__.py`, `iikocloud/mixins/_base.py`
- Rewrite: `iikocloud/api_client_manager.py` (shell only — domains empty yet)
- Create: `tests/unit/test_manager_lifecycle.py`
- Keep: `iikocloud/rate_limiter.py`, `iikocloud/exceptions.py` (minor import fixes if needed)

**Interfaces:**
- Produces:
  - `@dataclass ApiCredentials(api_key: str, app_id: str, client_secret: str)` with `key_id` property
  - `class ApiMethod(Enum)` — Locked Names values
  - `@dataclass MethodRateLimits` + `from_settings` + `for_method(method) -> RateLimitConfig`
  - `class _ManagerBase` with:
    - lazy getters: `get_authorization_api` (optional), `get_organizations_api`, `get_customers_api`, `get_terminal_groups_api`, `get_menu_api`, `get_dictionaries_api`
    - `_ensure_token_manager`
    - `async execute_with_retry(self, method: ApiMethod, api_call: Callable[[], Awaitable[T]]) -> T`
  - `class IikoCloudApiClientManager(_ManagerBase):` with Multitone `get_instance` / `from_config` / `close_all` / `__init__` building Configuration+ApiClient+limiters

`execute_with_retry` algorithm (preserve current cloud behavior):

1. `await _ensure_token_manager()`
2. Capture `version_before = token_manager.token_version`
3. `await global_limiter.acquire()`; `await method_limiter.acquire()`
4. Try `await api_call()`
5. On 401/`UnauthorizedException`: `refresh_token_if_401(..., version_before)` → if refreshed, retry once (with rate limits again); else raise
6. Other errors: re-raise

`from_config`:

```python
creds = ApiCredentials(
    api_key=config.api_key.get_secret_value(),
    app_id=config.app_id,
    client_secret=config.client_secret.get_secret_value(),
)
limits = MethodRateLimits.from_settings(config.rate_limits)
return await cls.get_instance(creds, limits)
```

Default host for Cloud API: use SDK default `Configuration()` host (typically `https://api-ru.iiko.services`) unless config later adds override — **do not invent host field** unless present in current SDK Configuration defaults.

- [ ] **Step 1: Unit test lifecycle**

```python
async def test_same_credentials_same_instance():
    ...
async def test_close_all_allows_new_instance():
    ...
async def test_key_id_is_fingerprint_not_manual():
    c = ApiCredentials(api_key="a", app_id="b", client_secret="c")
    assert c.key_id  # non-empty, stable
    assert c.key_id == ApiCredentials("a", "b", "c").key_id
```

- [ ] **Step 2: Implement `_base.py` + shell manager**

Move Multitone + limiter wiring out of the old mega-file. Domain mixins not wired yet (plain `_ManagerBase` subclass is OK for this task).

- [ ] **Step 3: PASS unit lifecycle tests**

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: add ManagerBase with rate-limited execute_with_retry"
```

---

### Task 5: Organizations domain

**Files:**
- Create: `iikocloud/mixins/organizations/core.py`, `helpers.py`, `__init__.py`
- Modify: `api_client_manager.py` MRO
- Create: `tests/unit/test_organizations.py`

**Interfaces:**
- Produces:
  - `async def get_organizations(self, request: GetOrganizationsRequest | None = None) -> GetOrganizationsResponse`
  - `async def get_organization_settings(self, request: ...) -> ...` (exact request type from SDK)
  - Helper: default `get_organizations()` builds empty `GetOrganizationsRequest()` if None

Core pattern:

```python
async def get_organizations(
    self, request: GetOrganizationsRequest | None = None
) -> GetOrganizationsResponse:
    req = request if request is not None else GetOrganizationsRequest()

    async def api_call() -> GetOrganizationsResponse:
        api = await self.get_organizations_api()
        return await api.get_organizations(get_organizations_request=req)

    return await self.execute_with_retry(ApiMethod.GET_ORGANIZATIONS, api_call)
```

(Confirm exact kwarg name from SDK signature while implementing.)

- [ ] **Step 1: Unit test with mocked OrganizationsApi**
- [ ] **Step 2: Implement core + helpers; wire mixin**
- [ ] **Step 3: PASS**
- [ ] **Step 4: Commit** `feat: wrap organizations API via mixins`

---

### Task 6: Customers domain

**Files:**
- Create: `iikocloud/mixins/customers/{core,helpers,__init__}.py`
- Modify: MRO
- Create: `tests/unit/test_customers.py`

**Interfaces:**
- Core: `create_or_update_customer`, `get_customer_info`, `delete_customers`, `restore_customers` — each takes the corresponding SDK request model
- Helper:

```python
async def get_customer_by_phone(
    self, organization_id: str | UUID, phone: str
) -> GetCustomerInfoResponse:  # confirm response type name
    request = GetCustomerInfoByPhoneRequest(
        organizationId=_as_uuid(organization_id),
        phone=phone,
        type="phone",  # if required by model
    )
    return await self.get_customer_info(request)
```

Verify constructor fields against `get_customer_info_by_phone_request.py` before coding.

- [ ] TDD cycle + commit `feat: wrap customers API via mixins`

---

### Task 7: Terminal groups domain

**Files:** `iikocloud/mixins/terminal_groups/...`, unit tests

**Interfaces:**
- `get_terminal_groups(request) -> ...`
- `check_terminal_groups_availability(request) -> ...`
- Helper `get_terminal_groups_by_organization(organization_id)`

- [ ] TDD + commit `feat: wrap terminal groups API via mixins`

---

### Task 8: Menu domain

**Files:** `iikocloud/mixins/menu/...`, unit tests

**Interfaces:**
- `get_external_menus(...)`
- `get_external_menu_by_id(menu_request: MenuRequest, ...)`
- `get_stop_lists(request)`
- Helpers: `get_stop_lists_by_organization`, optional menu-by-id+org helper named by return (`get_external_menu_by_id_for_organization` only if it clarifies caller intent)

- [ ] TDD + commit `feat: wrap menu API via mixins`

---

### Task 9: Dictionaries domain

**Files:** `iikocloud/mixins/dictionaries/...`, unit tests

**Interfaces:** Locked Names dictionary methods; each takes SDK request; helpers `get_*_by_organization(organization_id)`.

- [ ] TDD + commit `feat: wrap dictionaries API via mixins`

---

### Task 10: Public package surface + demo + README

**Files:**
- Rewrite: `iikocloud/__init__.py`, `main.py`, `README.md`
- Delete obsolete mega leftovers if any

**Interfaces exports:**

```python
from iikocloud.api_client_manager import (
    ApiCredentials,
    ApiMethod,
    IikoCloudApiClientManager,
    MethodRateLimits,
)
from iikocloud.config_reader import (
    IikoCloudConfig,
    MethodRateLimitsSettings,
    RateLimitSettings,
    clear_config_cache,
    get_config,
    get_iikocloud_config,
    parse_config_file,
)
from iikocloud.exceptions import IikoCloudAuthException, IikoCloudException
from iikocloud.rate_limiter import GlobalRateLimiter, RateLimitConfig, TokenBucketRateLimiter
from iikocloud.token_manager import TokenManager
```

`main.py` demo:

```python
async def main() -> None:
    config = get_iikocloud_config()
    manager = await IikoCloudApiClientManager.from_config(config)
    try:
        orgs = await manager.get_organizations()
        print(len(orgs.organizations))
    finally:
        await IikoCloudApiClientManager.close_all()
```

README: install via uv/git, config v2, close_all rule, test commands.

- [ ] Commit `docs: README and public exports for MVP facade`

---

### Task 11: Integration harness (conftest)

**Files:**
- Create: `tests/integration/conftest.py`
- Create: `tests/conftest.py` (empty or shared utils only)
- Create: `tests/unit/conftest.py` if needed
- Delete: old `tests/conftest.py` manager fixture tied to `IIKOCLOUD_CONFIG`

**Interfaces** (mirror Iikoserver `tests/integration/conftest.py`):

```python
READ = "read"
WRITE = "write"

@lru_cache
def _read_test_config(role: str) -> IikoCloudConfig | None:
    # IIKOCLOUD_TEST_CONFIG YAML: top-level role → validate as IikoCloudConfig
    # Note: test YAML has no rate_limits → defaults apply
    ...

def load_test_config(role: str) -> IikoCloudConfig: ...  # skip if missing

def _section_for(request) -> str:
    if write or test_server marker: return WRITE
    return READ

@pytest_asyncio.fixture(loop_scope="session")
async def manager(request) -> AsyncGenerator[IikoCloudApiClientManager, None]:
    config = load_test_config(_section_for(request))
    mgr = await IikoCloudApiClientManager.from_config(config)
    yield mgr
    # do NOT close_all per test — session scope; teardown fixture closes once

@pytest_asyncio.fixture(loop_scope="session")
async def organization_id(manager) -> UUID:
    resp = await manager.get_organizations()
    if not resp.organizations:
        pytest.skip("no organizations")
    return resp.organizations[0].id
```

Use `pytest_asyncio.fixture(loop_scope="session")` and configure session event loop like Iikoserver (check their `pyproject` / conftest for `loop_scope="session"` pattern — copy exactly).

Also: `fresh_manager` fixture that `close_all` before/after for session/auth tests.

- [ ] Commit `test: add dual-server integration conftest`

---

### Task 12: Integration — session / auth (`write` section)

**Files:**
- Create: `tests/integration/session/test_auth.py`

Mark `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.test_server`.

Cases:

1. Invalid credentials → `IikoCloudAuthException` on first API call
2. Parallel `get_organizations` share one token (token_version stable / single auth)
3. Forced 401 path: invalidate `access_token` then call → refresh succeeds (if feasible without harming write org)

- [ ] Run: `uv run pytest tests/integration/session -v` (needs config)
- [ ] Commit `test: real API auth and concurrency on write credentials`

---

### Task 13: Integration — read domains

**Files:**
- Create:
  - `tests/integration/organizations/test_read.py`
  - `tests/integration/terminal_groups/test_read.py`
  - `tests/integration/menu/test_read.py`
  - `tests/integration/dictionaries/test_read.py`

Markers: `integration`, `slow` (no `write`). Assert non-empty structures / types; skip if org/menu missing.

Migrate valuable assertions from old `tests/test_integration.py`; replace hardcoded UUIDs with fixtures.

- [ ] Run read suite
- [ ] Commit `test: real API read coverage for MVP domains`

---

### Task 14: Integration — customers write lifecycle

**Files:**
- Create: `tests/integration/customers/test_lifecycle.py`

Markers: `integration`, `slow`, `write`, `lifecycle`.

Flow:

1. `create_or_update_customer` with random phone on `organization_id`
2. `get_customer_by_phone` finds them
3. `delete_customers`
4. `restore_customers`
5. Final delete/cleanup in `finally`

Use unique phone generator (keep from old tests). Never run against read credentials.

- [ ] Run: `uv run pytest -m "write and lifecycle" -v`
- [ ] Commit `test: customer lifecycle against write credentials`

---

### Task 15: Remove legacy tests/files + final verification

**Files:**
- Delete: `tests/test_api_client_manager.py`, `tests/test_token_manager.py`, `tests/test_rate_limiter.py`, `tests/test_exceptions.py`, `tests/test_integration.py` (after migration)
- Ensure: `tests/unit/test_rate_limiter.py`, `tests/unit/test_exceptions.py` exist (move/adapt)
- Optional: remove `response_text.json` from tree if unused (do not commit secrets)

- [ ] **Step 1: Move remaining unit tests for rate_limiter/exceptions**

- [ ] **Step 2: Full unit suite**

```bash
uv run pytest -m unit -v
```

Expected: all PASS, no network.

- [ ] **Step 3: Full integration suite**

```bash
uv run pytest -m integration -v
```

Expected: PASS with local `config.test.yml`, or skip if env missing in CI.

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: drop legacy flat tests after mixin rewrite"
```

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| Mixins + thin facade | 4–9 |
| Auth v2 only | 2, 3 |
| Dual rate limits in execute_with_retry | 4 |
| key_id fingerprint | 4 |
| MVP 5 domains | 5–9 |
| Naming by return semantics | Locked Names + domain tasks |
| config.test.yml read/write | 1, 11 |
| Real API tests | 12–14 |
| Packaging git SDK + pydantic direct | 1 |
| README / examples | 1, 10 |
| Phase B readiness | mixin layout |
| Secrets gitignored | done in prior commit; Task 1 verify |

No TBD placeholders remain for implementers: SDK kwarg names must be confirmed from installed package signatures at coding time (one-line `inspect.signature` check — not a design gap).

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-23-iikocloud-manager-mvp.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with checkpoints  

Which approach?
