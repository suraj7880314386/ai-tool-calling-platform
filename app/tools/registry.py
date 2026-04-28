"""Tool Registry — central manager for all available tools."""

import logging
from typing import List, Dict, Optional

from langchain.tools import BaseTool

from app.tools.search import web_search
from app.tools.calculator import calculator
from app.tools.database import database_query, DB_SCHEMA
from app.tools.wikipedia import wikipedia_lookup
from app.tools.weather import weather

logger = logging.getLogger(__name__)


# ─── Tool Metadata ────────────────────────────────────────

TOOL_METADATA = {
    "web_search": {
        "name": "web_search",
        "description": "Search the web for real-time information, news, current events.",
        "parameters": {"query": "string — search query"},
        "examples": [
            "Latest SpaceX launch news",
            "Current Bitcoin price",
            "Who won the 2024 World Series?",
        ],
    },
    "calculator": {
        "name": "calculator",
        "description": "Evaluate mathematical expressions — arithmetic, algebra, trig, logs.",
        "parameters": {"expression": "string — math expression to evaluate"},
        "examples": [
            "25 * 48 + 132",
            "sqrt(144) + log(1000, 10)",
            "sin(pi/4) * 2",
        ],
    },
    "database_query": {
        "name": "database_query",
        "description": f"Query the application database (SQL). Schema:\n{DB_SCHEMA}",
        "parameters": {"query": "string — SQL SELECT query or natural language question"},
        "examples": [
            "SELECT * FROM users WHERE role = 'admin'",
            "Show all products under $50",
            "How many active users signed up this week?",
        ],
    },
    "wikipedia_lookup": {
        "name": "wikipedia_lookup",
        "description": "Look up factual information on Wikipedia — people, places, concepts, history.",
        "parameters": {"query": "string — topic to look up"},
        "examples": [
            "Albert Einstein",
            "Quantum Computing",
            "History of the Roman Empire",
        ],
    },
    "weather": {
        "name": "weather",
        "description": "Get current weather for any city or location worldwide.",
        "parameters": {"location": "string — city name (e.g., 'Tokyo', 'New York')"},
        "examples": [
            "Tokyo",
            "London, UK",
            "New Delhi",
        ],
    },
}


class ToolRegistry:
    """Central registry for all LangChain tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {
            "web_search": web_search,
            "calculator": calculator,
            "database_query": database_query,
            "wikipedia_lookup": wikipedia_lookup,
            "weather": weather,
        }
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools as LangChain tool objects."""
        return list(self._tools.values())

    def get_tools_by_names(self, names: List[str]) -> List[BaseTool]:
        """Get specific tools by name."""
        tools = []
        for name in names:
            if name in self._tools:
                tools.append(self._tools[name])
            else:
                logger.warning(f"Tool not found: {name}")
        return tools

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a single tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict]:
        """List all tools with metadata."""
        return [TOOL_METADATA[name] for name in self._tools if name in TOOL_METADATA]

    def get_tool_info(self, name: str) -> Optional[Dict]:
        """Get metadata for a specific tool."""
        return TOOL_METADATA.get(name)

    @property
    def count(self) -> int:
        return len(self._tools)


# Singleton
tool_registry = ToolRegistry()
