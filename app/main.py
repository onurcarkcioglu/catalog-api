"""SecureStream Catalog API: OTT platformunun icerik katalogu servisi."""

import os
import secrets
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel


class Title(BaseModel):
    id: int
    name: str
    kind: str
    year: int
    age_rating: str


_CATALOG: dict[int, Title] = {
    t.id: t
    for t in [
        Title(id=1, name="Bosphorus Nights", kind="series", year=2025, age_rating="13+"),
        Title(id=2, name="Desert Signal", kind="movie", year=2024, age_rating="16+"),
        Title(id=3, name="Coral Cities", kind="documentary", year=2026, age_rating="G"),
    ]
}

TITLE_LOOKUPS = Counter("catalog_title_lookups", "Tekil icerik sorgulari", ["result"])

# Swagger/ReDoc uretimde kapali: saldirgana API haritasi vermiyoruz.
app = FastAPI(title="SecureStream Catalog API", version="0.1.0", docs_url=None, redoc_url=None)

# Her yanita guvenlik basliklari (ZAP DAST bulgusu uzerine eklendi).
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/titles")
def list_titles(
    kind: Annotated[str | None, Query(pattern="^(movie|series|documentary)$")] = None,
) -> list[Title]:
    titles = list(_CATALOG.values())
    if kind:
        titles = [t for t in titles if t.kind == kind]
    return titles


@app.get("/v1/titles/{title_id}")
def get_title(title_id: int) -> Title:
    title = _CATALOG.get(title_id)
    if title is None:
        TITLE_LOOKUPS.labels(result="not_found").inc()
        raise HTTPException(status_code=404, detail="title not found")
    TITLE_LOOKUPS.labels(result="found").inc()
    return title


API_KEY_FILE_DEFAULT = "/run/secrets/catalog/CATALOG_API_KEY"


def _read_api_key() -> str | None:
    path = os.environ.get("CATALOG_API_KEY_FILE", API_KEY_FILE_DEFAULT)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip() or None
    except OSError:
        return None


@app.get("/v1/admin/stats")
def admin_stats(x_api_key: Annotated[str | None, Header()] = None) -> dict[str, int]:
    # Anahtar Vault'tan External Secrets ile gelir; env yerine dosya olarak baglanir (CKV_K8S_35).
    # Her istekte okunur: ESO anahtari yenileyince pod yeniden baslatmadan gecerli olur.
    expected = _read_api_key()
    if not expected:
        raise HTTPException(status_code=503, detail="admin disabled")
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"titles": len(_CATALOG)}
