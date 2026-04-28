"""Web Search Tool — searches the web for real-time information."""

import time
import logging
import httpx
from typing import Optional

from langchain.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> str:
    """
    Search the web for real-time information. Use this for current events,
    recent news, facts about people/places/things, or any query requiring
    up-to-date information.

    Args:
        query: The search query string.

    Returns:
        Search results as a formatted string.
    """
    start = time.time()
    logger.info(f"[WebSearch] Searching: {query}")

    try:
        # Try SerpAPI if key available
        if settings.search_api_key:
            return _serpapi_search(query)

        # Fallback: DuckDuckGo instant answer API (free, no key needed)
        return _duckduckgo_search(query)

    except Exception as e:
        logger.error(f"[WebSearch] Failed: {e}")
        return f"Search failed: {str(e)}. Please try rephrasing your query."
    finally:
        duration = (time.time() - start) * 1000
        logger.info(f"[WebSearch] Completed in {duration:.1f}ms")


def _duckduckgo_search(query: str) -> str:
    """Free DuckDuckGo instant answer API."""
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1,
    }

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params=params)
        data = response.json()

    results = []

    # Abstract (main answer)
    if data.get("Abstract"):
        results.append(f"Summary: {data['Abstract']}")
        if data.get("AbstractSource"):
            results.append(f"Source: {data['AbstractSource']}")

    # Related topics
    for topic in data.get("RelatedTopics", [])[:5]:
        if isinstance(topic, dict) and "Text" in topic:
            results.append(f"- {topic['Text']}")

    # Answer (direct)
    if data.get("Answer"):
        results.append(f"Direct Answer: {data['Answer']}")

    if not results:
        return f"No results found for: {query}. Try a different search query."

    return "\n".join(results)


def _serpapi_search(query: str) -> str:
    """SerpAPI Google search (requires API key)."""
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": settings.search_api_key,
        "engine": "google",
        "num": 5,
    }

    with httpx.Client(timeout=15) as client:
        response = client.get(url, params=params)
        data = response.json()

    results = []

    # Knowledge graph
    if "knowledge_graph" in data:
        kg = data["knowledge_graph"]
        if "description" in kg:
            results.append(f"Summary: {kg['description']}")

    # Organic results
    for item in data.get("organic_results", [])[:5]:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        results.append(f"- {title}: {snippet}")

    # Answer box
    if "answer_box" in data:
        ab = data["answer_box"]
        if "answer" in ab:
            results.append(f"Direct Answer: {ab['answer']}")
        elif "snippet" in ab:
            results.append(f"Answer: {ab['snippet']}")

    if not results:
        return f"No results found for: {query}"

    return "\n".join(results)
