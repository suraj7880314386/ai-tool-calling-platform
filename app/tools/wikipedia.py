"""Wikipedia Tool — looks up encyclopedia articles."""

import time
import logging

from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def wikipedia_lookup(query: str) -> str:
    """
    Look up a topic on Wikipedia. Use this for factual information about
    historical events, people, places, scientific concepts, or any general
    knowledge topic.

    Args:
        query: Topic to look up on Wikipedia.

    Returns:
        A summary of the Wikipedia article.
    """
    start = time.time()
    logger.info(f"[Wikipedia] Looking up: {query}")

    try:
        import wikipedia

        # Search for the most relevant page
        search_results = wikipedia.search(query, results=3)

        if not search_results:
            return f"No Wikipedia article found for: {query}"

        # Try to get the page summary
        for title in search_results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                summary = wikipedia.summary(title, sentences=5, auto_suggest=False)

                result = (
                    f"Title: {page.title}\n"
                    f"URL: {page.url}\n\n"
                    f"Summary:\n{summary}"
                )

                duration = (time.time() - start) * 1000
                logger.info(f"[Wikipedia] Found: {page.title} ({duration:.1f}ms)")

                return result

            except wikipedia.DisambiguationError as e:
                # Pick the first option from disambiguation
                if e.options:
                    try:
                        summary = wikipedia.summary(e.options[0], sentences=5)
                        return f"Title: {e.options[0]}\n\nSummary:\n{summary}"
                    except Exception:
                        continue
            except wikipedia.PageError:
                continue

        return f"Could not find a clear Wikipedia article for: {query}. Try being more specific."

    except Exception as e:
        logger.error(f"[Wikipedia] Error: {e}")
        return f"Wikipedia lookup failed: {str(e)}"
