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


def _extract_tools_from_ast() -> dict:
    with open(TARGET, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TOOLS":
                    # Evaluate literal dict safely
                    return ast.literal_eval(node.value)
    fail("TOOLS assignment not found in server.py")


def validate_tools_shape():
    # Prefer AST extraction to avoid importing runtime deps
    try:
        tools = _extract_tools_from_ast()
    except Exception as e:
        fail(f"Failed to parse TOOLS via AST: {e}")

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

    term_schema = tools["term_search"]["inputSchema"]
    if "term" not in term_schema.get("required", []):
        fail("term_search must require 'term'")

    ok("TOOLS shape validated (AST)")


def main():
    validate_syntax()
    validate_tools_shape()
    ok("All validations passed")


if __name__ == "__main__":
    main()
