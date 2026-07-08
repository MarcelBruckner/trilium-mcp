import httpx

from tests.live._client import HEALTH_URL, call, run_async


def test_health_endpoint_returns_ok():
    assert httpx.get(HEALTH_URL, timeout=5.0).text == "ok"


def test_get_app_info():
    result = run_async(call("getAppInfo"))
    assert isinstance(result.data, dict)
    assert result.data.get("appVersion")


def test_search_returns_results_list():
    result = run_async(call("searchNotes", {"search": "trilium"}))
    assert isinstance(result.data, dict)
    assert isinstance(result.data.get("results"), list)


def test_create_backup_succeeds():
    result = run_async(call("createBackup", {"backupName": "integration-test"}))
    assert result.is_error is False
