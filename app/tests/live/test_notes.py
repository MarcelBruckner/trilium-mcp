import pytest
from fastmcp.exceptions import ToolError

from tests.live._client import (
    body_arg_name,
    client,
    make_note,
    path_arg_name,
    result_list,
    run_async,
)


def test_create_and_get_note():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-create")
            got = await c.call_tool("getNoteById", {"noteId": note_id})
            return note_id, got.data
    note_id, note = run_async(run())
    assert note["noteId"] == note_id
    assert note["title"] == "itest-create"


def test_patch_note_title():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-before")
            arg = await path_arg_name(c, "patchNoteById", "noteId")
            await c.call_tool("patchNoteById", {arg: note_id, "title": "itest-after"})
            got = await c.call_tool("getNoteById", {"noteId": note_id})
            return got.data
    note = run_async(run())
    assert note["title"] == "itest-after"


def test_delete_note_removes_it():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-delete")
            await c.call_tool("deleteNoteById", {"noteId": note_id})
            # Boundary check: the deleted note is no longer retrievable via the API.
            with pytest.raises(ToolError):
                await c.call_tool("getNoteById", {"noteId": note_id})
    run_async(run())


def test_undelete_note_restores_it():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-undelete")
            await c.call_tool("deleteNoteById", {"noteId": note_id})
            await c.call_tool("undeleteNote", {"noteId": note_id})
            got = await c.call_tool("getNoteById", {"noteId": note_id})
            return note_id, got.data
    note_id, note = run_async(run())
    assert note["noteId"] == note_id


def test_put_then_get_note_content():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-content", content="orig")
            arg = await body_arg_name(c, "putNoteContentById", "noteId")
            await c.call_tool("putNoteContentById", {"noteId": note_id, arg: "updated body"})
            got = await c.call_tool("getNoteContent", {"noteId": note_id})
            return got.content[0].text
    text = run_async(run())
    assert "updated body" in text


def test_get_note_revisions_returns_list():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-revs")
            return await c.call_tool("getNoteRevisions", {"noteId": note_id})
    assert isinstance(result_list(run_async(run())), list)


def test_get_note_attachments_returns_list():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-atts")
            return await c.call_tool("getNoteAttachments", {"noteId": note_id})
    assert isinstance(result_list(run_async(run())), list)


def test_get_note_history_returns_list():
    r = run_async(_history())
    assert isinstance(result_list(r), list)


async def _history():
    async with client() as c:
        return await c.call_tool("getNoteHistory", {"ancestorNoteId": "root"})


def test_refresh_note_ordering_succeeds():
    async def run():
        async with client() as c:
            return await c.call_tool("postRefreshNoteOrdering", {"parentNoteId": "root"})
    result = run_async(run())
    assert result.is_error is False
