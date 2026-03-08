from __future__ import annotations

from .models import TaskState

ALLOWED_TASK_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.discovered: {TaskState.triaged, TaskState.rejected, TaskState.archived},
    TaskState.triaged: {TaskState.planned, TaskState.rejected, TaskState.archived},
    TaskState.planned: {TaskState.assigned, TaskState.blocked, TaskState.archived},
    TaskState.assigned: {TaskState.active, TaskState.blocked, TaskState.archived},
    TaskState.active: {TaskState.review, TaskState.blocked, TaskState.archived},
    TaskState.review: {TaskState.done, TaskState.active, TaskState.rejected, TaskState.archived},
    TaskState.done: {TaskState.archived},
    TaskState.blocked: {TaskState.planned, TaskState.archived},
    TaskState.rejected: {TaskState.archived},
    TaskState.archived: set(),
}


def can_transition(current: TaskState, target: TaskState) -> bool:
    return target in ALLOWED_TASK_TRANSITIONS.get(current, set())
