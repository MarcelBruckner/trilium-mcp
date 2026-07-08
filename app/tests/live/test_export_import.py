import pytest
from fastmcp.exceptions import ToolError

from tests.live._client import call, make_note, client, run_async


def test_export_subtree_returns_readable_text():
    result = run_async(call("exportNoteSubtree", {"noteId": "root"}))
    text = result.content[0].text
    assert text.startswith("Exported subtree of note 'root'")
    assert "!!!meta.json" in text
    assert "=====" in text


def test_export_subtree_rejects_unknown_format():
    with pytest.raises(ToolError, match="Unsupported format"):
        run_async(call("exportNoteSubtree", {"noteId": "root", "format": "pdf"}))


def test_import_zip_surfaces_error_without_body():
    # The ETAPI import endpoint has no request body in the spec, so the generated
    # tool sends none; Trilium rejects the empty import. We assert the MCP layer
    # surfaces that rejection cleanly (a ToolError) rather than crashing.
    async def run():
        async with client() as c:
            note_id = await make_note(c, title="itest-import-target")
            await c.call_tool("importZip", {"noteId": note_id})
    with pytest.raises(ToolError):
        run_async(run())
