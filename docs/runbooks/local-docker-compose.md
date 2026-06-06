# Local Docker Compose Runbook

## Default Path

Use `docker-compose.local.yml` for local deployment from source:

```powershell
docker compose -f docker-compose.local.yml up -d --build
```

The app is available at:

- UI and API base: `http://127.0.0.1:8000`
- Version endpoint: `http://127.0.0.1:8000/version`
- Health endpoint: `http://127.0.0.1:8000/health?format=json`

## What It Starts

- Service: `app`
- Container: `chatgpt2api-local`
- Image: `chatgpt2api:local`
- Port mapping: `8000:80`
- Persistent data: `./data:/app/data`
- Runtime config: `./config.json:/app/config.json`
- Storage backend: SQLite by default, stored at `/app/data/accounts.db`

## Prerequisites

- Docker Desktop is running.
- `config.json` exists in the repository root.
- `config.json` contains a valid `auth-key`, or `CHATGPT2API_AUTH_KEY` is supplied through compose/environment.
- Host port `8000` is free.

## Operations

Start or rebuild:

```powershell
docker compose -f docker-compose.local.yml up -d --build
```

View status:

```powershell
docker compose -f docker-compose.local.yml ps
```

View logs:

```powershell
docker compose -f docker-compose.local.yml logs -f app
```

Stop:

```powershell
docker compose -f docker-compose.local.yml down
```

Reset local runtime data only when explicitly intended:

```powershell
docker compose -f docker-compose.local.yml down
Remove-Item -Recurse -Force .\data
```

## Smoke Checks

```powershell
curl.exe -f http://127.0.0.1:8000/version
curl.exe -f "http://127.0.0.1:8000/health?format=json"
```

`/health?format=json` can return `"status":"degraded"` when no usable accounts are configured. That still proves the service is reachable; account-pool health must be judged separately.

## Published Image Alternative

Use `docker-compose.yml` only when you want the published GHCR image instead of the local source build. It maps host port `3000` to container port `80`.
