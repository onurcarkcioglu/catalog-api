"""SecureStream Catalog API: OTT platformunun icerik katalogu servisi."""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response
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
