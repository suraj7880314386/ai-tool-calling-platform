"""Execution history manager — saves and retrieves agent execution records."""

import uuid
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.models import Execution, ToolCallRecord, AgentThoughtRecord

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages execution history persistence."""

    def _get_session(self) -> Session:
        return SessionLocal()

    def generate_id(self) -> str:
        return str(uuid.uuid4())[:12]

    def save_execution(
        self,
        execution_id: str,
        query: str,
        answer: str,
        status: str,
        total_duration_ms: float,
        retries_used: int,
        session_id: str,
        tool_calls: List[dict],
        thoughts: List[dict],
    ) -> None:
        """Save a complete execution record."""
        db = self._get_session()
        try:
            execution = Execution(
                id=execution_id,
                session_id=session_id,
                query=query,
                answer=answer,
                status=status,
                total_duration_ms=total_duration_ms,
                retries_used=retries_used,
            )
            db.add(execution)

            # Save tool calls
            for tc in tool_calls:
                record = ToolCallRecord(
                    execution_id=execution_id,
                    tool_name=tc["tool_name"],
                    tool_input=tc["tool_input"],
                    tool_output=tc.get("tool_output", ""),
                    duration_ms=tc.get("duration_ms", 0),
                    success=1 if tc.get("success", True) else 0,
                )
                db.add(record)

            # Save thoughts
            for t in thoughts:
                record = AgentThoughtRecord(
                    execution_id=execution_id,
                    step=t["step"],
                    thought=t.get("thought", ""),
                    action=t.get("action"),
                    action_input=t.get("action_input"),
                    observation=t.get("observation"),
                )
                db.add(record)

            db.commit()
            logger.info(f"Saved execution {execution_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save execution: {e}")
        finally:
            db.close()

    def get_execution(self, execution_id: str) -> Optional[dict]:
        """Get a specific execution with full details."""
        db = self._get_session()
        try:
            execution = db.query(Execution).filter(Execution.id == execution_id).first()
            if not execution:
                return None

            return {
                "execution_id": execution.id,
                "query": execution.query,
                "answer": execution.answer,
                "status": execution.status,
                "tools_used": [tc.tool_name for tc in execution.tool_calls],
                "tool_calls": [
                    {
                        "tool_name": tc.tool_name,
                        "tool_input": tc.tool_input,
                        "tool_output": tc.tool_output,
                        "duration_ms": tc.duration_ms,
                        "success": bool(tc.success),
                    }
                    for tc in execution.tool_calls
                ],
                "agent_thoughts": [
                    {
                        "step": t.step,
                        "thought": t.thought,
                        "action": t.action,
                        "action_input": t.action_input,
                        "observation": t.observation,
                    }
                    for t in execution.thoughts
                ],
                "duration_ms": execution.total_duration_ms,
                "created_at": execution.created_at,
            }
        finally:
            db.close()

    def get_history(self, limit: int = 50, session_id: Optional[str] = None) -> List[dict]:
        """Get execution history, optionally filtered by session."""
        db = self._get_session()
        try:
            query = db.query(Execution).order_by(Execution.created_at.desc())

            if session_id:
                query = query.filter(Execution.session_id == session_id)

            executions = query.limit(limit).all()

            return [
                {
                    "execution_id": e.id,
                    "query": e.query,
                    "answer": e.answer[:200] + "..." if len(e.answer or "") > 200 else e.answer,
                    "status": e.status,
                    "tools_used": [tc.tool_name for tc in e.tool_calls],
                    "duration_ms": e.total_duration_ms,
                    "created_at": e.created_at,
                }
                for e in executions
            ]
        finally:
            db.close()


# Singleton
history_manager = HistoryManager()
