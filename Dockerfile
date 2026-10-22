# Base imaj pipeline'dan digest ile gelir; yerelde varsayilan etiket kullanilir.
ARG PYTHON_IMAGE=python:3.12-slim

# --- 1. asama: bagimliliklari ayri bir venv'e kur ---
FROM ${PYTHON_IMAGE} AS build
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt

# --- 2. asama: sadece calisma zamani; derleme araclari yok ---
FROM ${PYTHON_IMAGE}
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build /venv /venv
COPY app/ ./app/
ENV PATH="/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
