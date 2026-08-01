import json
from unittest.mock import patch

import mcp_server


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
