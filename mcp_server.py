"""
DA Leads MCP Server
Exposes DA Leads API as MCP tools for AI agents (Claude, Cursor, etc.)

Usage:
    # Run directly
    python mcp_server.py

    # Claude Code config (~/.claude/mcp.json):
    {
      "mcpServers": {
        "da-leads": {
          "command": "python",
          "args": ["/path/to/da_leads/mcp_server.py"],
          "env": {
            "DALEADS_API_KEY": "dk_live_xxx"
          }
        }
      }
    }
"""

import os
import json
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP

# Configuration
API_KEY = os.environ.get("DALEADS_API_KEY", "")
API_URL = "https://daleads.com.au/api"

mcp = FastMCP(
    "DA Leads",
    instructions=(
        "Search and analyze Australian development applications (DAs) across 330+ "
        "councils, plus address-level Property Intelligence (planning, hazards, "
        "environment, transport and scored risk components), and canonical Project "
        "Intelligence for linked applications and rights-gated lifecycle change polling. Use search_das for "
        "filtered listing, nearby_das for spatial queries, sql_query for custom "
        "analytics, search_projects for real projects, property_intelligence "
        "for a full address profile, bushfire_screening for the focused "
        "commercial screening contract, "
        "property_core for score-free public-record context, suburb_signals "
        "for SAL development activity, sa2_population_forecast for code-keyed "
        "regional scenarios, or walkability_screening for the straight-line "
        "amenity contract. No API key yet? property_sample, "
        "property_core_sample, suburb_signals_sample, "
        "sa2_population_forecast_sample, property_walkability_sample, "
        "property_flood_sample and property_bushfire_sample work keylessly, and "
        "property_sandbox_addresses lists real addresses that never count "
        "toward a key's quota."
    ),
)

_client = None


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
        _client = httpx.Client(
            base_url=API_URL,
            headers=headers,
            timeout=30,
        )
    return _client


def _shape_response(resp: httpx.Response) -> dict:
    # Surface the API's structured 4xx guidance (quota resets_at, plan gates,
    # address-resolution hints) to the agent instead of a bare status exception.
    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except ValueError:
            detail = {"error": resp.text[:500]}
        if not isinstance(detail, dict):
            detail = {"error": detail}
        return {"http_status": resp.status_code, **detail}
    return resp.json()


def _api_get(path: str, params: dict | None = None) -> dict:
    return _shape_response(_get_client().get(path, params=params))


def _api_post(path: str, body: dict) -> dict:
    return _shape_response(_get_client().post(path, json=body))


def _project_path(project_uid: str, suffix: str = "") -> str:
    """Build a canonical-project path without allowing path injection."""
    project_uid = project_uid.strip()
    if not project_uid:
        raise ValueError("project_uid must not be empty")
    return f"/v1/projects/{quote(project_uid, safe='')}{suffix}"


@mcp.tool()
def search_das(
    state: str | None = None,
    council: str | None = None,
    category: str | None = None,
    suburb: str | None = None,
    postcode: str | None = None,
    since: str | None = None,
    status_group: str | None = None,
    is_residential: bool | None = None,
    page: int = 1,
    limit: int = 20,
) -> str:
    """Search development applications with filters.

    Args:
        state: Filter by state (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
        council: Filter by council name (e.g. "City of Melbourne")
        category: Filter by trade category (e.g. "Renovation / Extension", "Swimming Pool / Spa")
        suburb: Filter by suburb name
        postcode: Filter by exact postcode
        since: Only show DAs lodged on or after this ISO date (YYYY-MM-DD)
        status_group: Normalized status: pending, advertised, approved, rejected, or other
        is_residential: Filter residential (true) or commercial (false)
        page: Page number (default 1)
        limit: Results per page (max 100)
    """
    params = {"page": page, "per_page": min(limit, 100)}
    if state:
        params["state"] = state
    if council:
        params["council"] = council
    if category:
        params["category"] = category
    if suburb:
        params["suburb"] = suburb
    if postcode:
        params["postcode"] = postcode
    if since:
        params["since"] = since
    if status_group:
        params["status_group"] = status_group
    if is_residential is not None:
        params["is_residential"] = is_residential
    data = _api_get("/v1/das", params)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_da(da_id: int) -> str:
    """Get full details of a specific development application by ID.

    Args:
        da_id: The DA record ID
    """
    data = _api_get(f"/v1/das/{da_id}")
    return json.dumps(data, indent=2)


@mcp.tool()
def nearby_das(
    lat: float,
    lng: float,
    radius_km: float = 5.0,
    category: str | None = None,
    since: str | None = None,
    status_group: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> str:
    """Find development applications near a location.

    Args:
        lat: Latitude
        lng: Longitude
        radius_km: Search radius in km (default 5, max 50)
        category: Filter by trade category
        since: Only show DAs lodged on or after this ISO date (YYYY-MM-DD)
        status_group: Normalized status: pending, advertised, approved, rejected, or other
        page: Page number (default 1)
        limit: Results per page (max 100)
    """
    params = {
        "lat": lat,
        "lng": lng,
        "radius_km": radius_km,
        "page": page,
        "per_page": min(limit, 100),
    }
    if category:
        params["category"] = category
    if since:
        params["since"] = since
    if status_group:
        params["status_group"] = status_group
    data = _api_get("/v1/das/nearby", params)
    return json.dumps(data, indent=2)


@mcp.tool()
def search_projects(
    q: str | None = None,
    state: str | None = None,
    stage: str | None = None,
    project_type: str | None = None,
    changed_since: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> str:
    """Search canonical development projects and their current lifecycle state.

    Project Intelligence joins related applications and changes into one project.
    The API only returns rights-cleared evidence and fields. Availability is
    determined by the API key's server-side Project Intelligence entitlement.

    Args:
        q: Project name search, or an exact project_uid
        state: Australian state or territory code
        stage: Normalized lifecycle stage exposed by the Project API
        project_type: Normalized project type exposed by the Project API
        changed_since: Only projects changed since this ISO-8601 timestamp
        page: Page number (default 1)
        limit: Results per page (default 20, max 100)
    """
    params: dict = {"page": page, "per_page": min(limit, 100)}
    for key, value in (
        ("q", q),
        ("state", state),
        ("stage", stage),
        ("project_type", project_type),
        ("changed_since", changed_since),
    ):
        if value:
            params[key] = value
    return json.dumps(_api_get("/v1/projects", params), indent=2)


@mcp.tool()
def get_project(project_uid: str) -> str:
    """Get one rights-cleared canonical project and its linked applications.

    Args:
        project_uid: Stable canonical project identifier from search_projects
    """
    return json.dumps(_api_get(_project_path(project_uid)), indent=2)


@mcp.tool()
def get_project_changes(
    project_uid: str,
    since: str | None = None,
    cursor: int | None = None,
    limit: int = 50,
) -> str:
    """Read redacted, rights-cleared event notifications for one project.

    Persist ``meta.cursor`` after every response. ``meta.next_cursor`` is only
    the immediate continuation when the current response has another page.

    Args:
        project_uid: Stable canonical project identifier
        since: Optional ISO-8601 lower bound for the first request
        cursor: Non-negative continuation cursor returned by the API
        limit: Results per response (default 50, max 100)
    """
    params: dict = {"per_page": min(limit, 100)}
    if since:
        params["since"] = since
    if cursor:
        params["cursor"] = cursor
    return json.dumps(
        _api_get(_project_path(project_uid, "/changes"), params), indent=2
    )


@mcp.tool()
def nearby_projects(
    lat: float,
    lng: float,
    radius_km: float = 5.0,
    stage: str | None = None,
    project_type: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> str:
    """Find canonical development projects near a WGS84 point.

    Args:
        lat: Latitude in WGS84 decimal degrees
        lng: Longitude in WGS84 decimal degrees
        radius_km: Search radius in kilometres (default 5, max 200)
        stage: Optional normalized lifecycle stage
        project_type: Optional normalized project type
        page: Page number (default 1)
        limit: Results per page (default 20, max 100)
    """
    params: dict = {
        "lat": lat,
        "lng": lng,
        "radius_km": radius_km,
        "page": page,
        "per_page": min(limit, 100),
    }
    if stage:
        params["stage"] = stage
    if project_type:
        params["project_type"] = project_type
    return json.dumps(_api_get("/v1/projects/nearby", params), indent=2)


@mcp.tool()
def list_categories() -> str:
    """List all trade categories with record counts.

    Returns categories like: Renovation / Extension, Swimming Pool / Spa,
    Granny Flat / Secondary Dwelling, Demolition, etc.
    """
    data = _api_get("/v1/categories")
    return json.dumps(data, indent=2)


@mcp.tool()
def list_councils(limit: int = 50) -> str:
    """List councils with state, DA count, and last activity date.

    Args:
        limit: Max councils to return
    """
    data = _api_get("/v1/councils")
    if isinstance(data.get("data"), list):
        data["data"] = data["data"][:max(0, limit)]
        data.setdefault("meta", {})["returned"] = len(data["data"])
    return json.dumps(data, indent=2)


@mcp.tool()
def get_stats() -> str:
    """Get overall DA statistics: total records, by state, by category, date range."""
    data = _api_get("/v1/stats")
    return json.dumps(data, indent=2)


@mcp.tool()
def sql_query(query: str, params: list[str] | None = None) -> str:
    """Run a read-only SQL query against DA records. Pro plan only.

    Query the 'das' table with columns: id, address, address_suburb,
    address_postcode, council_name, council_reference, state, trade_category,
    sub_category, application_type, is_residential, lodgement_date, status,
    cost_of_development, decision_date, decision_status, on_notice_from,
    on_notice_to, number_of_dwellings, lot_count, land_use, building_type,
    storeys, latitude, longitude, data_source, date_fetched, documents,
    info_url. Description and summary are deliberately unavailable because
    council free text may contain personal contact details.

    Max 1000 rows. 10 second timeout. SELECT only.

    Args:
        query: SQL SELECT query using table name 'das'
        params: Optional parameters for %s placeholders
    """
    body = {"query": query}
    if params:
        body["params"] = params
    data = _api_post("/v1/sql", body)
    return json.dumps(data, indent=2)


@mcp.tool()
def property_intelligence(
    address: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    components: str | None = None,
) -> str:
    """Full property intelligence profile for one Australian address (or lat/lng point).

    Returns planning (zones, overlays, heritage), hazards (flood, bushfire),
    environment, transport, nearby DAs, points of interest and scored risk
    components for the address. Requires an API key on a Property Intelligence
    plan; each lookup counts toward the key's monthly quota, except the sandbox
    addresses from property_sandbox_addresses which are never metered.
    No key? Use property_sample for a complete keyless example first.

    Args:
        address: Free-text address, e.g. "34 Mary St Clayton VIC"
        lat: Latitude (alternative to address)
        lng: Longitude (alternative to address)
        components: Optional comma-separated subset to return, e.g.
            "scores.noise,hazards,das". Blocks: das, poi, planning, hazards,
            environment, transport, utilities, administrative, public_housing,
            scores.
    """
    if (lat is None) != (lng is None):
        return json.dumps({"error": "pass both lat and lng, or use address"})
    params: dict = {}
    if address:
        params["address"] = address
    if lat is not None and lng is not None:
        params["lat"] = lat
        params["lng"] = lng
    if components:
        params["components"] = components
    data = _api_get("/v1/property", params)
    return json.dumps(data, indent=2)


@mcp.tool()
def property_core(
    address: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> str:
    """Score-free Property Core context for one Australian property.

    Returns resolved address/parcel identity, DA context, POI, planning,
    hazards, environment, transport, utilities, administrative and public
    housing facts through a closed v1 contract. It never returns modelled
    scores or surfaces. The response carries coverage and a response-specific
    source/licence inventory. Requires a complete Property Core entitlement.

    Args:
        address: Free-text property address (recommended)
        lat: Latitude, supplied together with lng instead of address
        lng: Longitude, supplied together with lat instead of address
    """
    if (lat is None) != (lng is None):
        return json.dumps({"error": "pass both lat and lng, or use address"})
    if not address and lat is None:
        return json.dumps({"error": "pass an address or both lat and lng"})
    params: dict = {}
    if address:
        params["address"] = address
    if lat is not None and lng is not None:
        params["lat"] = lat
        params["lng"] = lng
    return json.dumps(_api_get("/v1/property/core", params), indent=2)


@mcp.tool()
def find_suburbs(
    query: str,
    state: str | None = None,
    limit: int = 20,
) -> str:
    """Resolve a suburb name to explicit ABS SAL codes.

    Args:
        query: Suburb-name prefix, e.g. "Carlton"
        state: Optional state code to narrow repeated names
        limit: Maximum matches, up to 100
    """
    params: dict = {"q": query, "per_page": min(max(limit, 1), 100)}
    if state:
        params["state"] = state
    return json.dumps(_api_get("/v1/suburbs", params), indent=2)


@mcp.tool()
def find_sa2_regions(
    query: str,
    state: str | None = None,
    limit: int = 20,
) -> str:
    """Resolve a regional name to explicit ASGS 2021 SA2 codes.

    Args:
        query: Exact or partial SA2 name
        state: Optional state code
        limit: Maximum matches, up to 50
    """
    params: dict = {"name": query, "limit": min(max(limit, 1), 50)}
    if state:
        params["state"] = state
    return json.dumps(_api_get("/v1/regions/sa2", params), indent=2)


@mcp.tool()
def suburb_signals(sal_code: str) -> str:
    """Development activity signals for one ABS SAL suburb.

    Returns Census context and privacy-slim aggregate DA-record activity. The
    result is not a canonical project count and never attaches an SA2 absolute
    population forecast to the SAL by name.

    Args:
        sal_code: ABS SAL code such as SAL20495 for Carlton VIC
    """
    return json.dumps(_api_get(f"/v1/suburb-signals/{sal_code}"), indent=2)


@mcp.tool()
def sa2_population_forecast(sa2_code: str) -> str:
    """Quality-gated population scenarios for one ASGS 2021 SA2.

    Returns code-keyed historical ERP, model metadata and rolling-origin error
    metrics. Established-region scenarios are Beta. High-growth and greenfield
    future values remain withheld while the artifact has no DA dwelling
    constraint; their history and validation evidence still return.

    Args:
        sa2_code: Nine-digit ASGS 2021 SA2 code
    """
    return json.dumps(
        _api_get(f"/v1/regions/sa2/{sa2_code}/forecast"), indent=2)


@mcp.tool()
def walkability_screening(
    address: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> str:
    """Amenity & Walkability Screening for one Australian property.

    Requests exactly ``scores.walkability``. The method uses straight-line
    metres to 24 amenity scenarios plus disclosed motorway, major-water and
    regional slope adjustments. It is not a walking route, isochrone or travel
    time. Read ``coverage`` before interpreting the score.

    Args:
        address: Free-text property address (recommended)
        lat: Latitude, supplied together with lng instead of address
        lng: Longitude, supplied together with lat instead of address
    """
    if (lat is None) != (lng is None):
        return json.dumps({"error": "pass both lat and lng, or use address"})
    if not address and lat is None:
        return json.dumps({"error": "pass an address or both lat and lng"})
    params: dict = {"components": "scores.walkability"}
    if address:
        params["address"] = address
    if lat is not None and lng is not None:
        params["lat"] = lat
        params["lng"] = lng
    return json.dumps(_api_get("/v1/property", params), indent=2)


@mcp.tool()
def bushfire_screening(
    address: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> str:
    """Focused property-level bushfire pre-screen for an Australian subject.

    Returns the official bushfire overlay status and any licensed hazard hits,
    plus modelled fuel, terrain, fire-history coverage, score and
    source metadata. This standard product does not include preliminary BAL and
    is not a certified assessment. Prefer an address: the response then states
    whether it resolved onto a cadastral parcel. Coordinates are accepted for
    portfolio triage but are labelled coordinate-only/on-parcel and must not be
    treated as a building location.

    Args:
        address: Free-text property address (recommended)
        lat: Latitude, supplied together with lng instead of address
        lng: Longitude, supplied together with lat instead of address
    """
    if (lat is None) != (lng is None):
        return json.dumps({"error": "pass both lat and lng, or use address"})
    if not address and lat is None:
        return json.dumps({"error": "pass an address or both lat and lng"})
    params: dict = {"components": "scores.bushfire,hazards.bushfire"}
    if address:
        params["address"] = address
    if lat is not None and lng is not None:
        params["lat"] = lat
        params["lng"] = lng
    data = _api_get("/v1/property", params)
    return json.dumps(data, indent=2)


@mcp.tool()
def property_sample() -> str:
    """Complete real Property Intelligence response, no API key required.

    Returns the canned production payload for 163 Grattan St, Carlton VIC
    (heritage terrace with DA activity) so you can inspect the full response
    shape before requesting a key.
    """
    data = _api_get("/v1/property/sample")
    return json.dumps(data, indent=2)


@mcp.tool()
def property_core_sample() -> str:
    """Real score-free Property Core v1 example, no API key required."""
    return json.dumps(_api_get("/v1/property/sample/core"), indent=2)


@mcp.tool()
def suburb_signals_sample() -> str:
    """Real Carlton SAL development-signals example, no API key required."""
    return json.dumps(_api_get("/v1/suburb-signals/sample"), indent=2)


@mcp.tool()
def sa2_population_forecast_sample() -> str:
    """Real Carlton SA2 forecast Beta example, no API key required."""
    return json.dumps(_api_get("/v1/regions/sa2/forecast/sample"), indent=2)


@mcp.tool()
def property_walkability_sample() -> str:
    """Real focused Walkability Screening v1 example, no API key required."""
    return json.dumps(
        _api_get("/v1/property/sample/walkability"), indent=2)


@mcp.tool()
def property_flood_sample() -> str:
    """Real flood score component example, no API key required.

    Returns the production scores.flood block for a study-covered Rocklea QLD
    point: official 1% AEP modelled depth, overlay status, terrain context
    and provenance.
    """
    data = _api_get("/v1/property/sample/flood")
    return json.dumps(data, indent=2)


@mcp.tool()
def property_bushfire_sample() -> str:
    """Real Bushfire Screening example, no API key required.

    Returns the focused production contract for a bushfire-fringe address in
    Katoomba NSW. It demonstrates subject identity, official/modelled status,
    input coverage and the explicit exclusion of preliminary BAL.
    """
    data = _api_get("/v1/property/sample/bushfire")
    return json.dumps(data, indent=2)


@mcp.tool()
def property_sandbox_addresses() -> str:
    """List sandbox addresses whose lookups never count toward your quota.

    Twelve real addresses covering all eight states; use them with
    property_intelligence to evaluate live responses for free on any
    Property Intelligence key.
    """
    data = _api_get("/v1/property/sandbox")
    return json.dumps(data, indent=2)


def main() -> None:
    """Run the DA Leads MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
