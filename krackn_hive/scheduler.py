from dataclasses import dataclass


@dataclass(slots=True)
class NectarEconomyScheduler:
    scout_fraction: float = 0.2
    worker_fraction: float = 0.65
    guard_fraction: float = 0.15

    def budget_for_role(self, global_budget: int, role: str, queued_tasks: int) -> int:
        ratio = {
            "scout": self.scout_fraction,
            "worker": self.worker_fraction,
            "guard": self.guard_fraction,
            "drone": 0.1,
            "queen": 0.05,
        }.get(role, 0.1)
        return max(1, min(global_budget, int(global_budget * ratio), queued_tasks + 1))
