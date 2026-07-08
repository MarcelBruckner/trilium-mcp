import asyncio

import httpx

import server


def _mock_client():
    """An httpx client whose transport fakes Trilium's create-note response,
    including branch.prefix == null (the field the spec types as string)."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/create-note"):
            return httpx.Response(201, json={
                "note": {
                    "noteId": "abc123", "isProtected": False, "title": "t",
                    "type": "text", "mime": "text/html", "blobId": "b1",
                    "dateCreated": "2026-07-08 00:00:00.000+0000",
                    "dateModified": "2026-07-08 00:00:00.000+0000",
                    "utcDateCreated": "2026-07-08 00:00:00.000Z",
                    "utcDateModified": "2026-07-08 00:00:00.000Z",
                    "parentNoteIds": ["root"], "childNoteIds": [],
                    "parentBranchIds": ["root_abc123"], "childBranchIds": [],
                    "attributes": [],
                },
                "branch": {
                    "branchId": "root_abc123", "noteId": "abc123",
                    "parentNoteId": "root", "prefix": None, "notePosition": 10,
                    "isExpanded": False,
                    "utcDateModified": "2026-07-08 00:00:00.000Z",
                },
            })
        return httpx.Response(404, json={"status": 404})

    return httpx.AsyncClient(
        base_url="http://trilium:8080/etapi",
        auth=server.EtapiTokenAuth(),
        transport=httpx.MockTransport(handler),
    )


def test_build_server_needs_no_token_and_builds_tools():
    mcp = server.build_server()
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert len(tools) >= 30
    assert "createNote" in names


def test_createnote_with_null_prefix_does_not_error():
    from fastmcp import Client

    async def run():
        reset = server._incoming_auth.set("Bearer test-token")
        try:
            mcp = server.build_server(client=_mock_client())
            async with Client(mcp) as c:
                return await c.call_tool("createNote", {
                    "parentNoteId": "root", "title": "t",
                    "type": "text", "content": "c",
                })
        finally:
            server._incoming_auth.reset(reset)

    # Must NOT raise ToolError("Output validation error: None is not of type 'string'").
    result = asyncio.run(run())
    assert result is not None
