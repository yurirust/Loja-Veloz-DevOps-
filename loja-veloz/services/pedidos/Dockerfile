# ─── Stage 1: Build / dependências ────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Runtime enxuto ──────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Segurança: usuário não-root
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copiar dependências instaladas do stage de build
COPY --from=builder /install /usr/local

COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
