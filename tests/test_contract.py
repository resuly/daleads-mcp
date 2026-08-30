import json
from pathlib import Path
from unittest.mock import patch

import mcp_server
import pytest

from scripts.check_contamination_contract import compare as compare_contamination_contract


PROJECT_CONTRACT = json.loads(
    (Path(__file__).parents[1] / "contracts" / "project-intelligence-v1.json")
    .read_text(encoding="utf-8")
)

CONTAMINATION_CONTRACT = json.loads(
    (Path(__file__).parents[1] / "contracts/contamination-screening-v1.json")
    .read_text(encoding="utf-8")
)


def _client_path(tool: str, project_uid: str | None = None,
                 watch_uid: str | None = None) -> str:
    path = PROJECT_CONTRACT["tools"][tool]["path"].removeprefix("/api")
    if project_uid is not None:
        path = path.replace("{project_uid}", project_uid)
    if watch_uid is not None:
        path = path.replace("{watch_uid}", watch_uid)
    return path


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


def test_contamination_contract_records_provider_only_fail_closed_surface():
    assert CONTAMINATION_CONTRACT["contract_version"] == \
        "contamination-screening-v1"
    assert CONTAMINATION_CONTRACT["provider_sample_path"] == \
        "/api/v1/property/sample/contamination"
    assert CONTAMINATION_CONTRACT["component"] == "scores.contamination"
    assert CONTAMINATION_CONTRACT["standalone_offer_state"] == "not_sellable"
    required = CONTAMINATION_CONTRACT["delivery_contract_schema"]["required"]
    assert "subject_identity" in required
    assert "professional_assessment_required" in required
    assert not hasattr(mcp_server, "contamination_screening")


def test_contamination_release_gate_fails_on_provider_drift(tmp_path):
    root = Path(__file__).resolve().parents[1]
    provider = tmp_path / "provider"
    target = provider / "contracts"
    target.mkdir(parents=True)
    source = root / "contracts/contamination-screening-v1.json"
    (target / source.name).write_bytes(source.read_bytes())
    assert compare_contamination_contract(provider, root)["state"] == "ok"

    payload = json.loads((target / source.name).read_text(encoding="utf-8"))
    payload["delivery_contract_schema"]["required"].remove("subject_identity")
    (target / source.name).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="contracts differ"):
        compare_contamination_contract(provider, root)


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


def test_create_project_watch_matches_provider_contract():
    with patch.object(mcp_server, "_api_post", return_value={"data": {}}) as post:
        json.loads(mcp_server.create_project_watch(
            "project/one", "https://hooks.example.com/project", "watch-create-001",
        ))
    post.assert_called_once_with(
        _client_path("create_project_watch", "project%2Fone"),
        {"callback_url": "https://hooks.example.com/project",
         "idempotency_key": "watch-create-001"},
    )


def test_list_and_deactivate_project_watches_match_provider_contract():
    with patch.object(mcp_server, "_api_get", return_value={"data": []}) as get:
        json.loads(mcp_server.list_project_watches())
    get.assert_called_once_with(_client_path("list_project_watches"))

    with patch.object(mcp_server, "_api_delete", return_value={"data": {}}) as delete:
        json.loads(mcp_server.deactivate_project_watch("watch/one"))
    delete.assert_called_once_with(
        _client_path("deactivate_project_watch", watch_uid="watch%2Fone")
    )


def test_cursor_contract_distinguishes_checkpoint_from_page_continuation():
    semantics = PROJECT_CONTRACT["cursor_semantics"]
    assert semantics["durable_checkpoint"] == "meta.cursor"
    assert semantics["page_continuation"] == "meta.next_cursor"
