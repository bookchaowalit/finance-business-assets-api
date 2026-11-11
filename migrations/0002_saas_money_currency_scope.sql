-- SPEC-003 (2026-11-11): exact money, ISO 4217 currency, workspace-defined scope (business-assets).
-- Amounts move from double precision to numeric; currency codes must be three upper-case letters;
-- owner_scope (the owner's own life areas) becomes scope, a free label each workspace defines.
-- Append-only: do not edit once applied.

-- asset
ALTER TABLE business_assets.assets NO FORCE ROW LEVEL SECURITY;
UPDATE business_assets.assets SET currency = upper(btrim(currency));
ALTER TABLE business_assets.assets FORCE ROW LEVEL SECURITY;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'business_assets.assets'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'business_assets.assets'::regclass AND attname = 'monthly_value')] LOOP EXECUTE format('ALTER TABLE business_assets.assets DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE business_assets.assets ALTER COLUMN monthly_value TYPE numeric(19,4) USING monthly_value::numeric(19,4);
ALTER TABLE business_assets.assets ADD CONSTRAINT assets_monthly_value_check CHECK (monthly_value IS NULL OR (monthly_value >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'business_assets.assets'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'business_assets.assets'::regclass AND attname = 'total_value')] LOOP EXECUTE format('ALTER TABLE business_assets.assets DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE business_assets.assets ALTER COLUMN total_value TYPE numeric(19,4) USING total_value::numeric(19,4);
ALTER TABLE business_assets.assets ADD CONSTRAINT assets_total_value_check CHECK (total_value IS NULL OR (total_value >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'business_assets.assets'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'business_assets.assets'::regclass AND attname = 'currency')] LOOP EXECUTE format('ALTER TABLE business_assets.assets DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE business_assets.assets ADD CONSTRAINT assets_currency_check CHECK (currency ~ '^[A-Z]{3}$');

-- asset-metric
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'business_assets.asset_metrics'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'business_assets.asset_metrics'::regclass AND attname = 'revenue')] LOOP EXECUTE format('ALTER TABLE business_assets.asset_metrics DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE business_assets.asset_metrics ALTER COLUMN revenue TYPE numeric(19,4) USING revenue::numeric(19,4);
ALTER TABLE business_assets.asset_metrics ADD CONSTRAINT asset_metrics_revenue_check CHECK (revenue >= 0);
