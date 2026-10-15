FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app/frontend
ENV NEXT_TELEMETRY_DISABLED=1
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv
COPY --from=frontend-build /usr/local/bin/node /usr/local/bin/node
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_NO_SYNC=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH" \
    HOSTNAME=0.0.0.0 \
    PORT=3000
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-default-groups --no-install-project --no-cache \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /app/data /app/frontend \
    && chown -R app:app /app/data /app/frontend
COPY backend/ ./backend/
COPY --from=frontend-build --chown=app:app /app/frontend/.next/standalone/ ./frontend/
COPY --from=frontend-build --chown=app:app /app/frontend/.next/static/ ./frontend/.next/static/
USER app
WORKDIR /app/frontend
EXPOSE 3000
CMD ["node", "server.js"]
