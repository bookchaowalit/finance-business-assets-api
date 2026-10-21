"""Shared helpers for the business-assets domain tests."""

import uuid
from typing import Any

ASSETS = "/v1/assets"
METRICS = "/v1/asset-metrics"


def create(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    return client.post(
        ASSETS, headers=owner, json={"name": "Asset", "asset_type": "content", **fields}
    )


def create_metric(
    client: Any, owner: dict[str, str], asset_id: int, **fields: Any
) -> Any:
    body = {"asset_id": asset_id, "metric_date": "2026-10-01", **fields}
    return client.post(METRICS, headers=owner, json=body)


def other_workspace(harness: Any, platform: Any) -> dict[str, str]:
    """A token for a second owner in a different workspace."""
    actor = uuid.uuid4()
    platform.grants[actor] = set(harness.cell.permissions())
    return harness.token(actor, uuid.uuid4())
