"""Enforce that every ETAPI operationId is exercised by a live test."""

import re
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve()
_LIVE_DIR = _HERE.parent
_SPEC = _LIVE_DIR.parents[1] / "trilium-etapi.openapi"  # app/trilium-etapi.openapi


# Endpoints intentionally NOT exposed as MCP tools, so they are not tested.
# login/logout manage ETAPI session tokens; an MCP client authenticates via the
# Authorization header and logout would invalidate its own credential. Excluded
# in server.py via a RouteMap (see the build_server comment).
_EXCLUDED_OPERATIONS = {"login", "logout"}


def _spec_operation_ids() -> set[str]:
    spec = yaml.safe_load(_SPEC.read_text())
    ids = set()
    for path_item in spec.get("paths", {}).values():
        for op in path_item.values():
            if isinstance(op, dict) and "operationId" in op:
                ids.add(op["operationId"])
    return ids


def _exercised_tool_names() -> set[str]:
    names = set()
    for py in _LIVE_DIR.glob("test_*.py"):
        if py.name == "test_coverage.py":
            continue  # don't count names mentioned in this guard itself
        source = py.read_text()
        names.update(re.findall(r'["\']([a-zA-Z]+)["\']', source))
    return names


def test_all_tools_have_a_live_test():
    operations = _spec_operation_ids() - _EXCLUDED_OPERATIONS
    exercised = _exercised_tool_names()
    uncovered = sorted(operations - exercised)
    assert not uncovered, f"tools with no live test: {uncovered}"


def test_excluded_operations_are_not_registered():
    # The excluded auth endpoints must genuinely be absent from the tool surface.
    import asyncio

    import server

    mcp = server.build_server()
    names = {t.name for t in asyncio.run(mcp.list_tools())}
    still_present = sorted(_EXCLUDED_OPERATIONS & names)
    assert not still_present, f"excluded tools still registered: {still_present}"


def test_no_unknown_tool_names_referenced():
    # Every operationId-shaped call in tests must correspond to a real endpoint.
    operations = _spec_operation_ids()
    called = set(
        re.findall(
            r'call_tool\(\s*["\']([a-zA-Z]+)["\']',
            "\n".join(
                p.read_text() for p in _LIVE_DIR.glob("test_*.py")
                if p.name != "test_coverage.py"
            ),
        )
    )
    unknown = sorted(called - operations)
    assert not unknown, f"tests call unknown tool names: {unknown}"
