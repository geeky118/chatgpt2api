# Local Docker Compose Harness Setup

## Goal

Document the current project in harness-engineering form and deploy it locally through Docker Compose.

## Context

- The repository already has a Python FastAPI backend, a statically exported Next.js frontend, a `Dockerfile`, `docker-compose.yml`, and `docker-compose.local.yml`.
- Local source deployment should use `docker-compose.local.yml`, which builds `chatgpt2api:local` and exposes the app on `http://127.0.0.1:8000`.
- The container needs `config.json` or `CHATGPT2API_AUTH_KEY` to provide the auth key.

## Constraints

- Do not change business behavior for this task.
- Keep durable guidance in repository docs.
- Do not print secrets from `config.json`.
- Validate local Docker Compose startup before closing.

## Approach

1. Bootstrap and tailor harness documentation.
2. Record the local Docker Compose runbook and verification path.
3. Start the app with `docker compose -f docker-compose.local.yml up -d --build`.
4. Smoke `/version` and `/health?format=json`.

## Validation

- Passed: `docker compose -f docker-compose.local.yml build --progress=plain app`
- Passed: `docker compose -f docker-compose.local.yml up -d`
- Passed: `docker compose -f docker-compose.local.yml ps`
  - `chatgpt2api-local` is `Up`, mapped as `0.0.0.0:8000->80/tcp`.
- Passed: `curl.exe -f http://127.0.0.1:8000/version`
  - Returned `{"version":"1.4.1"}`.
- Passed: `curl.exe -f "http://127.0.0.1:8000/health?format=json"`
  - Returned `status=degraded` because the local account pool is empty, while SQLite storage health is `healthy`.
- Passed: `curl.exe -f http://127.0.0.1:8000/ -o NUL -w "%{http_code} %{content_type}"`
  - Returned `200 text/html; charset=utf-8`.

## Decisions

- Use the local source-built compose file as the default local deployment path.
- Keep `docker-compose.yml` documented as the published-image alternative.
- Add Dockerfile defaults for `BUILDPLATFORM`, `TARGETPLATFORM`, and `TARGETARCH` so local Docker Compose builds do not fail when those args are not injected.
- Use Aliyun Debian mirrors inside the Docker build to avoid local default Debian mirror `502 Bad Gateway` failures.

## Risks

- Docker build may take time because it installs Node dependencies, builds Next static output, installs Python dependencies through `uv`, and builds native Python packages.
- Local health may be `degraded` if no usable accounts are configured.
- First successful local build was slow: `npm install` took about 19 minutes, and the full image build required cached/retried dependency downloads.

## Open Questions

- None.
