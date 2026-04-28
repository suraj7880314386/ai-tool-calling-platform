"""Database models for execution history and audit trail."""

from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Execution(Base):
    """Records every agent execution."""
    __tablename__ = "executions"

    id = Column(String(16), primary_key=True)
    session_id = Column(String(64), index=True, default="default")
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    status = Column(String(20), default="success")
    total_duration_ms = Column(Float, default=0.0)
    retries_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tool_calls = relationship("ToolCallRecord", back_populates="execution", cascade="all, delete-orphan")
    thoughts = relationship("AgentThoughtRecord", back_populates="execution", cascade="all, delete-orphan")


class ToolCallRecord(Base):
    """Records individual tool calls within an execution."""
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(16), ForeignKey("executions.id"), nullable=False)
    tool_name = Column(String(50), nullable=False)
    tool_input = Column(Text, nullable=False)
    tool_output = Column(Text, nullable=True)
    duration_ms = Column(Float, default=0.0)
    success = Column(Integer, default=1)  # SQLite boolean
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="tool_calls")


class AgentThoughtRecord(Base):
    """Records the agent's reasoning chain."""
    __tablename__ = "agent_thoughts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(16), ForeignKey("executions.id"), nullable=False)
    step = Column(Integer, nullable=False)
    thought = Column(Text, nullable=True)
    action = Column(String(100), nullable=True)
    action_input = Column(Text, nullable=True)
    observation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="thoughts")


class SampleData(Base):
    """Sample data table for the database query tool to work with."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False)
    role = Column(String(50), default="user")
    signup_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)


class Product(Base):
    """Sample products table for database queries."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
