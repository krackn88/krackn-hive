# 🐝 Krackn Hive

**Krackn Hive** is a honey-bee inspired autonomous engineering swarm: a Queen orchestrates intent, Scouts emit discovery signals, Workers execute, Guards validate, and Drones specialize.

Production-ready kernel on **FastAPI + Postgres + Redis**.

## Quick start

### Docker (recommended)

```bash
docker compose up -d
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Local

```bash
# 1. Copy env and set database
cp .env.example .env
# Edit .env: set KRACKN_DATABASE_URL (e.g. postgres or sqlite+aiosqlite:///./hive.db)

# 2. Migrate (Postgres) or create schema (SQLite via lifespan)
alembic upgrade head   # Postgres only

# 3. Run
pip install -e .
uvicorn krackn_hive.main:app --reload
```

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `KRACKN_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/krackn_hive` | Database URL |
| `KRACKN_REDIS_URL` | `redis://localhost:6379/0` | Redis URL (when event_bus=redis) |
| `KRACKN_EVENT_BUS` | `memory` | `memory` or `redis` |
| `KRACKN_ABANDONMENT_TTL_SECONDS` | `900` | Stale lease reclaim threshold |
| `KRACKN_GLOBAL_BUDGET_TOKENS` | `100` | Nectar budget tuning |

## Core mechanics

### 1) Dance Floor Event Bus
- `InMemoryEventBus` for local/dev
- `RedisDanceFloorEventBus` when `KRACKN_EVENT_BUS=redis`
- CloudEvent envelope, pattern subscriptions (`hive.task.*`, `hive.signal.*`, ...)

### 2) Comb Cell Storage
- `hive_tasks`, `hive_signals`, `hive_agents`, `hive_artifacts`, `agent_roles`
- Lifecycle transitions, lease ownership, abandonment sweeper

### 3) Nectar Economy
- `NectarEconomyScheduler`, `RewardEngine`, budget checks, per-assignment leases

### 4) Task Lifecycle + Abandonment
- State machine in `lifecycle.py`, guarded transitions, stale-assignment reclaim

### 5) Guardrails
- Policy engine (exfiltration/destructive patterns), artifact SHA256 provenance

### 6) Agent Caste Registry
- Role registry, agent registration, queen/scout/worker/guard/drone scaffolds

## API

- `POST /api/tasks` – create + triage (idempotency key)
- `POST /api/tasks/{task_id}/transition` – state transition
- `POST /api/signals` – emit waggle signals
- `POST /api/tasks/{task_id}/artifacts` – submit for guard validation
- `POST /api/roles` – register role capabilities
- `POST /api/dispatch/{role_name}` – role-aware dispatch + lease TTL
- `POST /api/agents` – register agent
- `GET /api/summary` – task counts by state
- `POST /api/tasks/{task_id}/lease/renew` – renew lease
- `POST /api/abandonment/sweep` – reclaim stale leases

## Dev

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check krackn_hive tests
```

## Next

- OTel traces + metrics
- Signed provenance for artifact approvals
- Rate limiting, auth
