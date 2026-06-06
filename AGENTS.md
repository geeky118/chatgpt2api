# AGENTS

## Purpose

This repository is the durable operating guide for chatgpt2api agents. Keep project-specific commands, architecture facts, deployment notes, and UI constraints here or in linked docs instead of relying on chat history.

## Start Here

1. Read this file first.
2. Read [docs/architecture/system-overview.md](docs/architecture/system-overview.md) before non-trivial code changes.
3. For multi-step work, create or update a plan in [docs/exec-plans/active/](docs/exec-plans/active/).
4. For local runtime work, use [docs/runbooks/local-docker-compose.md](docs/runbooks/local-docker-compose.md).
5. Run the smallest meaningful verification from [docs/runbooks/verification.md](docs/runbooks/verification.md) before finishing.

## Working Rules

- Keep this file short and link outward to deeper docs.
- Do not rewrite existing runtime/deploy material when a focused runbook link is enough.
- Prefer repo-local scripts and documented commands over chat-only instructions.
- Say explicitly when validation could not run and leave the exact follow-up command.
- Do not commit generated runtime data from `data/`, local env files, logs, screenshots, or temporary build artifacts.

## UI Guardrails

- 正式对外页面禁止出现解释性占位文案、模板名、实现说明、调试态提示或“搜索/导购/专题从这里开始”这类产品说明型 copy，除非用户明确要求做原型或演示稿。
- 移动端首页固定壳默认按正式商业页面处理：优先搜索、主视觉、导航和导购效率，不要塞模板来源、后台配置名、实现思路说明或半成品引导文案。

## Common Commands

- Local Docker build/start: `docker compose -f docker-compose.local.yml up -d --build`
- Local Docker status: `docker compose -f docker-compose.local.yml ps`
- Local Docker logs: `docker compose -f docker-compose.local.yml logs -f app`
- Local smoke: `curl.exe -f http://127.0.0.1:8000/version` and `curl.exe -f "http://127.0.0.1:8000/health?format=json"`
- Python tests: `uv run pytest`
- Targeted tests: `uv run pytest test/test_v1_chat_completions.py`
- Frontend build only: `cd web; npm run build`

## Docs Index

- Architecture: [docs/architecture/system-overview.md](docs/architecture/system-overview.md)
- Local Docker Compose: [docs/runbooks/local-docker-compose.md](docs/runbooks/local-docker-compose.md)
- Verification: [docs/runbooks/verification.md](docs/runbooks/verification.md)
- Execution plans: [docs/exec-plans/](docs/exec-plans/)

## Definition of Done

- The requested change is implemented.
- Validation was run, or the exact blocker and next command are documented.
- New durable knowledge was written back into the repo if it would be expensive to rediscover.
