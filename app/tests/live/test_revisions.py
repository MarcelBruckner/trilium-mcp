from tests.live._client import client, make_note, result_list, run_async


async def _first_revision_id(c, note_id) -> str:
    items = result_list(await c.call_tool("getNoteRevisions", {"noteId": note_id}))
    assert items, "expected at least one revision after createRevision"
    return items[0]["revisionId"]


def test_create_revision_and_read_it_back():
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-rev", content="v1")
            await c.call_tool("putNoteContentById", {"noteId": note_id, "content": "v2"})
            await c.call_tool("createRevision", {"noteId": note_id})
            rev_id = await _first_revision_id(c, note_id)
            got = await c.call_tool("getRevisionById", {"revisionId": rev_id})
            content = await c.call_tool("getRevisionContent", {"revisionId": rev_id})
            return rev_id, got.data, content
    rev_id, revision, content = run_async(run())
    assert revision["revisionId"] == rev_id
    assert content.content[0].text is not None  # text body returned, not a crash
