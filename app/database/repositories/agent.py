from typing import Optional
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.agent import Agent
from .base import BaseRepository

class AgentRepository(BaseRepository[Agent]):
    async def create(self, **kwargs) -> Agent:
        agent = Agent(**kwargs)
        self.session.add(agent)
        await self.session.commit()
        return agent

    async def get(self, agent_id: UUID) -> Optional[Agent]:
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalars().first()

    async def update(self, agent_id: UUID, **kwargs) -> Optional[Agent]:
        await self.session.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(**kwargs)
        )
        await self.session.commit()
        return await self.get(agent_id)

    async def delete(self, agent_id: UUID) -> bool:
        await self.session.execute(
            delete(Agent).where(Agent.id == agent_id)
        )
        await self.session.commit()
        return True

    async def get_by_name(self, name: str) -> Optional[Agent]:
        result = await self.session.execute(
            select(Agent).where(Agent.name == name)
        )
        return result.scalars().first()