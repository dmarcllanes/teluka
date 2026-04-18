# ─────────────────────────────────────────────────────────────────────────────
# Teluka — FastHTML app
# Multi-stage build: slim final image using uv for fast, reproducible installs
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy lockfile and project metadata first (layer cache)
COPY pyproject.toml uv.lock ./

# Install dependencies into an isolated venv (no editable install)
RUN uv sync --frozen --no-install-project --no-dev


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN addgroup --system teluka && adduser --system --ingroup teluka teluka

WORKDIR /app

# Copy the venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY main.py       ./
COPY components/   ./components/
COPY core/         ./core/
COPY lib/          ./lib/
COPY schemas/      ./schemas/
COPY static/       ./static/

# Activate the venv by prepending it to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Runtime environment defaults (override via docker run -e or compose env_file)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=production \
    PORT=5001

# Drop to non-root
USER teluka

EXPOSE 5001

# FastHTML uses uvicorn under the hood via serve()
CMD ["python", "main.py"]
