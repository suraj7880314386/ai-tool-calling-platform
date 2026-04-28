"""Tests for the Tool-Calling Platform API."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_root(client):
    async with client as c:
        response = await c.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI Agent Tool-Calling API Platform"
    assert len(data["tools"]) == 5


@pytest.mark.asyncio
async def test_health(client):
    async with client as c:
        response = await c.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["tools_available"] == 5


@pytest.mark.asyncio
async def test_list_tools(client):
    async with client as c:
        response = await c.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    tool_names = [t["name"] for t in data["tools"]]
    assert "calculator" in tool_names
    assert "web_search" in tool_names
    assert "database_query" in tool_names


@pytest.mark.asyncio
async def test_get_tool_info(client):
    async with client as c:
        response = await c.get("/api/v1/tools/calculator")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "calculator"
    assert len(data["examples"]) > 0


@pytest.mark.asyncio
async def test_get_tool_not_found(client):
    async with client as c:
        response = await c.get("/api/v1/tools/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_history_empty(client):
    async with client as c:
        response = await c.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_execution_not_found(client):
    async with client as c:
        response = await c.get("/api/v1/history/nonexistent-id")
    assert response.status_code == 404
