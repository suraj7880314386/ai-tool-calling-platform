"""Database Query Tool — executes SQL queries against the application database."""

import time
import logging
import re

from langchain.tools import tool

from app.core.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Tables the agent is allowed to query
ALLOWED_TABLES = {"users", "products"}

# Schema description for the LLM
DB_SCHEMA = """
Available tables:

TABLE: users
- id (INTEGER, primary key)
- name (VARCHAR)
- email (VARCHAR)
- role (VARCHAR) — values: 'admin', 'user', 'moderator'
- signup_date (DATETIME)
- is_active (INTEGER) — 1=active, 0=inactive

TABLE: products
- id (INTEGER, primary key)
- name (VARCHAR)
- category (VARCHAR) — values: 'electronics', 'clothing', 'books', 'food', 'sports'
- price (FLOAT)
- stock (INTEGER)
- created_at (DATETIME)
"""


@tool
def database_query(query: str) -> str:
    """
    Query the application database using natural language or SQL.
    Use this to look up users, products, or any stored data.

    The database has these tables:
    - users (id, name, email, role, signup_date, is_active)
    - products (id, name, category, price, stock, created_at)

    You can pass either:
    - Natural language: "Show all active admin users"
    - SQL: "SELECT * FROM users WHERE role = 'admin' AND is_active = 1"

    Args:
        query: Natural language question or SQL query about the data.

    Returns:
        Query results formatted as a readable string.
    """
    start = time.time()
    logger.info(f"[Database] Query: {query}")

    try:
        # If it looks like SQL, execute directly (with safety checks)
        if _looks_like_sql(query):
            sql = query
        else:
            # Convert natural language to SQL hint
            sql = _natural_language_to_sql_hint(query)

        # Validate safety
        _validate_query(sql)

        # Execute
        result = _execute_sql(sql)

        duration = (time.time() - start) * 1000
        logger.info(f"[Database] Completed in {duration:.1f}ms")

        return result

    except PermissionError as e:
        return f"Query blocked: {str(e)}"
    except Exception as e:
        logger.error(f"[Database] Error: {e}")
        return f"Database query failed: {str(e)}. Schema info:\n{DB_SCHEMA}"


def _looks_like_sql(query: str) -> bool:
    """Check if the input looks like a SQL query."""
    sql_keywords = {"select", "insert", "update", "delete", "show", "describe"}
    first_word = query.strip().split()[0].lower() if query.strip() else ""
    return first_word in sql_keywords


def _validate_query(sql: str) -> None:
    """Validate the SQL query for safety."""
    sql_lower = sql.lower().strip()

    # Only allow SELECT queries
    if not sql_lower.startswith("select"):
        raise PermissionError("Only SELECT queries are allowed for safety.")

    # Block dangerous keywords
    dangerous = {"drop", "delete", "insert", "update", "alter", "truncate", "exec", "execute", "--", ";"}
    # Remove the leading SELECT to avoid false positives
    rest = sql_lower[6:]
    for word in dangerous:
        if word in rest:
            raise PermissionError(f"Dangerous keyword detected: {word}")

    # Check that only allowed tables are referenced
    for table in ALLOWED_TABLES:
        if table in sql_lower:
            return  # Found an allowed table

    raise PermissionError(f"Query must reference one of: {ALLOWED_TABLES}")


def _natural_language_to_sql_hint(query: str) -> str:
    """
    Convert natural language to a basic SQL query.
    The LLM agent typically sends SQL directly, but this handles edge cases.
    """
    q = query.lower()

    if "user" in q or "signup" in q or "admin" in q or "email" in q:
        table = "users"
    elif "product" in q or "price" in q or "stock" in q or "category" in q:
        table = "products"
    else:
        table = "users"  # Default

    # Build a basic SELECT
    sql = f"SELECT * FROM {table}"

    # Add simple filters
    if "active" in q:
        sql += " WHERE is_active = 1"
    elif "inactive" in q:
        sql += " WHERE is_active = 0"
    elif "admin" in q:
        sql += " WHERE role = 'admin'"

    sql += " LIMIT 20"
    return sql


def _execute_sql(sql: str) -> str:
    """Execute SQL and format results."""
    db = SessionLocal()
    try:
        result = db.execute(text(sql))
        rows = result.fetchall()
        columns = result.keys()

        if not rows:
            return f"Query returned 0 results.\nSQL: {sql}"

        # Format as table
        col_names = list(columns)
        output = [" | ".join(col_names)]
        output.append("-" * len(output[0]))

        for row in rows[:50]:  # Cap at 50 rows
            output.append(" | ".join(str(val) for val in row))

        summary = f"\n\nTotal: {len(rows)} row(s) returned"
        if len(rows) > 50:
            summary += " (showing first 50)"

        return "\n".join(output) + summary + f"\nSQL: {sql}"

    finally:
        db.close()
