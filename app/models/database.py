from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import json

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(String, primary_key=True)
    knowledge_base_path = Column(String, nullable=False)
    chats = relationship("Chat", back_populates="agent")

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    messages = Column(String)  # Store messages as a JSON string
    agent = relationship("Agent", back_populates="chats")

    def add_message(self, message: str):
        messages = json.loads(self.messages)
        messages.append(message)
        self.messages = json.dumps(messages)

# Create an engine and session
engine = create_engine('sqlite:///app.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine) 