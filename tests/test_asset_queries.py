"""Listing, grouping and the lifecycle of business assets and their metrics."""

from asset_helpers import ASSETS, METRICS, create, create_metric

# --- asset -----------------------------------------------------------------------------------


def test_list_assets_filters_by_asset_type(client, owner):
    create(client, owner, name="Blog", asset_type="content")
    create(client, owner, name="Library", asset_type="code")
    listed = client.get(ASSETS, headers=owner, params={"asset_type": "code"})
    assert listed.status_code == 200, listed.text
    assert {item["asset_type"] for item in listed.json()["items"]} == {"code"}


def test_list_assets_filters_by_status(client, owner):
    create(client, owner, name="Old site", status="archived")
    create(client, owner, name="New site", status="building")
    listed = client.get(ASSETS, headers=owner, params={"status": "archived"})
    assert listed.status_code == 200, listed.text
    assert {item["status"] for item in listed.json()["items"]} == {"archived"}


def test_list_assets_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(ASSETS, headers=owner, params={"platform": "youtube"})
    assert listed.status_code == 422


def test_assets_are_listed_in_creation_order(client, owner):
    ids = [create(client, owner, name=f"Order {n}").json()["id"] for n in range(3)]
    listed = client.get(ASSETS, headers=owner).json()["items"]
    assert [item["id"] for item in listed] == sorted(ids)


def test_asset_stats_count_per_type_and_status(client, owner):
    create(client, owner, name="A", asset_type="brand")
    create(client, owner, name="B", asset_type="brand", status="active")
    by_type = client.get(
        f"{ASSETS}/stats", headers=owner, params={"group_by": "asset_type"}
    )
    assert by_type.status_code == 200, by_type.text
    assert by_type.json()["groups"]["brand"] >= 2
    by_status = client.get(
        f"{ASSETS}/stats", headers=owner, params={"group_by": "status"}
    )
    assert by_status.json()["groups"]["active"] >= 1


def test_asset_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(f"{ASSETS}/stats", headers=owner, params={"group_by": "name"})
    assert stats.status_code == 422


def test_launching_an_asset_bumps_its_version(client, owner):
    asset = create(client, owner, name="Launch me").json()
    launched = client.patch(
        f"{ASSETS}/{asset['id']}",
        headers=owner,
        json={"status": "active", "launched_at": "2026-10-20"},
    )
    assert launched.status_code == 200, launched.text
    assert launched.json()["status"] == "active"
    assert launched.json()["launched_at"] == "2026-10-20"
    assert launched.json()["version"] == 2


def test_an_asset_patch_that_changes_nothing_keeps_the_version(client, owner):
    asset = create(client, owner, name="Stable", monthly_value=10).json()
    same = client.patch(
        f"{ASSETS}/{asset['id']}",
        headers=owner,
        json={"name": "Stable", "monthly_value": 10},
    )
    assert same.status_code == 200, same.text
    assert same.json()["version"] == 1


def test_a_negative_value_is_refused_on_asset_update(client, owner):
    asset = create(client, owner, name="Keep value", total_value=500).json()
    path = f"{ASSETS}/{asset['id']}"
    assert (
        client.patch(path, headers=owner, json={"total_value": -1}).status_code == 422
    )
    assert client.get(path, headers=owner).json()["total_value"] == 500


def test_an_asset_with_metrics_cannot_be_deleted(client, owner):
    asset = create(client, owner, name="Measured").json()
    metric = create_metric(client, owner, asset["id"]).json()
    refused = client.delete(f"{ASSETS}/{asset['id']}", headers=owner)
    assert refused.status_code == 409, refused.text
    assert refused.json()["detail"] == {"error": "has_dependents"}
    assert client.delete(f"{METRICS}/{metric['id']}", headers=owner).status_code == 204
    assert client.delete(f"{ASSETS}/{asset['id']}", headers=owner).status_code == 204


def test_deleting_an_asset_removes_it(client, owner):
    asset = create(client, owner, name="Short lived").json()
    path = f"{ASSETS}/{asset['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


# --- asset metric ----------------------------------------------------------------------------


def test_list_metrics_filters_by_asset(client, owner):
    one = create(client, owner, name="One").json()
    two = create(client, owner, name="Two").json()
    create_metric(client, owner, one["id"])
    create_metric(client, owner, two["id"])
    listed = client.get(METRICS, headers=owner, params={"asset_id": one["id"]})
    assert listed.status_code == 200, listed.text
    assert {m["asset_id"] for m in listed.json()["items"]} == {one["id"]}


def test_metrics_are_listed_by_date_not_by_creation(client, owner):
    asset = create(client, owner, name="Timeline").json()
    for day in ("2026-10-03", "2026-10-01", "2026-10-02"):
        create_metric(client, owner, asset["id"], metric_date=day)
    params = {"asset_id": asset["id"]}
    listed = client.get(METRICS, headers=owner, params=params).json()["items"]
    assert [m["metric_date"] for m in listed] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
    ]
    latest = client.get(METRICS, headers=owner, params={**params, "order": "desc"})
    assert latest.json()["items"][0]["metric_date"] == "2026-10-03"


def test_list_metrics_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(METRICS, headers=owner, params={"views": "1"})
    assert listed.status_code == 422


def test_metric_stats_count_per_asset(client, owner):
    asset = create(client, owner, name="Counted").json()
    for day in ("2026-10-01", "2026-10-02"):
        create_metric(client, owner, asset["id"], metric_date=day)
    stats = client.get(
        f"{METRICS}/stats", headers=owner, params={"group_by": "asset_id"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"][str(asset["id"])] == 2


def test_metric_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{METRICS}/stats", headers=owner, params={"group_by": "metric_date"}
    )
    assert stats.status_code == 422


def test_updating_a_metric_bumps_its_version(client, owner):
    asset = create(client, owner, name="Growing").json()
    metric = create_metric(client, owner, asset["id"], views=10).json()
    path = f"{METRICS}/{metric['id']}"
    grown = client.patch(path, headers=owner, json={"views": 25, "subscribers": 3})
    assert grown.status_code == 200, grown.text
    assert grown.json()["views"] == 25
    assert grown.json()["version"] == 2
    same = client.patch(path, headers=owner, json={"views": 25})
    assert same.json()["version"] == 2


def test_deleting_a_metric_keeps_its_asset(client, owner):
    asset = create(client, owner, name="Survivor").json()
    metric = create_metric(client, owner, asset["id"]).json()
    assert client.delete(f"{METRICS}/{metric['id']}", headers=owner).status_code == 204
    assert client.get(f"{METRICS}/{metric['id']}", headers=owner).status_code == 404
    assert client.get(f"{ASSETS}/{asset['id']}", headers=owner).status_code == 200
