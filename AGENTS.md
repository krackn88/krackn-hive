# Agent Guidance for Krackn Hive

## Project Overview

Krackn Hive is a honey-bee inspired swarm for engineering task management: Queen, Scouts, Workers, Guards, Drones. Stack: FastAPI, SQLAlchemy 2.0 async, Postgres, Redis (optional), Pydantic 2.

## Upgrade Plan

See `.cursor/plans/` for the upgrade TODO. Phase 1 (critical) fixes merge conflicts and duplicate code in:

- `krackn_hive/swarm.py`
- `krackn_hive/api.py`
- `krackn_hive/storage.py`
- `krackn_hive/models.py`
- `krackn_hive/event_bus.py`
- `krackn_hive/abandonment.py`
- `tests/test_swarm.py`

Fix order: `models.py` → `storage.py` → `swarm.py` → `api.py` → event_bus, abandonment, tests.

## Key Files

| File | Purpose |
|------|---------|
| `krackn_hive/swarm.py` | HiveSwarmService: submit_task, assign_next, emit_signal, submit_artifact |
| `krackn_hive/api.py` | FastAPI router, /tasks, /signals, /dispatch, etc. |
| `krackn_hive/storage.py` | CombRepository: DB operations |
| `krackn_hive/models.py` | SQLAlchemy models (HiveTask, HiveSignal, etc.) |
| `krackn_hive/event_bus.py` | InMemoryEventBus, RedisDanceFloorEventBus |
| `krackn_hive/schemas.py` | Pydantic schemas (TaskCreate, CloudEvent, etc.) |
| `krackn_hive/lifecycle.py` | Task state machine and valid transitions |

## Conventions

- Use `EventType.task_created.value` for CloudEvent `type`, not raw strings.
- One implementation per repository method; remove duplicate/merge-conflict blocks.
- HiveTask must include `idempotency_key`, `lease_owner`, `lease_expires_at` for full flow.
- Use `asyncio_mode = "auto"` and `@pytest.mark.asyncio` for async tests.
