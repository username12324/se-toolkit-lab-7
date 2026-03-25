# Bot Dockerfile — builds the Telegram bot using uv
# Based on the same pattern as backend/Dockerfile

ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/

# ---
# Stage 1: Build the application
# ---
FROM ${REGISTRY_PREFIX}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace files for dependency resolution
COPY pyproject.toml uv.lock /app/
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY bot/pyproject.toml /app/bot/pyproject.toml

# Sync dependencies (frozen to use uv.lock)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy all source code
COPY backend /app/backend/
COPY bot /app/bot/

# ---
# Stage 2: Final runtime image
# ---
FROM ${REGISTRY_PREFIX}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Non-root user for security
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the built application from builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

USER nonroot
WORKDIR /app

# Run the bot
CMD ["python", "bot/bot.py"]
