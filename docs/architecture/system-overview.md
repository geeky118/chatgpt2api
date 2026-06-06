# System Overview

## Purpose

chatgpt2api is a FastAPI service that exposes OpenAI-compatible API surfaces, account-pool administration, image task management, registration tooling, and a statically exported Next.js admin/debug UI. The production container serves both the API and the exported frontend from one FastAPI process.

## Main Components

- API entrypoint: `main.py` creates the FastAPI app through `api.create_app()`.
- Route assembly: `api/app.py` installs exception handlers, CORS, API routers, background lifecycle jobs, and static web fallback routing.
- API routers: `api/ai.py`, `api/accounts.py`, `api/image_tasks.py`, `api/register.py`, and `api/system.py` define the HTTP contract.
- Service layer: `services/` owns account selection, OpenAI upstream calls, storage backends, logging, image processing, backup, registration, proxy, and protocol adaptation.
- Storage backends: `services/storage/` supports `json`, `sqlite`, `postgres`, and `git` modes, selected through `STORAGE_BACKEND` and related environment variables.
- Frontend: `web/` is a Next.js app with `output: 'export'`; the Docker build writes the static output to `/app/web_dist`.
- Runtime data: `data/` is the local persistent mount for SQLite databases, account JSON, logs, image artifacts, and backup state.

## Runtime Shape

- The local source-built compose file is `docker-compose.local.yml`.
- The local container name is `chatgpt2api-local`.
- Host port `8000` maps to container port `80`.
- `config.json` is mounted into `/app/config.json`.
- `./data` is mounted into `/app/data`.
- Local compose defaults to `STORAGE_BACKEND=sqlite` and `DATABASE_URL=sqlite:////app/data/accounts.db`.
- The image-pull compose file `docker-compose.yml` maps host port `3000` to container port `80` and uses the published `ghcr.io/basketikun/chatgpt2api:latest` image.

## External Integrations

- Upstream ChatGPT/OpenAI-compatible calls are implemented in `services/openai_backend_api.py` and protocol files under `services/protocol/`.
- Account import/integration code includes CPA pools and sub2api connection management in `api/accounts.py` and related services.
- Registration flows use `services/register/` and can depend on external mail providers, proxy settings, and OpenAI auth endpoints.
- Optional backup and image storage features can call external Cloudflare R2 or WebDAV services when configured.

## Boundaries and Contracts

- `config.json` and environment variables are runtime configuration, not generated source. Keep secrets out of commits.
- API auth is enforced through helpers in `api/support.py`; admin endpoints generally require an Authorization header derived from configured auth keys.
- `/version`, `/health`, and `/health?format=json` are the lightweight local smoke endpoints.
- Static frontend routing is handled by the catch-all route in `api/app.py`; do not break `_next/` asset resolution or index fallback when changing frontend output behavior.
- Storage implementations must satisfy the `StorageBackend` interface in `services/storage/base.py`.

## Risky Areas

- Docker builds run both Node/Next and Python/uv stages; frontend build failures block the final API image.
- `config.json` is mounted into the container and may contain local secrets. Avoid printing or committing sensitive values.
- Account refresh, registration, and image generation flows depend on upstream behavior and may fail even when local smoke endpoints are healthy.
- Background startup creates watchers and cleanup jobs in the FastAPI lifespan; long-running tests should account for those side effects.
- SQLite local storage depends on the mounted `data/` directory; deleting it resets local runtime state.

## Notes for Agents

- For local deployment, prefer the source-built `docker-compose.local.yml` path unless the user explicitly wants the published GHCR image.
- Run smoke checks against `http://127.0.0.1:8000` after local compose startup.
- If changing API behavior, add or run targeted tests under `test/` before relying on Docker smoke alone.
- If changing frontend pages, run `cd web; npm run build` or the full Docker build because the served UI comes from static export.
