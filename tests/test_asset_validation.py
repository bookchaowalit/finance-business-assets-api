"""What business assets refuse: unknown kinds, negative values, missing or foreign asset references."""

from asset_helpers import (
    ASSETS,
    METRICS,
    create,
    create_metric,
    other_workspace,
)

# --- asset -----------------------------------------------------------------------------------


def test_asset_name_is_required(client, owner):
    response = client.post(ASSETS, headers=owner, json={"asset_type": "code"})
    assert response.status_code == 422


def test_asset_name_is_limited_to_200_characters(client, owner):
    assert create(client, owner, name="x" * 201).status_code == 422
    assert create(client, owner, name="y" * 200).status_code == 201


def test_asset_type_is_required(client, owner):
    response = client.post(ASSETS, headers=owner, json={"name": "Untyped"})
    assert response.status_code == 422


def test_asset_type_must_be_a_known_kind(client, owner):
    response = create(client, owner, name="Odd kind", asset_type="spaceship")
    assert response.status_code == 422


def test_every_listed_asset_type_is_accepted(client, owner):
    for kind in (
        "content",
        "code",
        "audience",
        "data",
        "brand",
        "system",
        "network",
        "ip",
    ):
        response = create(client, owner, name=f"Kind {kind}", asset_type=kind)
        assert response.status_code == 201, (kind, response.text)


def test_status_must_be_a_known_status(client, owner):
    response = create(client, owner, name="Odd status", status="frozen")
    assert response.status_code == 422


def test_monthly_value_cannot_be_negative(client, owner):
    assert create(client, owner, name="Neg month", monthly_value=-1).status_code == 422
    assert create(client, owner, name="Zero month", monthly_value=0).status_code == 201


def test_total_value_cannot_be_negative(client, owner):
    assert create(client, owner, name="Neg total", total_value=-1).status_code == 422
    assert create(client, owner, name="Zero total", total_value=0).status_code == 201


def test_currency_code_is_at_most_12_characters(client, owner):
    assert create(client, owner, name="Long ccy", currency="C" * 13).status_code == 422
    assert create(client, owner, name="USD asset", currency="USD").status_code == 201


def test_launch_date_must_be_a_real_calendar_date(client, owner):
    response = create(client, owner, name="Bad date", launched_at="2026-02-30")
    assert response.status_code == 422


def test_unknown_asset_fields_are_refused(client, owner):
    response = create(client, owner, name="Extra", colour="red")
    assert response.status_code == 422


# --- asset metric ----------------------------------------------------------------------------


def test_a_metric_needs_an_asset(client, owner):
    response = client.post(METRICS, headers=owner, json={"metric_date": "2026-10-01"})
    assert response.status_code == 422


def test_a_metric_needs_a_date(client, owner):
    asset = create(client, owner, name="Dateless").json()
    response = client.post(METRICS, headers=owner, json={"asset_id": asset["id"]})
    assert response.status_code == 422


def test_a_metric_cannot_point_at_a_missing_asset(client, owner):
    response = create_metric(client, owner, 987654321)
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {"error": "reference_not_found"}


def test_a_metric_asset_id_must_be_positive(client, owner):
    assert create_metric(client, owner, 0).status_code == 422
    assert create_metric(client, owner, -3).status_code == 422


def test_a_metric_cannot_point_at_an_asset_of_another_workspace(
    client, owner, harness, platform
):
    asset = create(client, owner, name="Mine").json()
    stranger = other_workspace(harness, platform)
    response = create_metric(client, stranger, asset["id"])
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {"error": "reference_not_found"}


def test_a_metric_cannot_be_moved_to_a_missing_asset(client, owner):
    asset = create(client, owner, name="Stays put").json()
    metric = create_metric(client, owner, asset["id"]).json()
    path = f"{METRICS}/{metric['id']}"
    refused = client.patch(path, headers=owner, json={"asset_id": 987654321})
    assert refused.status_code == 422, refused.text
    assert client.get(path, headers=owner).json()["asset_id"] == asset["id"]


def test_metric_counts_cannot_be_negative(client, owner):
    asset = create(client, owner, name="Counted").json()
    for field in ("views", "subscribers"):
        refused = create_metric(client, owner, asset["id"], **{field: -1})
        assert refused.status_code == 422, field


def test_metric_revenue_and_engagement_cannot_be_negative(client, owner):
    asset = create(client, owner, name="Earning").json()
    assert create_metric(client, owner, asset["id"], revenue=-0.01).status_code == 422
    refused = create_metric(client, owner, asset["id"], engagement_rate=-0.5)
    assert refused.status_code == 422


def test_metric_counts_must_be_whole_numbers(client, owner):
    asset = create(client, owner, name="Whole").json()
    assert create_metric(client, owner, asset["id"], views=1.5).status_code == 422


def test_metric_date_must_be_a_real_calendar_date(client, owner):
    asset = create(client, owner, name="Calendar").json()
    refused = create_metric(client, owner, asset["id"], metric_date="2026-04-31")
    assert refused.status_code == 422
