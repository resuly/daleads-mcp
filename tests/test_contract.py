import json
import re
from pathlib import Path
from unittest.mock import patch

import mcp_server


PROJECT_CONTRACT = json.loads(
    (Path(__file__).parents[1] / "contracts" / "project-intelligence-v1.json")
    .read_text(encoding="utf-8")
)


def _client_path(tool: str, project_uid: str | None = None) -> str:
    path = PROJECT_CONTRACT["tools"][tool]["path"].removeprefix("/api")
    if project_uid is not None:
        path = path.replace("{project_uid}", project_uid)
    return path


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


def test_project_contract_is_bound_to_one_official_key_and_endpoint():
    assert mcp_server.API_URL == PROJECT_CONTRACT["api_base_url"]
    assert PROJECT_CONTRACT["authentication"] == {
        "environment_variable": "DALEADS_API_KEY",
        "header": "Authorization: Bearer <key>",
        "entitlement": "project_intelligence",
    }


def test_search_projects_matches_provider_contract():
    with patch.object(mcp_server, "_api_get", return_value={"data": [], "meta": {}}) as get:
        json.loads(mcp_server.search_projects(
            q="Riverstone", state="NSW", stage="assessment",
            project_type="residential", changed_since="2026-08-01T00:00:00Z",
            page=2, limit=40,
        ))

    path, params = get.call_args.args
    assert path == _client_path("search_projects")
    assert set(params) == set(
        PROJECT_CONTRACT["tools"]["search_projects"]["query"]
    )
    assert params["per_page"] == 40
    assert "limit" not in params
    assert "days" not in params


def test_get_project_escapes_uid_as_one_path_segment():
    with patch.object(mcp_server, "_api_get", return_value={"data": {}}) as get:
        json.loads(mcp_server.get_project("nsw/hda 229407"))

    get.assert_called_once_with(
        _client_path("get_project", "nsw%2Fhda%20229407")
    )


def test_get_project_changes_matches_provider_contract():
    with patch.object(mcp_server, "_api_get", return_value={"data": [], "meta": {}}) as get:
        json.loads(mcp_server.get_project_changes(
            "project-1", since="2026-08-01T00:00:00Z", cursor=17, limit=75
        ))

    path, params = get.call_args.args
    assert path == _client_path("get_project_changes", "project-1")
    assert set(params) == set(
        PROJECT_CONTRACT["tools"]["get_project_changes"]["query"]
    )
    assert params["per_page"] == 75
    assert "changed_since" not in params


def test_nearby_projects_uses_radius_km_not_legacy_radius():
    with patch.object(mcp_server, "_api_get", return_value={"data": [], "meta": {}}) as get:
        json.loads(mcp_server.nearby_projects(
            lat=-33.8688, lng=151.2093, radius_km=8,
            stage="approved", project_type="mixed_use", page=3, limit=25,
        ))

    path, params = get.call_args.args
    assert path == _client_path("nearby_projects")
    assert set(params) == set(
        PROJECT_CONTRACT["tools"]["nearby_projects"]["query"]
    )
    assert params["radius_km"] == 8
    assert "radius" not in params


def test_cursor_contract_distinguishes_checkpoint_from_page_continuation():
    semantics = PROJECT_CONTRACT["cursor_semantics"]
    assert semantics["durable_checkpoint"] == "meta.cursor"
    assert semantics["page_continuation"] == "meta.next_cursor"


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
