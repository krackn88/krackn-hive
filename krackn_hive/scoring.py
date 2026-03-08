from dataclasses import dataclass

from .schemas import SignalCreate


@dataclass(slots=True)
class NectarBudget:
    max_tokens_per_task: int = 50_000
    max_wall_seconds_per_task: int = 900
    max_sandbox_seconds_per_task: int = 600


class RewardEngine:
    def __init__(self, budget: NectarBudget):
        self._budget = budget
        self._trust: dict[str, float] = {}

    def within_budget(self, signal: SignalCreate) -> bool:
        cost = signal.estimated_cost
        return (
            cost.tokens <= self._budget.max_tokens_per_task
            and cost.wall_seconds <= self._budget.max_wall_seconds_per_task
            and cost.sandbox_seconds <= self._budget.max_sandbox_seconds_per_task
        )

    def rank(self, signal: SignalCreate) -> float:
        trust = self._trust.get(signal.source_agent_id, 1.0)
        cost = 1.0 + (signal.estimated_cost.tokens / 10000.0) + (signal.estimated_cost.wall_seconds / 60.0)
        return (signal.score * signal.confidence * trust) / cost
