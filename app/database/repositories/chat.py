from typing import Optional
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.chat import Chat
from .base import BaseRepository

class ChatRepository(BaseRepository[Chat]):
    async def create(self, **kwargs) -> Chat:
        chat = Chat(**kwargs)
        self.session.add(chat)
        await self.session.commit()
        return chat

    async def get(self, chat_id: UUID) -> Optional[Chat]:
        result = await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        return result.scalars().first()

    async def update(self, chat_id: UUID, **kwargs) -> Optional[Chat]:
        await self.session.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(**kwargs)
        )
        await self.session.commit()
        return await self.get(chat_id)

    async def delete(self, chat_id: UUID) -> bool:
        await self.session.execute(
            delete(Chat).where(Chat.id == chat_id)
        )
        await self.session.commit()
        return True

    async def get_agent_chats(self, agent_id: UUID) -> list[Chat]:
        result = await self.session.execute(
            select(Chat).where(Chat.agent_id == agent_id)
        )
        return result.scalars().all()