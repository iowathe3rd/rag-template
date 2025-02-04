from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Agent as DBAgent, Chat as DBChat
from app.schemas.agent import Agent
from app.schemas.chat import Chat
from app.database.session import get_db
import logging

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# Agent Creation Endpoint
@router.post("/agents", response_model=Agent)
async def create_agent(agent: Agent, db: AsyncSession = Depends(get_db)):
    """
    Create a new agent with specified configuration.
    
    This endpoint initializes a new agent with custom configuration for the RAG system.
    Each agent maintains its own knowledge base and chat history.
    
    Args:
        agent: Agent configuration including name, description, and configs
        db: Database session for persistence
        
    Returns:
        The created agent object with generated ID
        
    Raises:
        HTTPException: If agent creation fails
    """
    try:
        # Create new agent record
        db_agent = DBAgent(
            name=agent.name,
            description=agent.description,
        )
        db.add(db_agent)
        await db.commit()
        await db.refresh(db_agent)
        logger.info(f"Agent created: {db_agent}")
        return db_agent
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Agent Retrieval Endpoint
@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve an existing agent's details.
    
    This endpoint fetches the complete configuration and metadata for a specific agent.
    
    Args:
        agent_id: Unique identifier for the agent
        db: Database session for queries
        
    Returns:
        The agent object if found
        
    Raises:
        HTTPException: If agent not found (404)
    """
    db_agent = await db.get(DBAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent

# Chat Creation Endpoint
@router.post("/agents/{agent_id}/chats", response_model=Chat)
async def create_chat(agent_id: str, chat: Chat, db: AsyncSession = Depends(get_db)):
    """
    Create a new chat session for a specific agent.
    
    This endpoint creates a new chat session associated with a particular agent.
    It allows for tracking conversations and maintaining context.
    
    Args:
        agent_id: ID of the agent to associate the chat with
        chat: Chat configuration including title and metadata
        db: Database session for persistence
        
    Returns:
        The created chat session object
        
    Raises:
        HTTPException: If chat creation fails
    """
    try:
        # Create new chat session
        db_chat = DBChat(agent_id=agent_id, title=chat.title, metadata=chat.metadata)
        db.add(db_chat)
        await db.commit()
        await db.refresh(db_chat)
        logger.info(f"Chat created: {db_chat}")
        return db_chat
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Chat Retrieval Endpoint
@router.get("/agents/{agent_id}/chats/{chat_id}", response_model=Chat)
async def get_chat(agent_id: str, chat_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve details of an existing chat session.
    
    This endpoint fetches the chat history and metadata for a specific chat session.
    
    Args:
        agent_id: ID of the associated agent
        chat_id: Unique identifier for the chat session
        db: Database session for queries
        
    Returns:
        The chat session object if found
        
    Raises:
        HTTPException: If chat not found (404)
    """
    db_chat = await db.get(DBChat, chat_id)
    if not db_chat or db_chat.agent_id != agent_id:
        logger.warning(f"Chat not found: agent_id={agent_id}, chat_id={chat_id}")
        raise HTTPException(status_code=404, detail="Chat not found")
    logger.info(f"Chat retrieved: {db_chat}")
    return db_chat 