from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import Agent as DBAgent, Chat as DBChat
from app.models.schemas import Agent, Chat
from app.dependencies import get_db

router = APIRouter()

@router.post("/agents", response_model=Agent)
async def create_agent(agent: Agent, db: Session = Depends(get_db)):
    """
    Create a new agent.

    This endpoint allows you to create a new agent with a specified knowledge base path.

    Args:
        agent: The agent data including ID and knowledge base path.

    Returns:
        The created agent object.
    """
    db_agent = DBAgent(id=agent.id, knowledge_base_path=agent.knowledge_base_path)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    Retrieve an agent by ID.

    This endpoint allows you to retrieve an agent's details using their ID.

    Args:
        agent_id: The ID of the agent to retrieve.

    Returns:
        The agent object if found, otherwise raises a 404 error.
    """
    db_agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent

@router.post("/agents/{agent_id}/chats", response_model=Chat)
async def create_chat(agent_id: str, chat: Chat, db: Session = Depends(get_db)):
    """
    Create a new chat session for an agent.

    This endpoint allows you to create a new chat session associated with a specific agent.

    Args:
        agent_id: The ID of the agent for whom the chat is being created.
        chat: The chat data including ID and initial messages.

    Returns:
        The created chat object.
    """
    db_chat = DBChat(id=chat.id, agent_id=agent_id, messages="[]")
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

@router.get("/agents/{agent_id}/chats/{chat_id}", response_model=Chat)
async def get_chat(agent_id: str, chat_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a chat session by ID.

    This endpoint allows you to retrieve the details of a chat session using its ID and the associated agent ID.

    Args:
        agent_id: The ID of the agent associated with the chat.
        chat_id: The ID of the chat session to retrieve.

    Returns:
        The chat object if found, otherwise raises a 404 error.
    """
    db_chat = db.query(DBChat).filter(DBChat.id == chat_id, DBChat.agent_id == agent_id).first()
    if not db_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return db_chat 