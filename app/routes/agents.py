from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import Agent as DBAgent, Chat as DBChat
from app.models.schemas import Agent, Chat
from app.dependencies import get_db

router = APIRouter()

@router.post("/agents", response_model=Agent)
async def create_agent(agent: Agent, db: Session = Depends(get_db)):
    db_agent = DBAgent(id=agent.id, knowledge_base_path=agent.knowledge_base_path)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    db_agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent

@router.post("/agents/{agent_id}/chats", response_model=Chat)
async def create_chat(agent_id: str, chat: Chat, db: Session = Depends(get_db)):
    db_chat = DBChat(id=chat.id, agent_id=agent_id, messages="[]")
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

@router.get("/agents/{agent_id}/chats/{chat_id}", response_model=Chat)
async def get_chat(agent_id: str, chat_id: str, db: Session = Depends(get_db)):
    db_chat = db.query(DBChat).filter(DBChat.id == chat_id, DBChat.agent_id == agent_id).first()
    if not db_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return db_chat 