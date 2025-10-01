"""
Aurora Pro AI - Database Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Agent(Base):
    """Agent model for multi-agent orchestration"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    description = Column(Text)
    config = Column(JSON, default={})
    status = Column(String(50), default="inactive")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """Task model for agent execution tracking"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    result = Column(Text)
    task_metadata = Column(JSON, default={})
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Model(Base):
    """Model registry for AI models"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    model_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    version = Column(String(50))
    config = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    """Conversation history for agents"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    agent_id = Column(Integer, nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class Metric(Base):
    """Performance metrics"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    value = Column(Float, nullable=False)
    tags = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class Plugin(Base):
    """Plugin registry"""
    __tablename__ = "plugins"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    config = Column(JSON, default={})
    is_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
