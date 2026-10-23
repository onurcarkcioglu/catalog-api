from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_titles():
    r = client.get("/v1/titles")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_filter_by_kind():
    r = client.get("/v1/titles", params={"kind": "movie"})
    assert [t["id"] for t in r.json()] == [2]


def test_invalid_kind_rejected():
    # Girdi dogrulama: beklenmeyen deger 422 ile reddedilmeli.
    r = client.get("/v1/titles", params={"kind": "<script>alert(1)</script>"})
    assert r.status_code == 422


def test_get_title_found():
    r = client.get("/v1/titles/1")
    assert r.status_code == 200
    assert r.json()["name"] == "Bosphorus Nights"


def test_get_title_not_found():
    assert client.get("/v1/titles/999").status_code == 404


def test_docs_disabled():
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 200


def test_metrics_exposed():
    client.get("/v1/titles/1")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "catalog_title_lookups_total" in r.text


def test_security_headers():
    r = client.get("/healthz")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert "max-age=" in r.headers["strict-transport-security"]


def test_admin_requires_key(monkeypatch, tmp_path):
    key_file = tmp_path / "CATALOG_API_KEY"
    key_file.write_text("unit-test-only\n")
    monkeypatch.setenv("CATALOG_API_KEY_FILE", str(key_file))
    assert client.get("/v1/admin/stats").status_code == 401
    assert client.get("/v1/admin/stats", headers={"X-API-Key": "wrong"}).status_code == 401
    r = client.get("/v1/admin/stats", headers={"X-API-Key": "unit-test-only"})
    assert r.status_code == 200
    assert r.json() == {"titles": 3}


def test_admin_disabled_without_key(monkeypatch, tmp_path):
    monkeypatch.setenv("CATALOG_API_KEY_FILE", str(tmp_path / "missing"))
    assert client.get("/v1/admin/stats").status_code == 503


def test_admin_disabled_with_empty_key(monkeypatch, tmp_path):
    key_file = tmp_path / "CATALOG_API_KEY"
    key_file.write_text("\n")
    monkeypatch.setenv("CATALOG_API_KEY_FILE", str(key_file))
    assert client.get("/v1/admin/stats", headers={"X-API-Key": ""}).status_code == 503


def test_admin_key_not_read_from_env(monkeypatch, tmp_path):
    # The key is mounted as a file (CKV_K8S_35); an env variable alone must not enable admin.
    monkeypatch.setenv("CATALOG_API_KEY_FILE", str(tmp_path / "missing"))
    monkeypatch.setenv("CATALOG_API_KEY", "unit-test-only")
    r = client.get("/v1/admin/stats", headers={"X-API-Key": "unit-test-only"})
    assert r.status_code == 503
