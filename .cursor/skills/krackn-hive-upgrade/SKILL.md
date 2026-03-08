---
name: krackn-hive-upgrade
description: Apply the krackn-hive upgrade plan: fix merge conflicts, duplicate code, and infrastructure. Use when upgrading krackn-hive, resolving merge conflicts in swarm/api/storage, or implementing the upgrade TODO.
---

# Krackn Hive Upgrade Workflow

## Order of Fixes

1. **models.py** – Add `idempotency_key`, `lease_owner`, `lease_expires_at` to HiveTask; fix conditional SQLAlchemy; remove overwriting class definitions.
2. **storage.py** – Single implementation per method; lease-based `assign_task`; unified `abandon_stale_assignments`.
3. **swarm.py** – Remove duplicate `__init__`, `submit_task`, `emit_signal`, `assign_next`, `submit_artifact`; fix CloudEvent (one `type=`); fix imports and orphan blocks.
4. **api.py** – Single `POST /tasks` (with `_task_read` and idempotency); single `dispatch` with `lease_seconds`; remove orphan `)`; fix imports.
5. **event_bus.py** – Fix Redis conditional; fix double-publish in Redis bus.
6. **abandonment.py**, **tests/test_swarm.py** – Remove duplicate `type=` in CloudEvent; fix duplicate imports/assertions.

## Conventions When Fixing

- Use `EventType.task_created.value` (and other enum values) for CloudEvent `type`, not raw `"hive.task.created"`.
- One CloudEvent per publish; no duplicate `type=` keys.
- Keep lease-based flow: `planned` → `triaged`, `lease_seconds`, `lease_owner`, `lease_expires_at`.
- Implement `_task_read(task)` and use it in `create_task`; handle missing `lease_owner`/`lease_expires_at` safely until models support them.
