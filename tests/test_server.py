import os
import json
import types
import importlib
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

# Path assumptions: package is importable as cnpj_mcp_server


def test_module_import_succeeds(monkeypatch):
    # Ensure no API key required during import
    monkeypatch.setenv("CNPJ_API_KEY", "test_key_1234567890")
    mod = importlib.import_module("cnpj_mcp_server.server")
    assert hasattr(mod, "TOOLS")
    assert hasattr(mod, "cnpj_client")
    assert hasattr(mod, "call_tool")


def test_tools_shape_and_presence(monkeypatch):
    monkeypatch.setenv("CNPJ_API_KEY", "test_key_1234567890")
    mod = importlib.import_module("cnpj_mcp_server.server")

    tools = mod.TOOLS
    # Required tools
    for key in ("cnpj_detailed_lookup", "term_search", "cnpj_advanced_search", "search_csv"):
        assert key in tools, f"Missing tool: {key}"
        entry = tools[key]
        assert entry.get("name") == key
        assert isinstance(entry.get("description"), str) and entry["description"].strip()
        schema = entry.get("inputSchema")
        assert isinstance(schema, dict) and schema.get("type") == "object"
        assert "properties" in schema and isinstance(schema["properties"], dict)

    # term_search must require 'term'
    assert "term" in tools["term_search"]["inputSchema"]["properties"]
    assert "term" in tools["term_search"]["inputSchema"].get("required", [])


@pytest.mark.parametrize("input_cnpj,expected", [
    ("11.222.333/0001-81", "11222333000181"),
    ("11222333000181", "11222333000181"),
])
def test_clean_cnpj_valid(monkeypatch, input_cnpj, expected):
    monkeypatch.setenv("CNPJ_API_KEY", "test_key_1234567890")
    from cnpj_mcp_server.server import CNPJClient
    c = CNPJClient()
    assert c._clean_cnpj(input_cnpj) == expected


def test_clean_cnpj_invalid(monkeypatch):
    monkeypatch.setenv("CNPJ_API_KEY", "test_key_1234567890")
    from cnpj_mcp_server.server import CNPJClient
    c = CNPJClient()
    with pytest.raises(ValueError):
        c._clean_cnpj("123")


@pytest.mark.asyncio
async def test_headers_include_api_key(monkeypatch):
    monkeypatch.setenv("CNPJ_API_KEY", "secret_api_key_abc")
    import cnpj_mcp_server.server as mod
    client = mod.CNPJClient()

    async def fake_json():
        return {"ok": True}

    class FakeResponse:
        status = 200
        async def json(self):
            return await fake_json()
        async def text(self):
            return "OK"

    class FakeGetCtx:
        def __init__(self, expected_headers):
            self.expected_headers = expected_headers
        async def __aenter__(self):
            # Assert header contains x-api-key
            assert self.expected_headers.get("x-api-key") == "secret_api_key_abc"
            # Ensure no credentials in params (validated in call site)
            return FakeResponse()
        async def __aexit__(self, *exc):
            return False

    class FakeSession:
        def get(self, url, params=None, headers=None):
            # Assert key not in params
            assert not params or ("x-api-key" not in params)
            return FakeGetCtx(headers or {})
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            return False

    with patch("aiohttp.ClientSession", return_value=FakeSession()):
        res = await client._make_request("/search/", params={"term":"padaria"})
        assert res["ok"] is True


@pytest.mark.asyncio
async def test_call_tool_term_search_routes_to_advanced(monkeypatch):
    monkeypatch.setenv("CNPJ_API_KEY", "test_key_1234567890")
    import cnpj_mcp_server.server as mod

    async def fake_advanced_search(**kwargs):
        return {"routed": "advanced", "kwargs": kwargs}

    with patch.object(mod.cnpj_client, "advanced_search", side_effect=fake_advanced_search):
        contents = await mod.call_tool("term_search", {"term": "padarias em SP Tatuapé", "uf": "SP"})
        assert len(contents) == 1
        payload = json.loads(contents[0].text)
        assert payload["routed"] == "advanced"
        assert payload["kwargs"]["term"] == "padarias em SP Tatuapé"
        assert payload["kwargs"]["uf"] == "SP"
