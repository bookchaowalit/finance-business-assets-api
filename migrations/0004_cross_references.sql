-- SPEC-006 (2026-11-11): cross-service references between the finance cells (business-assets).
-- Append-only: do not edit once applied.

-- The relay sends a record's events in insert order (the row lock makes it the commit order).
ALTER TABLE business_assets.outbox ADD COLUMN seq bigint GENERATED ALWAYS AS IDENTITY;
DROP INDEX business_assets.outbox_unrelayed;
CREATE INDEX outbox_unrelayed ON business_assets.outbox (seq) WHERE relayed_at IS NULL;

-- SPEC-006: cross-service references, fed by finance.events.v1.
CREATE TABLE business_assets.ref_targets (
    workspace_id   uuid NOT NULL,
    target         text NOT NULL,
    record_id      bigint NOT NULL,
    status         text,
    deleted        boolean NOT NULL DEFAULT false,
    record_version bigint NOT NULL DEFAULT 0,
    event_seq      bigint NOT NULL DEFAULT 0,
    updated_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, target, record_id)
);
CREATE TABLE business_assets.ref_sources (
    workspace_id    uuid NOT NULL,
    source          text NOT NULL,
    source_id       bigint NOT NULL,
    field           text NOT NULL,
    target_resource text NOT NULL,
    target_id       bigint,
    deleted         boolean NOT NULL DEFAULT false,
    record_version  bigint NOT NULL DEFAULT 0,
    event_seq       bigint NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, source, source_id, field)
);
CREATE INDEX ref_sources_live ON business_assets.ref_sources (workspace_id, target_resource, target_id) WHERE NOT deleted;
CREATE TABLE business_assets.ref_offsets (
    topic       text NOT NULL,
    partition   integer NOT NULL,
    next_offset bigint NOT NULL,
    PRIMARY KEY (topic, partition)
);
ALTER TABLE business_assets.ref_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_assets.ref_targets FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON business_assets.ref_targets USING (workspace_id = business_assets.current_workspace());
CREATE POLICY publisher_sync ON business_assets.ref_targets TO business_assets_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON business_assets.ref_targets TO business_assets_api;
GRANT SELECT, INSERT, UPDATE ON business_assets.ref_targets TO business_assets_publisher;
ALTER TABLE business_assets.ref_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_assets.ref_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON business_assets.ref_sources USING (workspace_id = business_assets.current_workspace());
CREATE POLICY publisher_sync ON business_assets.ref_sources TO business_assets_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON business_assets.ref_sources TO business_assets_api;
GRANT SELECT, INSERT, UPDATE ON business_assets.ref_sources TO business_assets_publisher;
GRANT SELECT, INSERT, UPDATE ON business_assets.ref_offsets TO business_assets_publisher;

-- Rows written before SPEC-005 announce themselves once, so other cells learn their ids.
ALTER TABLE business_assets.outbox NO FORCE ROW LEVEL SECURITY;
ALTER TABLE business_assets.assets NO FORCE ROW LEVEL SECURITY;
INSERT INTO business_assets.outbox (workspace_id, type, subject, classification, payload, correlation_id) SELECT workspace_id, 'business-assets.asset.snapshot', 'empire:business-assets:asset:' || id, 'confidential', jsonb_build_object('asset_type', asset_type, 'status', status, 'currency', currency, 'launched_at', launched_at, 'version', version, 'deleted', false), 'spec-006-snapshot' FROM business_assets.assets ORDER BY id;
ALTER TABLE business_assets.assets FORCE ROW LEVEL SECURITY;
ALTER TABLE business_assets.asset_metrics NO FORCE ROW LEVEL SECURITY;
INSERT INTO business_assets.outbox (workspace_id, type, subject, classification, payload, correlation_id) SELECT workspace_id, 'business-assets.asset-metric.snapshot', 'empire:business-assets:asset-metric:' || id, 'confidential', jsonb_build_object('asset_id', asset_id, 'metric_date', metric_date, 'version', version, 'deleted', false), 'spec-006-snapshot' FROM business_assets.asset_metrics ORDER BY id;
ALTER TABLE business_assets.asset_metrics FORCE ROW LEVEL SECURITY;
ALTER TABLE business_assets.outbox FORCE ROW LEVEL SECURITY;
