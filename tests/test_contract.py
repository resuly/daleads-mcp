import json
import re
from pathlib import Path
from unittest.mock import patch

import mcp_server


def test_release_versions_are_one_contract():
    root = Path(__file__).resolve().parents[1]
    project_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'^version = "([^"]+)"$', project_text, re.MULTILINE)
    assert version_match, "pyproject.toml has no single-line project version"
    project_version = version_match.group(1)
    registry = json.loads((root / "server.json").read_text(encoding="utf-8"))
    assert registry["version"] == project_version
    assert {package["version"] for package in registry["packages"]} == {
        project_version,
    }


def test_search_das_uses_current_api_parameters():
    with patch.object(mcp_server, "_api_get", return_value={"data": []}) as get:
        json.loads(
            mcp_server.search_das(
                postcode="3000",
                since="2026-07-01",
                status_group="approved",
                is_residential=True,
            )
        )

    path, params = get.call_args.args
    assert path == "/v1/das"
    assert params["postcode"] == "3000"
    assert params["since"] == "2026-07-01"
    assert params["status_group"] == "approved"
    assert params["is_residential"] is True
    assert "q" not in params
    assert "days" not in params


def test_nearby_das_uses_radius_km_and_since():
    with patch.object(mcp_server, "_api_get", return_value={"data": []}) as get:
        json.loads(
            mcp_server.nearby_das(
                lat=-37.8136,
                lng=144.9631,
                radius_km=3.5,
                since="2026-07-01",
            )
        )

    path, params = get.call_args.args
    assert path == "/v1/das/nearby"
    assert params["radius_km"] == 3.5
    assert params["since"] == "2026-07-01"
    assert "radius" not in params
    assert "days" not in params


def test_list_councils_applies_limit_locally():
    payload = {"data": [{"council": "A"}, {"council": "B"}], "meta": {"total": 2}}
    with patch.object(mcp_server, "_api_get", return_value=payload) as get:
        result = json.loads(mcp_server.list_councils(limit=1))

    get.assert_called_once_with("/v1/councils")
    assert result["data"] == [{"council": "A"}]
    assert result["meta"] == {"total": 2, "returned": 1}


def test_bushfire_screening_uses_closed_component_set():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.bushfire_screening(
            address="15 Cliff Drive, Katoomba NSW 2780"))

    get.assert_called_once_with("/v1/property", {
        "address": "15 Cliff Drive, Katoomba NSW 2780",
        "components": "scores.bushfire,hazards.bushfire",
    })


def test_bushfire_screening_rejects_ambiguous_coordinate_input_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.bushfire_screening(lat=-33.7))
    assert result["error"] == "pass both lat and lng, or use address"
    get.assert_not_called()


def test_property_bushfire_sample_uses_keyless_focused_route():
    with patch.object(mcp_server, "_api_get", return_value={"meta": {"sample": True}}) as get:
        result = json.loads(mcp_server.property_bushfire_sample())
    get.assert_called_once_with("/v1/property/sample/bushfire")
    assert result["meta"]["sample"] is True


def test_contamination_screening_uses_closed_component_set():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.contamination_screening(
            address="163 Grattan Street, Carlton VIC 3053"))

    get.assert_called_once_with("/v1/property", {
        "address": "163 Grattan Street, Carlton VIC 3053",
        "components": "scores.contamination",
    })


def test_contamination_screening_rejects_ambiguous_coordinate_input_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.contamination_screening(lng=144.96))
    assert result["error"] == "pass both lat and lng, or use address"
    get.assert_not_called()


def test_property_contamination_sample_uses_keyless_focused_route():
    with patch.object(mcp_server, "_api_get", return_value={"meta": {"sample": True}}) as get:
        result = json.loads(mcp_server.property_contamination_sample())
    get.assert_called_once_with("/v1/property/sample/contamination")
    assert result["meta"]["sample"] is True


def test_neighbourhood_context_uses_closed_component_set():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.neighbourhood_context(
            address="163 Grattan Street, Carlton VIC 3053"))

    get.assert_called_once_with("/v1/property", {
        "address": "163 Grattan Street, Carlton VIC 3053",
        "components": "scores.heat_island,scores.view_quality",
    })


def test_neighbourhood_context_rejects_ambiguous_coordinates_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.neighbourhood_context(lat=-37.8))
    assert result["error"] == "pass both lat and lng, or use address"
    get.assert_not_called()


def test_neighbourhood_context_rejects_mixed_subject_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.neighbourhood_context(
            address="163 Grattan Street, Carlton VIC 3053",
            lat=-37.8,
            lng=144.96,
        ))
    assert result["error"] == \
        "pass either address or both lat and lng, not both"
    get.assert_not_called()


def test_solar_resource_uses_closed_component_set():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.solar_resource(lat=-37.8, lng=144.96))

    get.assert_called_once_with("/v1/property", {
        "lat": -37.8,
        "lng": 144.96,
        "components": "scores.solar",
    })


def test_solar_resource_requires_a_subject_before_network():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.solar_resource())
    assert result["error"] == "pass an address or both lat and lng"
    get.assert_not_called()


def test_solar_resource_treats_blank_address_as_no_subject():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.solar_resource(address="   "))
    assert result["error"] == "pass an address or both lat and lng"
    get.assert_not_called()


def test_solar_resource_rejects_mixed_subject_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.solar_resource(
            address="1 Wrong Street, Sydney NSW",
            lat=-37.8,
            lng=144.96,
        ))
    assert result["error"] == \
        "pass either address or both lat and lng, not both"
    get.assert_not_called()


def test_property_context_sample_uses_keyless_focused_route():
    with patch.object(mcp_server, "_api_get", return_value={
        "meta": {"sample": True},
    }) as get:
        result = json.loads(mcp_server.property_context_sample())
    get.assert_called_once_with("/v1/property/sample/context")
    assert result["meta"]["sample"] is True
