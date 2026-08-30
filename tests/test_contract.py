import ast
import json
import re
from pathlib import Path
from unittest.mock import patch

import mcp_server
import pytest
from scripts.check_provider_contract import compare as compare_provider_contract


PROJECT_CONTRACT = json.loads(
    (Path(__file__).parents[1] / "contracts" / "project-intelligence-v1.json")
    .read_text(encoding="utf-8")
)
FOCUSED_CONTRACT = json.loads(
    (Path(__file__).parents[1] / "contracts" / "focused-api-v1.json")
    .read_text(encoding="utf-8")
)


def _client_path(tool: str, project_uid: str | None = None) -> str:
    path = PROJECT_CONTRACT["tools"][tool]["path"].removeprefix("/api")
    if project_uid is not None:
        path = path.replace("{project_uid}", project_uid)
    return path


def _focused_path(tool: str) -> str:
    return FOCUSED_CONTRACT["tools"][tool]["path"].removeprefix("/api")


def _focused_components(tool: str) -> str:
    return ",".join(FOCUSED_CONTRACT["tools"][tool]["closed_components"])


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


def test_release_gate_fails_when_provider_contract_drifts(tmp_path):
    root = Path(__file__).resolve().parents[1]
    provider = tmp_path / "provider"
    provider_contracts = provider / "contracts"
    provider_contracts.mkdir(parents=True)
    source = json.loads((root / "contracts" / "focused-api-v1.json")
                        .read_text(encoding="utf-8"))
    (provider_contracts / "focused-api-v1.json").write_text(
        json.dumps(source), encoding="utf-8")
    assert compare_provider_contract(provider, root)["state"] == "ok"

    source["tools"]["solar_resource"]["lifecycle"] = "ready"
    (provider_contracts / "focused-api-v1.json").write_text(
        json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="provider/consumer contracts differ"):
        compare_provider_contract(provider, root)


def test_release_workflow_checks_out_and_compares_provider_contract():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8")
    assert "repository: resuly/da_leads" in workflow
    assert "ref: main" in workflow
    assert "token: ${{ secrets.DA_LEADS_READ_TOKEN }}" in workflow
    assert "python scripts/check_provider_contract.py" in workflow


def test_readme_tool_count_and_new_skills_are_complete():
    root = Path(__file__).resolve().parents[1]
    server_text = (root / "mcp_server.py").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    module = ast.parse(server_text)
    registered_tools = {
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "tool"
            for decorator in node.decorator_list
        )
    }
    assert registered_tools == {
        "search_das", "get_da", "nearby_das", "search_projects",
        "get_project", "get_project_changes", "nearby_projects",
        "list_categories", "list_councils", "get_stats", "sql_query",
        "property_intelligence", "property_core", "find_suburbs",
        "find_sa2_regions", "suburb_signals", "sa2_population_forecast",
        "walkability_screening", "noise_screening", "flood_screening",
        "bushfire_screening",
        "neighbourhood_context", "solar_resource", "property_sample",
        "property_core_sample", "suburb_signals_sample",
        "sa2_population_forecast_sample", "property_walkability_sample",
        "property_flood_sample", "property_bushfire_sample",
        "property_context_sample", "property_sandbox_addresses",
    }
    assert set(FOCUSED_CONTRACT["tools"]) <= registered_tools
    assert set(FOCUSED_CONTRACT["keyless_samples"]) <= registered_tools
    assert "It exposes 32 tools" in readme
    for name in (
        "daleads-bushfire-screening",
        "daleads-flood-screening",
        "daleads-neighbourhood-context",
        "daleads-noise-screening",
        "daleads-project-monitoring",
        "daleads-property-core",
        "daleads-solar-resource",
        "daleads-suburb-signals",
        "daleads-walkability-screening",
    ):
        skill_root = root / "skills" / name
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        interface = (skill_root / "agents" / "openai.yaml").read_text(
            encoding="utf-8")
        assert "TODO" not in skill
        assert f"${name}" in interface
        for adapter_root in (".agents", ".claude"):
            adapter = root / adapter_root / "skills" / name
            assert adapter.is_symlink()
            assert adapter.resolve() == skill_root.resolve()


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
    assert mcp_server.API_URL == FOCUSED_CONTRACT["api_base_url"]
    assert PROJECT_CONTRACT["authentication"] == {
        "environment_variable": "DALEADS_API_KEY",
        "header": "Authorization: Bearer <key>",
        "entitlement": "project_intelligence",
    }


def test_focused_lifecycle_and_standalone_exclusions_are_explicit():
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    lifecycle = {specification["lifecycle"]
                 for specification in FOCUSED_CONTRACT["tools"].values()}
    assert lifecycle <= set(FOCUSED_CONTRACT["lifecycle_vocabulary"])
    assert FOCUSED_CONTRACT["tools"]["walkability_screening"][
        "lifecycle"] == "pilot"
    assert FOCUSED_CONTRACT["tools"]["solar_resource"][
        "lifecycle"] == "developer_preview"
    assert "Pilot" in (mcp_server.walkability_screening.__doc__ or "")
    assert "Developer Preview" in (mcp_server.solar_resource.__doc__ or "")
    assert "Walkability Screening Pilot" in readme
    assert "Solar Resource Developer Preview" in readme
    assert "Pilot" in (root / "skills" / "daleads-walkability-screening" /
                       "SKILL.md").read_text(encoding="utf-8")
    assert "Developer Preview" in (
        root / "skills" / "daleads-solar-resource" / "SKILL.md"
    ).read_text(encoding="utf-8")

    exclusion = FOCUSED_CONTRACT["standalone_product_exclusions"][
        "contamination"]
    assert exclusion["offer_state"] == "not_sellable"
    assert exclusion["focused_tool"] == "not_published"
    assert "legacy_full_compatibility" in exclusion
    assert "contamination_screening" not in FOCUSED_CONTRACT["tools"]
    assert not (root / "skills" / "daleads-contamination-screening").exists()


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


def test_project_tools_reject_dot_path_segments_before_network():
    with patch.object(mcp_server, "_api_get") as get:
        for project_uid in (".", "..", " .. "):
            with pytest.raises(
                    ValueError, match="must not be a dot path segment"):
                mcp_server.get_project(project_uid)
            with pytest.raises(
                    ValueError, match="must not be a dot path segment"):
                mcp_server.get_project_changes(project_uid)
    get.assert_not_called()


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

    get.assert_called_once_with(_focused_path("bushfire_screening"), {
        "address": "15 Cliff Drive, Katoomba NSW 2780",
        "components": _focused_components("bushfire_screening"),
    })


def test_bushfire_screening_rejects_ambiguous_coordinate_input_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.bushfire_screening(lat=-33.7))
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "partial_coordinates_error"]
    get.assert_not_called()


def test_bushfire_screening_rejects_blank_and_mixed_subjects_locally():
    with patch.object(mcp_server, "_api_get") as get:
        blank = json.loads(mcp_server.bushfire_screening(address="   "))
        mixed = json.loads(mcp_server.bushfire_screening(
            address="1 Wrong Street, Sydney NSW", lat=-37.8, lng=144.96))
    assert blank["error"] == FOCUSED_CONTRACT["subject_contract"][
        "missing_subject_error"]
    assert mixed["error"] == FOCUSED_CONTRACT["subject_contract"][
        "mixed_subject_error"]
    get.assert_not_called()


def test_property_bushfire_sample_uses_keyless_focused_route():
    with patch.object(mcp_server, "_api_get", return_value={"meta": {"sample": True}}) as get:
        result = json.loads(mcp_server.property_bushfire_sample())
    get.assert_called_once_with(
        FOCUSED_CONTRACT["keyless_samples"]["property_bushfire_sample"]
        .removeprefix("/api"))
    assert result["meta"]["sample"] is True


def test_property_core_uses_dedicated_closed_endpoint():
    with patch.object(mcp_server, "_api_get", return_value={"meta": {}}) as get:
        json.loads(mcp_server.property_core(address="163 Grattan St Carlton VIC"))
    get.assert_called_once_with(
        _focused_path("property_core"),
        {"address": "163 Grattan St Carlton VIC"})


def test_property_intelligence_rejects_invalid_subjects_before_network():
    with patch.object(mcp_server, "_api_get") as get:
        missing = json.loads(mcp_server.property_intelligence())
        blank = json.loads(mcp_server.property_intelligence(address="   "))
        partial = json.loads(mcp_server.property_intelligence(lat=-37.8))
        mixed = json.loads(mcp_server.property_intelligence(
            address="1 Wrong Street, Sydney NSW", lat=-37.8, lng=144.96))
    assert missing["error"] == FOCUSED_CONTRACT["subject_contract"][
        "missing_subject_error"]
    assert blank == missing
    assert partial["error"] == FOCUSED_CONTRACT["subject_contract"][
        "partial_coordinates_error"]
    assert mixed["error"] == FOCUSED_CONTRACT["subject_contract"][
        "mixed_subject_error"]
    get.assert_not_called()


def test_property_core_rejects_partial_coordinates_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.property_core(lat=-37.8))
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "partial_coordinates_error"]
    get.assert_not_called()


def test_property_core_rejects_blank_and_mixed_subjects_locally():
    with patch.object(mcp_server, "_api_get") as get:
        blank = json.loads(mcp_server.property_core(address="   "))
        mixed = json.loads(mcp_server.property_core(
            address="1 Wrong Street, Sydney NSW", lat=-37.8, lng=144.96))
    assert blank["error"] == FOCUSED_CONTRACT["subject_contract"][
        "missing_subject_error"]
    assert mixed["error"] == FOCUSED_CONTRACT["subject_contract"][
        "mixed_subject_error"]
    get.assert_not_called()


def test_neighbourhood_context_uses_closed_component_set():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.neighbourhood_context(
            address="163 Grattan Street, Carlton VIC 3053"))

    get.assert_called_once_with(_focused_path("neighbourhood_context"), {
        "address": "163 Grattan Street, Carlton VIC 3053",
        "components": _focused_components("neighbourhood_context"),
    })


def test_neighbourhood_context_rejects_ambiguous_coordinates_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.neighbourhood_context(lat=-37.8))
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "partial_coordinates_error"]
    get.assert_not_called()


def test_neighbourhood_context_rejects_mixed_subject_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.neighbourhood_context(
            address="163 Grattan Street, Carlton VIC 3053",
            lat=-37.8,
            lng=144.96,
        ))
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "mixed_subject_error"]
    get.assert_not_called()


def test_suburb_signals_uses_sal_code_path():
    with patch.object(mcp_server, "_api_get", return_value={"data": {}}) as get:
        json.loads(mcp_server.suburb_signals("SAL20495"))
    get.assert_called_once_with(
        _focused_path("suburb_signals").replace("{sal_code}", "SAL20495"))


def test_geography_code_tools_reject_path_traversal_before_network():
    with patch.object(mcp_server, "_api_get") as get:
        bad_sal = json.loads(mcp_server.suburb_signals(
            "../property/sample"))
        bad_sa2 = json.loads(mcp_server.sa2_population_forecast(
            "../../../terms"))
    assert bad_sal["error"] == FOCUSED_CONTRACT["tools"][
        "suburb_signals"]["path_parameter"]["error"]
    assert bad_sa2["error"] == FOCUSED_CONTRACT["tools"][
        "sa2_population_forecast"]["path_parameter"]["error"]
    get.assert_not_called()


def test_suburb_and_sa2_resolvers_use_explicit_geography_catalogs():
    with patch.object(mcp_server, "_api_get", return_value={"data": []}) as get:
        json.loads(mcp_server.find_suburbs("Carlton", state="VIC", limit=5))
    get.assert_called_once_with(
        _focused_path("find_suburbs"),
        {"q": "Carlton", "per_page": 5, "state": "VIC"})

    with patch.object(mcp_server, "_api_get", return_value={"data": []}) as get:
        json.loads(mcp_server.find_sa2_regions("Carlton", state="VIC", limit=5))
    get.assert_called_once_with(
        _focused_path("find_sa2_regions"),
        {"name": "Carlton", "limit": 5, "state": "VIC"})


def test_sa2_forecast_uses_code_keyed_path():
    with patch.object(mcp_server, "_api_get", return_value={"data": {}}) as get:
        json.loads(mcp_server.sa2_population_forecast("206041117"))
    get.assert_called_once_with(
        _focused_path("sa2_population_forecast").replace(
            "{sa2_code}", "206041117"))


def test_walkability_screening_uses_closed_component():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.walkability_screening(
            address="163 Grattan St Carlton VIC"))
    get.assert_called_once_with(_focused_path("walkability_screening"), {
        "address": "163 Grattan St Carlton VIC",
        "components": _focused_components("walkability_screening"),
    })


def test_ready_noise_and_flood_tools_use_closed_component_sets():
    cases = (
        (mcp_server.noise_screening, "noise_screening"),
        (mcp_server.flood_screening, "flood_screening"),
    )
    for function, tool in cases:
        with patch.object(mcp_server, "_api_get", return_value={
                "scores": {}}) as get:
            json.loads(function(address="163 Grattan St Carlton VIC"))
        get.assert_called_once_with(_focused_path(tool), {
            "address": "163 Grattan St Carlton VIC",
            "components": _focused_components(tool),
        })


def test_all_closed_property_tools_reject_mixed_subjects_before_network():
    tool_names = (
        "noise_screening", "flood_screening", "walkability_screening",
        "bushfire_screening", "neighbourhood_context", "solar_resource",
    )
    for tool_name in tool_names:
        with patch.object(mcp_server, "_api_get") as get:
            result = json.loads(getattr(mcp_server, tool_name)(
                address="1 Wrong Street, Sydney NSW",
                lat=-37.8,
                lng=144.96,
            ))
        assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
            "mixed_subject_error"]
        get.assert_not_called()


def test_walkability_rejects_missing_subject_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.walkability_screening())
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "missing_subject_error"]
    get.assert_not_called()


def test_solar_resource_uses_closed_component_set():
    with patch.object(mcp_server, "_api_get", return_value={"scores": {}}) as get:
        json.loads(mcp_server.solar_resource(lat=-37.8, lng=144.96))

    get.assert_called_once_with(_focused_path("solar_resource"), {
        "lat": -37.8,
        "lng": 144.96,
        "components": _focused_components("solar_resource"),
    })


def test_solar_resource_requires_a_subject_before_network():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.solar_resource())
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "missing_subject_error"]
    get.assert_not_called()


def test_walkability_rejects_blank_and_mixed_subjects_locally():
    with patch.object(mcp_server, "_api_get") as get:
        blank = json.loads(mcp_server.walkability_screening(address="   "))
        mixed = json.loads(mcp_server.walkability_screening(
            address="1 Wrong Street, Sydney NSW", lat=-37.8, lng=144.96))
    assert blank["error"] == FOCUSED_CONTRACT["subject_contract"][
        "missing_subject_error"]
    assert mixed["error"] == FOCUSED_CONTRACT["subject_contract"][
        "mixed_subject_error"]
    get.assert_not_called()


def test_solar_resource_treats_blank_address_as_no_subject():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.solar_resource(address="   "))
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "missing_subject_error"]
    get.assert_not_called()


def test_solar_resource_rejects_mixed_subject_locally():
    with patch.object(mcp_server, "_api_get") as get:
        result = json.loads(mcp_server.solar_resource(
            address="1 Wrong Street, Sydney NSW",
            lat=-37.8,
            lng=144.96,
        ))
    assert result["error"] == FOCUSED_CONTRACT["subject_contract"][
        "mixed_subject_error"]
    get.assert_not_called()


def test_all_keyless_samples_use_focused_contract_routes():
    for sample_tool, contract_path in FOCUSED_CONTRACT[
            "keyless_samples"].items():
        function = getattr(mcp_server, sample_tool)
        with patch.object(mcp_server, "_api_get", return_value={"ok": True}) as get:
            assert json.loads(function()) == {"ok": True}
        get.assert_called_once_with(contract_path.removeprefix("/api"))


def test_property_context_sample_uses_keyless_focused_route():
    with patch.object(mcp_server, "_api_get", return_value={
        "meta": {"sample": True},
    }) as get:
        result = json.loads(mcp_server.property_context_sample())
    get.assert_called_once_with(
        FOCUSED_CONTRACT["keyless_samples"]["property_context_sample"]
        .removeprefix("/api"))
    assert result["meta"]["sample"] is True
