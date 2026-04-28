"""API route definitions."""

import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.api.schemas import (
    ExecuteRequest,
    ExecuteResponse,
    ToolListResponse,
    ToolInfo,
    HistoryResponse,
    HistoryEntry,
    HealthResponse,
    ExecutionStatus,
    ToolCall,
    AgentThought,
)
from app.agents.executor import agent_manager
from app.tools.registry import tool_registry
from app.core.history import history_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Agent Platform"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# ─── Execute Endpoints ────────────────────────────────────

@router.post("/execute", response_model=ExecuteResponse)
async def execute_agent(request: ExecuteRequest):
    """
    Execute the AI agent with automatic tool selection.
    The agent analyzes the query, selects appropriate tools,
    and chains them if needed to produce a final answer.
    """
    try:
        tool_names = [t.value for t in request.tools] if request.tools else None

        result = agent_manager.execute(
            query=request.query,
            session_id=request.session_id,
            tool_names=tool_names,
        )

        return ExecuteResponse(
            execution_id=result["execution_id"],
            query=result["query"],
            answer=result["answer"],
            status=ExecutionStatus(result["status"]),
            tool_calls=[
                ToolCall(
                    tool_name=tc["tool_name"],
                    tool_input=tc["tool_input"],
                    tool_output=tc["tool_output"],
                    duration_ms=tc["duration_ms"],
                    success=tc["success"],
                )
                for tc in result["tool_calls"]
            ],
            agent_thoughts=[
                AgentThought(
                    step=t["step"],
                    thought=t["thought"],
                    action=t.get("action"),
                    action_input=t.get("action_input"),
                    observation=t.get("observation"),
                )
                for t in result["agent_thoughts"]
            ],
            total_duration_ms=result["total_duration_ms"],
            retries_used=result.get("retries_used", 0),
            session_id=result["session_id"],
        )

    except Exception as e:
        logger.error(f"Execute failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/stream")
async def stream_execute(request: ExecuteRequest):
    """Stream agent execution with real-time thought process via SSE."""

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'start', 'query': request.query})}\n\n"

            tool_names = [t.value for t in request.tools] if request.tools else None
            result = agent_manager.execute(
                query=request.query,
                session_id=request.session_id,
                tool_names=tool_names,
            )

            # Stream thoughts
            for thought in result.get("agent_thoughts", []):
                yield f"data: {json.dumps({'type': 'thought', 'data': thought})}\n\n"

            # Stream tool calls
            for tc in result.get("tool_calls", []):
                yield f"data: {json.dumps({'type': 'tool_call', 'data': tc})}\n\n"

            # Stream answer
            answer = result["answer"]
            chunk_size = 40
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'answer_chunk', 'content': chunk})}\n\n"

            # Done
            yield f"data: {json.dumps({'type': 'done', 'execution_id': result['execution_id'], 'duration_ms': result['total_duration_ms']})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─── Tool Endpoints ───────────────────────────────────────

@router.get("/tools", response_model=ToolListResponse)
async def list_tools():
    """List all available tools with descriptions and examples."""
    tools = tool_registry.list_tools()
    return ToolListResponse(
        tools=[
            ToolInfo(
                name=t["name"],
                description=t["description"],
                parameters=t.get("parameters", {}),
                examples=t.get("examples", []),
            )
            for t in tools
        ],
        total=len(tools),
    )


@router.get("/tools/{name}")
async def get_tool_info(name: str):
    """Get detailed information about a specific tool."""
    info = tool_registry.get_tool_info(name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found")
    return info


# ─── History Endpoints ────────────────────────────────────

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    session_id: str = Query(default=None),
):
    """Get agent execution history."""
    entries = history_manager.get_history(limit=limit, session_id=session_id)

    return HistoryResponse(
        entries=[
            HistoryEntry(
                execution_id=e["execution_id"],
                query=e["query"],
                answer=e.get("answer", ""),
                status=ExecutionStatus(e["status"]),
                tools_used=e.get("tools_used", []),
                duration_ms=e.get("duration_ms", 0),
                created_at=e["created_at"],
            )
            for e in entries
        ],
        total=len(entries),
    )


@router.get("/history/{execution_id}")
async def get_execution_detail(execution_id: str):
    """Get full details of a specific execution."""
    detail = history_manager.get_execution(execution_id)
    if not detail:
        raise HTTPException(
            status_code=404, detail=f"Execution {execution_id} not found"
        )
    return detail


# ─── Health ───────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    import time
    start = time.time()

    return HealthResponse(
        status="healthy",
        database="connected",
        llm=f"openai/{settings.llm_model}",
        tools_available=tool_registry.count,
        uptime_seconds=round(time.time() - start, 3),
    )
