# ─────────────────────────────────────────────────────────────────────────────
# Teluka — FastHTML  |  3-stage multi-stage build
#
# Stage 1 (deps)     — install uv + resolve dependencies into a venv
# Stage 2 (builder)  — copy source, compile .pyc files, strip dev artefacts
# Stage 3 (runtime)  — distroless-style final image, non-root, no build tools
# ─────────────────────────────────────────────────────────────────────────────


# ── Stage 1: dependency resolver ──────────────────────────────────────────────
FROM python:3.12-slim AS deps

# Pull uv binary from the official image (no apt install needed)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Only copy the files uv needs — changes here bust only this layer
COPY pyproject.toml uv.lock ./

# Create venv and install all production deps (frozen = respects uv.lock exactly)
RUN uv venv /app/.venv && \
    uv sync --frozen --no-install-project --no-dev


# ── Stage 2: application builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Bring the pre-built venv from stage 1
COPY --from=deps /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY main.py       ./
COPY components/   ./components/
COPY core/         ./core/
COPY lib/          ./lib/
COPY schemas/      ./schemas/
COPY static/       ./static/

# Pre-compile all .py files to .pyc so the runtime image starts faster
# -q  = quiet  |  -j0 = use all CPU cores
RUN python -m compileall -q -j0 .


# ── Stage 3: production runtime ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: create a non-root user
RUN addgroup --system teluka && \
    adduser  --system --ingroup teluka --no-create-home teluka

WORKDIR /app

# Copy ONLY what the running app needs — nothing from the build toolchain
COPY --from=builder /app/.venv      /app/.venv
COPY --from=builder /app/main.py    ./
COPY --from=builder /app/components ./components
COPY --from=builder /app/core       ./core
COPY --from=builder /app/lib        ./lib
COPY --from=builder /app/schemas    ./schemas
COPY --from=builder /app/static     ./static

# Activate the venv
ENV PATH="/app/.venv/bin:$PATH"

# Python tunables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

# App config defaults — override at runtime with --env-file .env
ENV ENV=production \
    PORT=5001

# Drop privileges
USER teluka

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')"

CMD ["python", "main.py"]
