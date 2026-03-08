"""Integration tests for the API. Requires database (set KRACKN_DATABASE_URL)."""

import pytest
from httpx import ASGITransport, AsyncClient

from krackn_hive.db import engine
from krackn_hive.main import app
from krackn_hive.models import Base


@pytest.fixture(scope="module", autouse=True)
def ensure_schema():
    """Create tables before integration tests. Lifespan runs per-request; ensure schema exists."""
    import asyncio

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield


@pytest.mark.asyncio
async def test_summary_endpoint():
    """GET /api/summary returns HiveSummary."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "discovered" in data
    assert "triaged" in data
    assert "done" in data


@pytest.mark.asyncio
async def test_create_task_flow():
    """POST /api/tasks creates a task and returns TaskRead."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/tasks",
            json={"goal": "test goal", "priority": 1.0, "constraints": {}},
        )
    if resp.status_code == 500 and "connection" in str(resp.json().get("detail", "")).lower():
        pytest.skip("Database not available")
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["goal"] == "test goal"
    assert data["status"] == "triaged"
