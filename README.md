# Krackn Hive

Production-oriented honey-bee inspired swarm architecture for engineering automation, built with **FastAPI + Redis + Postgres**.

## What is implemented

- **Dance floor event bus**
  - `InMemoryEventBus` for local deterministic behavior
  - `RedisDanceFloorEventBus` for distributed pub/sub
- **Comb cell storage**
  - Postgres-ready SQLAlchemy models for tasks, signals, agents, artifacts, and role registry
- **Nectar economy scheduler**
  - Role-budgeted allocation model via `NectarEconomyScheduler`
- **Pheromone/reward scoring**
  - `RewardEngine` ranks signals by score/confidence/trust vs cost
- **Task abandonment**
  - TTL sweeper marks stale assigned/active tasks as blocked and emits state-change events
- **Agent role registry**
  - Role capabilities and concurrency limits persisted in `agent_roles`
- **Agent castes scaffold**
  - Queen, Scout, Worker, Guard, Drone classes under `krackn_hive/agents`

## API

- `POST /api/tasks` – create hive task
- `POST /api/signals` – emit waggle signal
- `POST /api/roles` – register role
- `POST /api/dispatch/{role_name}` – assign next task to role budget
- `POST /api/agents` – register agent profile
- `POST /api/abandonment/sweep` – reclaim stale tasks

## Run

```bash
uvicorn krackn_hive.main:app --reload
```
