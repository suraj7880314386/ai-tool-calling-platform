"""LangChain Agent Executor — orchestrates tool-calling with ReAct reasoning."""

import time
import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool

from app.config import settings
from app.tools.registry import tool_registry
from app.agents.retry import with_retry, RateLimitError, should_retry
from app.core.history import history_manager

logger = logging.getLogger(__name__)

# ─── Agent System Prompt ──────────────────────────────────

AGENT_PROMPT = PromptTemplate.from_template("""You are a powerful AI assistant with access to multiple tools.
Your job is to answer the user's query accurately by selecting and using the right tool(s).

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Important rules:
1. ALWAYS use a tool when you need factual, real-time, or computed data.
2. For math, ALWAYS use the calculator — never compute in your head.
3. For database questions, construct a valid SQL SELECT query.
4. You can chain multiple tools if needed (e.g., search then calculate).
5. If a tool fails, try rephrasing the input or using a different tool.
6. Be concise and direct in your final answer.

Begin!

Question: {input}
Thought: {agent_scratchpad}""")


class AgentManager:
    """Manages LangChain agent creation and execution."""

    def __init__(self):
        self._llm = None
        self._agent_executor = None

    def _get_llm(self) -> ChatOpenAI:
        """Lazy-load LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                api_key=settings.openai_api_key,
                request_timeout=60,
            )
        return self._llm

    def _build_agent(
        self, tools: Optional[List[BaseTool]] = None
    ) -> AgentExecutor:
        """Build a ReAct agent with specified tools."""
        llm = self._get_llm()
        agent_tools = tools or tool_registry.get_all_tools()

        agent = create_react_agent(
            llm=llm,
            tools=agent_tools,
            prompt=AGENT_PROMPT,
        )

        executor = AgentExecutor(
            agent=agent,
            tools=agent_tools,
            verbose=True,
            max_iterations=settings.max_agent_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            early_stopping_method="generate",
        )

        return executor

    @with_retry()
    def execute(
        self,
        query: str,
        session_id: str = "default",
        tool_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the agent on a query.

        Args:
            query: User's question/command
            session_id: Session identifier
            tool_names: Specific tools to use (None = all)

        Returns:
            Dict with answer, tool calls, thoughts, and timing
        """
        start = time.time()
        execution_id = history_manager.generate_id()

        logger.info(f"[Agent] Executing ({execution_id}): {query[:80]}...")

        try:
            # Build agent with requested tools
            tools = None
            if tool_names:
                tools = tool_registry.get_tools_by_names(tool_names)

            executor = self._build_agent(tools)

            # Run the agent
            result = executor.invoke({"input": query})

            # Parse results
            answer = result.get("output", "No answer generated.")
            intermediate_steps = result.get("intermediate_steps", [])

            # Extract tool calls and thoughts
            tool_calls = []
            thoughts = []

            for i, (agent_action, observation) in enumerate(intermediate_steps):
                # Tool call record
                tool_calls.append({
                    "tool_name": agent_action.tool,
                    "tool_input": str(agent_action.tool_input),
                    "tool_output": str(observation)[:1000],
                    "duration_ms": 0,  # LangChain doesn't expose per-tool timing
                    "success": True,
                })

                # Thought record
                thoughts.append({
                    "step": i + 1,
                    "thought": getattr(agent_action, "log", ""),
                    "action": agent_action.tool,
                    "action_input": str(agent_action.tool_input),
                    "observation": str(observation)[:500],
                })

            total_ms = (time.time() - start) * 1000

            # Save to history
            history_manager.save_execution(
                execution_id=execution_id,
                query=query,
                answer=answer,
                status="success",
                total_duration_ms=total_ms,
                retries_used=0,
                session_id=session_id,
                tool_calls=tool_calls,
                thoughts=thoughts,
            )

            logger.info(
                f"[Agent] Done ({execution_id}): {len(tool_calls)} tool calls, "
                f"{total_ms:.0f}ms"
            )

            return {
                "execution_id": execution_id,
                "query": query,
                "answer": answer,
                "status": "success",
                "tool_calls": tool_calls,
                "agent_thoughts": thoughts,
                "total_duration_ms": round(total_ms, 2),
                "session_id": session_id,
            }

        except Exception as e:
            total_ms = (time.time() - start) * 1000

            # Check if retryable
            if should_retry(e):
                raise RateLimitError(str(e))

            # Non-retryable: save failure and return
            history_manager.save_execution(
                execution_id=execution_id,
                query=query,
                answer=f"Error: {str(e)}",
                status="failed",
                total_duration_ms=total_ms,
                retries_used=0,
                session_id=session_id,
                tool_calls=[],
                thoughts=[],
            )

            logger.error(f"[Agent] Failed ({execution_id}): {e}")

            return {
                "execution_id": execution_id,
                "query": query,
                "answer": f"I encountered an error processing your request: {str(e)}",
                "status": "failed",
                "tool_calls": [],
                "agent_thoughts": [],
                "total_duration_ms": round(total_ms, 2),
                "retries_used": 0,
                "session_id": session_id,
            }


# Singleton
agent_manager = AgentManager()
