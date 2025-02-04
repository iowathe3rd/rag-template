from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.agent import Agent
from app.schemas.agent import Agent as AgentSchema
from app.database.repositories import AgentRepository

class AgentManager:
    def __init__(self, db: AsyncSession):
        self.agent_repository = AgentRepository(db)

    async def create_agent(self, agent_data: AgentSchema) -> Agent:
        return await self.agent_repository.create(
            name=agent_data.name,
            description=agent_data.description
        )

    async def get_agent(self, agent_id: str) -> Agent:
        agent = await self.agent_repository.get(agent_id)
        if not agent:
            raise ValueError(f"Agent with id {agent_id} not found")
        return agent

    async def get_agent_by_name(self, name: str) -> Agent:
        agent = await self.agent_repository.get_by_name(name)
        if not agent:
            raise ValueError(f"Agent with name {name} not found")
        return agent

    async def update_agent(self, agent_id: str, agent_data: AgentSchema) -> Agent:
        agent = await self.agent_repository.update(
            agent_id,
            name=agent_data.name,
            description=agent_data.description
        )
        if not agent:
            raise ValueError(f"Agent with id {agent_id} not found")
        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        return await self.agent_repository.delete(agent_id) 