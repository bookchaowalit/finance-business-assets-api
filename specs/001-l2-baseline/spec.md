# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | in review (implemented; owner approval pending) |
| Repository / path | bookchaowalit/finance-business-assets-api / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | Owner (bookchaowalit): pending, see the Wave 2 report owner actions |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / pending owner |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, there was no type check, and the only tests were the generic contract suite; the asset and asset-metric rules (kinds, non-negative values, one metric per day, references) were not tested.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — An asset needs a name and a known type

- **Given** an owner with write permission
- **When** they create an asset without a name, without a type, with type `spaceship` or with a 201-character name
- **Then** the API answers 422 for each; every listed type (content, code, audience, data, brand, system, network, ip) is accepted
- **Test:** `tests/test_asset_validation.py::test_asset_type_must_be_a_known_kind` · level: integration (API + throwaway PostgreSQL)

### AC-02 — Asset values cannot be negative

- **Given** an owner with write permission
- **When** they create or update an asset with a negative `monthly_value` or `total_value`
- **Then** the API answers 422 and the stored value is unchanged; 0 is accepted
- **Test:** `tests/test_asset_validation.py::test_monthly_value_cannot_be_negative` · level: integration (API + throwaway PostgreSQL)

### AC-03 — A metric must point at an asset of the same workspace

- **Given** an asset in one workspace
- **When** a metric is created for a missing asset id, or by another workspace for that asset
- **Then** the API answers 422 `reference_not_found`
- **Test:** `tests/test_asset_validation.py::test_a_metric_cannot_point_at_an_asset_of_another_workspace` · level: integration (API + throwaway PostgreSQL)

### AC-04 — An asset has one metric row per day

- **Given** an asset with a metric for 2026-10-01
- **When** another metric for the same asset and day is created, or a metric is moved onto that day
- **Then** the API answers 409; the same day for another asset, or another day, is accepted
- **Test:** `tests/test_asset_defaults.py::test_an_asset_has_one_metric_row_per_day` · level: integration (API + throwaway PostgreSQL)

### AC-05 — New assets default to planning and THB; new metrics to zero counts

- **Given** a create request with only the required fields
- **When** the record is created
- **Then** an asset has status planning, currency THB and version 1; a metric has views, subscribers and revenue 0
- **Test:** `tests/test_asset_defaults.py::test_new_asset_defaults_to_planning_thb` · level: integration (API + throwaway PostgreSQL)

### AC-06 — An asset with metrics cannot be deleted

- **Given** an asset with one metric
- **When** the owner deletes the asset, then the metric, then the asset again
- **Then** the first delete answers 409 `has_dependents`; after the metric is gone the asset is deleted
- **Test:** `tests/test_asset_queries.py::test_an_asset_with_metrics_cannot_be_deleted` · level: integration (API + throwaway PostgreSQL)

### AC-07 — Metrics are listed by date and filtered by asset

- **Given** metrics created out of date order for two assets
- **When** the owner lists by `asset_id`, ascending and descending
- **Then** only that asset's metrics come back, oldest date first (newest first with `order=desc`); stats group by `asset_id` and refuse `metric_date`
- **Test:** `tests/test_asset_queries.py::test_metrics_are_listed_by_date_not_by_creation` · level: integration (API + throwaway PostgreSQL)

### AC-08 — Numbers fit their columns

- **Given** an int field (PostgreSQL integer) or a real field
- **When** a client sends 2**31, or NaN / Infinity / 1e400 as raw JSON
- **Then** the API answers 422 naming the field (before: a 500 from PostgreSQL, or the value silently stored as null)
- **Test:** `tests/test_contract.py::test_numbers_fit_their_columns` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `/v1/*` (all resources) | unchanged | same routes and payloads; see README |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "56"` (measured 58.35% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_asset_validation.py::test_asset_type_must_be_a_known_kind` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-02 | `tests/test_asset_validation.py::test_monthly_value_cannot_be_negative` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-03 | `tests/test_asset_validation.py::test_a_metric_cannot_point_at_an_asset_of_another_workspace` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-04 | `tests/test_asset_defaults.py::test_an_asset_has_one_metric_row_per_day` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_asset_defaults.py::test_new_asset_defaults_to_planning_thb` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_asset_queries.py::test_an_asset_with_metrics_cannot_be_deleted` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_asset_queries.py::test_metrics_are_listed_by_date_not_by_creation` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-08 | `tests/test_contract.py::test_numbers_fit_their_columns` | a6cbc60 · `.venv/bin/pytest -q -k numbers_fit` · `ValueError: Out of range float values are not JSON compliant: nan` | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |
