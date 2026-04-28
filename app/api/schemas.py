"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────

class ToolName(str, Enum):
    SEARCH = "web_search"
    CALCULATOR = "calculator"
    DATABASE = "database_query"
    WIKIPEDIA = "wikipedia"
    WEATHER = "weather"


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRIED = "retried"


# ─── Request Models ───────────────────────────────────────

class ExecuteRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User query for the agent")
    tools: Optional[List[ToolName]] = Field(
        default=None,
        description="Specific tools to use. If None, agent auto-selects."
    )
    max_retries: Optional[int] = Field(default=None, ge=0, le=5)
    session_id: str = Field(default="default", description="Session ID for context")

    model_config = {"json_schema_extra": {
        "examples": [{
            "query": "What is the square root of 144 plus the population of Japan?",
            "tools": None,
            "session_id": "user-123"
        }]
    }}


class StreamExecuteRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default")


# ─── Response Models ──────────────────────────────────────

class ToolCall(BaseModel):
    tool_name: str
    tool_input: str
    tool_output: str
    duration_ms: float
    success: bool


class AgentThought(BaseModel):
    step: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None


class ExecuteResponse(BaseModel):
    execution_id: str
    query: str
    answer: str
    status: ExecutionStatus
    tool_calls: List[ToolCall] = []
    agent_thoughts: List[AgentThought] = []
    total_duration_ms: float
    retries_used: int = 0
    session_id: str


class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    examples: List[str] = []


class ToolListResponse(BaseModel):
    tools: List[ToolInfo]
    total: int


class HistoryEntry(BaseModel):
    execution_id: str
    query: str
    answer: str
    status: ExecutionStatus
    tools_used: List[str]
    duration_ms: float
    created_at: datetime


class HistoryResponse(BaseModel):
    entries: List[HistoryEntry]
    total: int


class HealthResponse(BaseModel):
    status: str
    database: str
    llm: str
    tools_available: int
    uptime_seconds: float


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    retry_after: Optional[int] = None
