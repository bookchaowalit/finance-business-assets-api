# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through `life-dashboard-web` (finance page: active assets and their summed
  monthly value), the cell's own MCP server (`business-assets-mcp`) and the hosted tool hub
  (`platform-mcp-remote-worker`).
- Automations with an `empire-platform` token (for example `owner-mcp`), within the permissions
  `business-assets.asset:read|write|delete` and `business-assets.asset-metric:read|write|delete`.

## Product Purpose

The list of things the business owns that are not bank money: content, code, audience, data,
brand, system, network and IP assets, each with an estimated monthly and total value, and a daily
metric history (views, subscribers, revenue, engagement rate) per asset.

Success: every asset the owner counts as business value exists once with its status and value, and
the dashboard can sum the monthly value of the active ones. Nothing in this repository feeds the
daily metrics yet [ต้องยืนยัน: which job or person writes `asset-metric` rows].

## Positioning

One capability, one service: its own API (Railway), its own database (Neon) with row-level
security per workspace, and authorization, executions and audit through `empire-platform`. It is
workspace-scoped, so the same service can serve other tenants without code changes.

## Operating Context

- Production: `https://business-assets-api-production.up.railway.app` (`/health`), deployed by
  merging to `main` after CI.
- Data starts empty (created 2026-10-12 from the retired `finance_*` tables' fields); imports keep
  old ids in `legacy_id`.
- Monitored by `platform-uptime-worker` (probed hourly, because the service sleeps when idle);
  errors go to Sentry without personal data.

## Capabilities and Constraints

- `/v1/assets`: list (filters `asset_type`, `status`; ordered by id), stats (grouped by one of
  those filters), get, get-by-legacy-id, create (with `Idempotency-Key`), patch (with
  `expected_version`), delete.
- `/v1/asset-metrics`: the same routes; filter `asset_id`; listed by `metric_date` (then id).
- Asset rules: `name` (at most 200 characters) and `asset_type` are required; `asset_type` is one
  of content, code, audience, data, brand, system, network, ip; `status` is one of planning
  (default), building, active, maintenance, archived; `monthly_value` and `total_value` cannot be
  negative; `currency` defaults to THB (at most 12 characters). Asset names are not unique.
- Metric rules: `asset_id` and `metric_date` are required; `asset_id` must be an asset of the same
  workspace (otherwise 422 `reference_not_found`); an asset has at most one metric row per day
  (409); `views` and `subscribers` are whole numbers from 0 and default to 0; `revenue` defaults
  to 0; none of the numbers can be negative.
- An asset that still has metrics cannot be deleted (409 `has_dependents`); delete its metrics
  first.
- Out of scope: collecting the metrics from platforms, and revenue accounting (revenue and
  invoices stay in the CRM ledger).

## Measures

Proposed (nothing collects them yet):

- Active assets with a metric row in the last 30 days.
- Sum of `monthly_value` of active assets, per currency (the dashboard already shows it).
- 5xx rate and p95 latency on `/v1/assets` (Sentry and uptime worker).
