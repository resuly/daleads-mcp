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


def test_readme_tool_count_and_new_skills_are_complete():
    root = Path(__file__).resolve().parents[1]
    server_text = (root / "mcp_server.py").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert server_text.count("@mcp.tool()") == 25
    assert "It exposes 25 tools" in readme
    for name in (
        "daleads-property-core",
        "daleads-suburb-signals",
        "daleads-walkability-screening",
    ):
        skill = (root / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "TODO" not in skill


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


def test_property_core_uses_dedicated_closed_endpoint():
    with patch.object(mcp_server, "_api_get", return_value={"meta": {}}) as get:
        json.loads(mcp_server.property_core(address="163 Grattan St Carlton VIC"))
    get.assert_called_once_with(
        "/v1/property/core", {"address": "163 Grattan St Carlton VIC"})


def test_property_core_rejects_partial_coordinates_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.property_core(lat=-37.8))
    assert result["error"] == "pass both lat and lng, or use address"
    get.assert_not_called()


def test_suburb_signals_uses_sal_code_path():
    with patch.object(mcp_server, "_api_get", return_value={"data": {}}) as get:
        json.loads(mcp_server.suburb_signals("SAL20495"))
    get.assert_called_once_with("/v1/suburb-signals/SAL20495")


def test_suburb_and_sa2_resolvers_use_explicit_geography_catalogs():
    with patch.object(mcp_server, "_api_get", return_value={"data": []}) as get:
        json.loads(mcp_server.find_suburbs("Carlton", state="VIC", limit=5))
    get.assert_called_once_with(
        "/v1/suburbs", {"q": "Carlton", "per_page": 5, "state": "VIC"})

    with patch.object(mcp_server, "_api_get", return_value={"data": []}) as get:
        json.loads(mcp_server.find_sa2_regions("Carlton", state="VIC", limit=5))
    get.assert_called_once_with(
        "/v1/regions/sa2", {"name": "Carlton", "limit": 5, "state": "VIC"})


def test_sa2_forecast_uses_code_keyed_path():
    with patch.object(mcp_server, "_api_get", return_value={"data": {}}) as get:
        json.loads(mcp_server.sa2_population_forecast("206041117"))
    get.assert_called_once_with("/v1/regions/sa2/206041117/forecast")


def test_walkability_screening_uses_closed_component():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.walkability_screening(
            address="163 Grattan St Carlton VIC"))
    get.assert_called_once_with("/v1/property", {
        "address": "163 Grattan St Carlton VIC",
        "components": "scores.walkability",
    })


def test_walkability_rejects_missing_subject_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.walkability_screening())
    assert result["error"] == "pass an address or both lat and lng"
    get.assert_not_called()


def test_new_keyless_samples_use_focused_routes():
    cases = (
        (mcp_server.property_core_sample, "/v1/property/sample/core"),
        (mcp_server.suburb_signals_sample, "/v1/suburb-signals/sample"),
        (mcp_server.sa2_population_forecast_sample,
         "/v1/regions/sa2/forecast/sample"),
        (mcp_server.property_walkability_sample,
         "/v1/property/sample/walkability"),
    )
    for function, path in cases:
        with patch.object(mcp_server, "_api_get", return_value={"ok": True}) as get:
            assert json.loads(function()) == {"ok": True}
        get.assert_called_once_with(path)
