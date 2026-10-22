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


def test_admin_requires_key(monkeypatch):
    monkeypatch.setenv("CATALOG_API_KEY", "unit-test-only")
    assert client.get("/v1/admin/stats").status_code == 401
    assert client.get("/v1/admin/stats", headers={"X-API-Key": "wrong"}).status_code == 401
    r = client.get("/v1/admin/stats", headers={"X-API-Key": "unit-test-only"})
    assert r.status_code == 200
    assert r.json() == {"titles": 3}


def test_admin_disabled_without_key(monkeypatch):
    monkeypatch.delenv("CATALOG_API_KEY", raising=False)
    assert client.get("/v1/admin/stats").status_code == 503
