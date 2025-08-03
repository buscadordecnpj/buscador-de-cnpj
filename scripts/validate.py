#!/usr/bin/env python3
import ast
import importlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
TARGET = os.path.join(ROOT, "src", "cnpj_mcp_server", "server.py")


def fail(msg: str):
    print(f"VALIDATION FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str):
    print(f"OK: {msg}")


def validate_syntax():
    try:
        with open(TARGET, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
    except SyntaxError as e:
        fail(f"Syntax error in server.py: {e}")
    ok("server.py parses successfully")


def validate_tools_shape():
    # Import safely with env var set
    os.environ.setdefault("CNPJ_API_KEY", "validation_key")
    mod = importlib.import_module("cnpj_mcp_server.server")
    tools = getattr(mod, "TOOLS", None)
    if not isinstance(tools, dict):
        fail("TOOLS is missing or not a dict")

    required = ["cnpj_detailed_lookup", "term_search", "cnpj_advanced_search", "search_csv"]
    missing = [k for k in required if k not in tools]
    if missing:
        fail(f"Missing tools: {missing}")

    for name, spec in tools.items():
        if not isinstance(spec, dict):
            fail(f"Tool {name} must be a dict")
        if spec.get("name") != name:
            fail(f"Tool {name} has mismatched name field")
        schema = spec.get("inputSchema")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            fail(f"Tool {name} inputSchema must be an object")

    # term_search requires term
    term_schema = tools["term_search"]["inputSchema"]
    if "term" not in term_schema.get("required", []):
        fail("term_search must require 'term'")

    ok("TOOLS shape validated")


def main():
    validate_syntax()
    validate_tools_shape()
    ok("All validations passed")


if __name__ == "__main__":
    main()
