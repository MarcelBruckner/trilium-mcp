import pytest
from fastmcp.exceptions import ToolError

from tests.live._client import client, make_note, path_arg_name, run_async


async def _make_attribute(c, note_id, name="itestLabel", value="v1"):
    r = await c.call_tool(
        "postAttribute",
        {"noteId": note_id, "type": "label", "name": name, "value": value},
    )
    return r.data["attributeId"], r.data


def test_create_and_get_attribute():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-attr-owner")
            attr_id, created = await _make_attribute(c, note_id, value="created")
            got = await c.call_tool("getAttributeById", {"attributeId": attr_id})
            return attr_id, created, got.data
    attr_id, created, got = run_async(run())
    assert attr_id
    assert created["name"] == "itestLabel"
    assert got["value"] == "created"


def test_patch_attribute_value():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-attr-owner2")
            attr_id, _ = await _make_attribute(c, note_id, value="before")
            attr_path = await path_arg_name(c, "patchAttributeById", "attributeId")
            await c.call_tool("patchAttributeById", {attr_path: attr_id, "value": "after"})
            got = await c.call_tool("getAttributeById", {"attributeId": attr_id})
            return got.data
    assert run_async(run())["value"] == "after"


def test_delete_attribute_removes_it():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-attr-owner3")
            attr_id, _ = await _make_attribute(c, note_id)
            await c.call_tool("deleteAttributeById", {"attributeId": attr_id})
            with pytest.raises(ToolError):
                await c.call_tool("getAttributeById", {"attributeId": attr_id})
    run_async(run())
