from sqlalchemy.orm import Session
from app.models.database import Chat, Message
from typing import List, Optional

class ChatManager:
    def __init__(self, db: Session):
        self.db = db

    async def get_chat_history(
        self, 
        agent_id: str, 
        chat_id: str,
        limit: Optional[int] = None
    ) -> List[str]:
        query = self.db.query(Message).join(Chat).filter(
            Chat.id == chat_id,
            Chat.agent_id == agent_id
        ).order_by(Message.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        messages = query.all()
        return [msg.content for msg in reversed(messages)]

    async def save_message(
        self,
        chat_id: str,
        content: str,
        role: str = "user"
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            content=content,
            role=role
        )
        self.db.add(message)
        self.db.commit()
        return message 