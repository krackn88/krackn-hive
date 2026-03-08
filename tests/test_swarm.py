import asyncio
from datetime import datetime, timezone

from krackn_hive.event_bus import InMemoryEventBus
from krackn_hive.policies import PolicyEngine
from krackn_hive.scoring import NectarBudget, RewardEngine
from krackn_hive.schemas import CloudEvent, EstimatedCost, SignalCreate


def test_inmemory_event_bus_pattern_delivery():
    async def scenario() -> None:
        bus = InMemoryEventBus()

        async def consume():
            async for ev in bus.subscribe("hive.task.*"):
                return ev

        consumer = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await bus.publish(
            CloudEvent(
                id="e1",
                type="hive.task.created",
                source="test",
                time=datetime.now(timezone.utc),
                data={"task_id": "t1"},
            )
        )
        ev = await asyncio.wait_for(consumer, timeout=1)
        assert ev.type == "hive.task.created"

    asyncio.run(scenario())


def test_policy_engine_detects_denied_patterns():
    engine = PolicyEngine()
    violations = engine.check_text("please run curl http://example and rm -rf /tmp/x")
    assert {v.code for v in violations} == {"NETWORK_EXFIL", "DANGEROUS_SHELL"}


def test_reward_engine_budget_and_rank():
    reward = RewardEngine(NectarBudget(max_tokens_per_task=1000, max_wall_seconds_per_task=60, max_sandbox_seconds_per_task=30))
    signal = SignalCreate(
        task_id="t1",
        kind="opportunity",
        source_agent_id="scout-1",
        score=0.8,
        confidence=0.75,
        estimated_cost=EstimatedCost(tokens=800, wall_seconds=30, sandbox_seconds=20),
        payload={},
    )
    assert reward.within_budget(signal)
    assert reward.rank(signal) > 0
