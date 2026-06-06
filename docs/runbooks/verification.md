# Verification Runbook

## Fast Local Checks

- API/unit tests: `uv run pytest`
- Targeted API tests: `uv run pytest test/<target_test_file>.py`
- Frontend static export: `cd web; npm run build`
- Full local image build/start: `docker compose -f docker-compose.local.yml up -d --build`
- Container status: `docker compose -f docker-compose.local.yml ps`
- Version smoke: `curl.exe -f http://127.0.0.1:8000/version`
- Health smoke: `curl.exe -f "http://127.0.0.1:8000/health?format=json"`

## Local Docker Compose Gate

Use this when the task touches runtime docs, Docker files, app startup, environment variables, static frontend serving, or deployment instructions.

1. Ensure `config.json` exists and has a valid `auth-key`, or set `CHATGPT2API_AUTH_KEY`.
2. Start locally: `docker compose -f docker-compose.local.yml up -d --build`.
3. Check status: `docker compose -f docker-compose.local.yml ps`.
4. Check logs if startup is not healthy: `docker compose -f docker-compose.local.yml logs --tail=120 app`.
5. Smoke the public endpoints:
   - `curl.exe -f http://127.0.0.1:8000/version`
   - `curl.exe -f "http://127.0.0.1:8000/health?format=json"`
6. Open `http://127.0.0.1:8000/` for UI validation when frontend output changed.

## Change-Specific Checks

- API protocol changes: run the closest `test/test_v1_*.py` files.
- Account/storage changes: run account, config, and storage-related tests plus `/api/storage/info` manually with an admin token if needed.
- Image changes: run image API/task/storage tests and verify generated artifacts under `data/images/` only locally.
- Registration changes: prefer isolated service tests first; live registration depends on external mail/proxy/OpenAI behavior and should be marked as an integration check.
- Frontend UI changes: run the Next build and a browser smoke against the composed app.

## Evidence

Record concrete command results in the active execution plan when a task is multi-step. Include the command, success/failure, endpoint URL, and any follow-up needed. Do not paste secrets from config or logs.
