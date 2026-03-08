from sqlalchemy.ext.asyncio import AsyncSession

from .models import AgentRole
from .storage import CombRepository


class AgentRoleRegistry:
    def __init__(self, session: AsyncSession):
        self.repo = CombRepository(session)

    async def register(self, name: str, capabilities: list[str], concurrency_limit: int) -> AgentRole:
        return await self.repo.upsert_role(name, capabilities, concurrency_limit)
