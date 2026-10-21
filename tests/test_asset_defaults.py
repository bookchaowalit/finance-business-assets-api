"""Defaults, uniqueness and imports of business assets and their metrics."""

from asset_helpers import ASSETS, METRICS, create, create_metric


def test_new_asset_defaults_to_planning_thb(client, owner):
    response = create(client, owner, name="Fresh")
    assert response.status_code == 201, response.text
    asset = response.json()
    assert asset["status"] == "planning"
    assert asset["currency"] == "THB"
    assert asset["version"] == 1
    assert asset["monthly_value"] is None
    assert asset["total_value"] is None


def test_asset_values_keep_their_decimal_value(client, owner):
    asset = create(
        client, owner, name="Decimals", monthly_value=99.5, total_value=1234.56
    ).json()
    assert asset["monthly_value"] == 99.5
    assert asset["total_value"] == 1234.56


def test_two_assets_may_share_a_name(client, owner):
    assert create(client, owner, name="Twin").status_code == 201
    assert create(client, owner, name="Twin").status_code == 201


def test_asset_import_keeps_the_old_id(client, owner):
    imported = create(client, owner, name="Imported", legacy_id=3131)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 3131
    found = client.get(f"{ASSETS}/legacy/3131", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["name"] == "Imported"
    assert create(client, owner, name="Again", legacy_id=3131).status_code == 409


def test_new_metric_defaults_to_zero_counts(client, owner):
    asset = create(client, owner, name="Zeros").json()
    response = create_metric(client, owner, asset["id"])
    assert response.status_code == 201, response.text
    metric = response.json()
    assert metric["views"] == 0
    assert metric["subscribers"] == 0
    assert metric["revenue"] == 0
    assert metric["engagement_rate"] is None
    assert metric["version"] == 1


def test_an_asset_has_one_metric_row_per_day(client, owner):
    asset = create(client, owner, name="Daily").json()
    assert create_metric(client, owner, asset["id"]).status_code == 201
    again = create_metric(client, owner, asset["id"], views=5)
    assert again.status_code == 409


def test_a_metric_date_may_repeat_for_another_asset_or_day(client, owner):
    first = create(client, owner, name="First").json()
    second = create(client, owner, name="Second").json()
    assert create_metric(client, owner, first["id"]).status_code == 201
    other_asset = create_metric(client, owner, second["id"])
    other_day = create_metric(client, owner, first["id"], metric_date="2026-10-02")
    assert other_asset.status_code == 201, other_asset.text
    assert other_day.status_code == 201, other_day.text


def test_moving_a_metric_onto_a_taken_day_is_refused(client, owner):
    asset = create(client, owner, name="Collide").json()
    create_metric(client, owner, asset["id"], metric_date="2026-10-01")
    later = create_metric(client, owner, asset["id"], metric_date="2026-10-02").json()
    clash = client.patch(
        f"{METRICS}/{later['id']}", headers=owner, json={"metric_date": "2026-10-01"}
    )
    assert clash.status_code == 409


def test_metric_import_keeps_the_old_id(client, owner):
    asset = create(client, owner, name="Import host").json()
    imported = create_metric(client, owner, asset["id"], legacy_id=777)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 777
    found = client.get(f"{METRICS}/legacy/777", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["asset_id"] == asset["id"]
