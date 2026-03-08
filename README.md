# 🐝 Krackn Hive

**Krackn Hive** is a honey-bee inspired autonomous engineering swarm: a Queen orchestrates intent, Scouts emit discovery signals, Workers execute, Guards validate, and Drones specialize.

This repo now includes a richer **production-oriented kernel** on top of **FastAPI + Postgres + Redis** patterns.

## Core mechanics implemented

### 1) Dance Floor Event Bus
- `InMemoryEventBus` for deterministic local runs/test
- `RedisDanceFloorEventBus` for distributed pub/sub
- Pattern subscriptions (`hive.task.*`, `hive.signal.*`, ...)
- CloudEvent envelope (`id`, `type`, `source`, `subject`, trace fields)

### 2) Comb Cell Storage
Durable entities modeled for swarm operation:
- `hive_tasks`
- `hive_signals`
- `hive_agents`
- `hive_artifacts`
- `agent_roles`

Repository includes:
- lifecycle-safe transitions with transition guardrails
- best-signal lookup per task
- assignment + lease ownership/expiry, agent heartbeat, stale-assignment abandonment
- role upsert/lookup and task-state summary

### 3) Nectar Economy + Pheromone Intelligence
- `NectarEconomyScheduler` allocates budget by role fractions
- `RewardEngine` evaluates score/confidence/trust vs cost
- signal budget checks convert over-budget opportunities to warnings
- task dispatch prioritizes task priority + signal quality and issues per-assignment leases

### 4) Task Lifecycle + Abandonment
- explicit state machine in `lifecycle.py`
- guarded transitions (invalid transitions produce conflict errors)
- abandonment sweeper reclaims stale active/assigned work and emits events

### 5) Guardrails
- policy engine detects denied command patterns (exfiltration/destructive shell)
- artifact submission path computes SHA256, stores provenance metadata, and applies guard approval/rejection semantics

### 6) Agent Caste Registry + Scaffolds
- role registry persists role capabilities/concurrency
- agent registration endpoint persists caste profiles
- queen/scout/worker/guard/drone agent class scaffolds included for autonomous loop expansion

## API surface

- `POST /api/tasks` – create + triage a task (supports idempotency key)
- `POST /api/tasks/{task_id}/transition` – move task through state machine
- `POST /api/signals` – emit waggle signals
- `POST /api/tasks/{task_id}/artifacts` – submit artifact for guard validation (idempotent submissions)
- `POST /api/roles` – register/update role capabilities
- `POST /api/dispatch/{role_name}` – role-aware dispatch decision + lease TTL
- `POST /api/agents` – register/update agent profile
- `GET /api/summary` – task counts by state
- `POST /api/tasks/{task_id}/lease/renew` – renew active task lease
- `POST /api/abandonment/sweep` – reclaim expired leases

## Run

```bash
uvicorn krackn_hive.main:app --reload
```

## Next upgrades
- Replace in-memory bus with Redis/Kafka adapter in runtime composition
- Add ack/retry delivery semantics for worker execution events
- Add OTel traces + metrics
- Add signed provenance/attestation emission for artifact approvals
