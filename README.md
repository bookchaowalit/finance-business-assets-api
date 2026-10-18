# finance-business-assets-api
The Business assets cell: its own API (Railway, serverless) and its own Neon
database, first generated from `cell.yaml` (one of the ten finance
services split on 2026-10-12). It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `finance-business-assets-api`, service `business-assets-api` (Serverless) |
| Data | Neon project `finance-business-assets-api`, database `business_assets` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`business-assets`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `business-assets.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/assets` | asset | `asset_type`, `status` |
| `/v1/asset-metrics` | asset-metric | `asset_id` |

## Develop and operate

```bash
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/business-assets-db provision
npm install && railway config apply && railway up --ci --service business-assets-api
railway scale --service business-assets-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Railway variables: `SENTRY_DSN` (error reporting; unset = off, see `src/cellkit/_sentry.py`),
`BUSINESS_ASSETS_DB_MODE=hosted`, `BUSINESS_ASSETS_DB_URL_API`,
`BUSINESS_ASSETS_JWT_PUBLIC_KEY_PEM`, `BUSINESS_ASSETS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.
