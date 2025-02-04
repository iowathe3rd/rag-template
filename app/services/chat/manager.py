from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.chat import Chat
from app.schemas.chat import Chat as ChatSchema, ChatMessage as ChatMessageSchema
from app.database.repositories import ChatRepository

class ChatManager:
    def __init__(self, db: AsyncSession):
        self.chat_repository = ChatRepository(db)

    async def create_chat(self, agent_id: str, chat_data: ChatSchema) -> Chat:
        return await self.chat_repository.create(
            agent_id=agent_id,
            title=chat_data.title,
            chat_metadata={}
        )

    async def get_chat(self, chat_id: str) -> Chat:
        chat = await self.chat_repository.get(chat_id)
        if not chat:
            raise ValueError(f"Chat with id {chat_id} not found")
        return chat

    async def update_chat(self, chat_id: str, chat_data: ChatSchema) -> Chat:
        chat = await self.chat_repository.update(
            chat_id,
            title=chat_data.title,
            chat_metadata={}
        )
        if not chat:
            raise ValueError(f"Chat with id {chat_id} not found")
        return chat

    async def delete_chat(self, chat_id: str) -> bool:
        return await self.chat_repository.delete(chat_id)

    async def get_agent_chats(self, agent_id: str) -> List[Chat]:
        return await self.chat_repository.get_agent_chats(agent_id)

    async def get_chat_history(self, agent_id: str, chat_id: str) -> str:
        chat = await self.get_chat(chat_id)
        messages = [
            f"{message.role}: {message.content}"
            for message in chat.messages
        ]
        return "\n".join(messages)

    async def add_message_to_chat(self, chat_id: str, message: ChatMessageSchema) -> Chat:
        chat = await self.get_chat(chat_id)
        chat.messages.append(message)
        return await self.chat_repository.update(chat_id, messages=chat.messages) 