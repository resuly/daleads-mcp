# DA Leads MCP

<!-- mcp-name: io.github.resuly/daleads-mcp -->

DA Leads MCP lets Claude, Cursor and other MCP clients query Australian development applications and address-level property intelligence through the [DA Leads API](https://daleads.com.au/api/).

It exposes DA search, canonical project search and monitoring, nearby
applications/projects, council and category lookups, read-only SQL analysis,
property intelligence, focused Bushfire and Walkability screening, score-free
Property Core, Suburb Signals, SA2 scenarios, Neighbourhood Context and Solar
Resource, keyless samples and sandbox addresses.

## Install

Run without installing globally:

```bash
uvx daleads-mcp
```

Or install with pipx:

```bash
pipx install daleads-mcp
daleads-mcp
```

## Configuration

Paid tools use a DA Leads API key. The property sample tools work without a key.

```json
{
  "mcpServers": {
    "da-leads": {
      "command": "uvx",
      "args": ["daleads-mcp"],
      "env": {
        "DALEADS_API_KEY": "dk_live_xxx"
      }
    }
  }
}
```

`DALEADS_API_KEY` is the only environment variable read by this package. Treat
it as a secret. It is sent only to the fixed official HTTPS API endpoint at
`https://daleads.com.au/api`.

## Tools

### Development applications

**`search_das`** — Search Australian development applications with filters, newest
first. Parameters: `state` (NSW, VIC, QLD, SA, WA, TAS, NT, ACT), `council` (full
council name, e.g. `City of Melbourne`), `category` (trade category, e.g.
`Renovation / Extension`), `suburb`, `postcode`, `since` (ISO date `YYYY-MM-DD`,
lodged on or after), `status_group` (`pending`, `advertised`, `approved`,
`rejected`, `other`), `is_residential` (bool), `page` (default 1), `limit`
(per page, default 20, max 100). Returns `{data: [DA record, ...], meta:
{total, page, per_page, pages}}`. Each record carries id, address, suburb,
postcode, council, state, trade_category, lodgement_date, status,
status_group, latitude, longitude, info_url and document links; paid plans add
description, summary, sub_category, cost_of_development, decision fields,
number_of_dwellings, building_type, storeys and the full documents list.
Applicant names are never returned on any plan.

**`get_da`** — Retrieve one development application in full. Parameters: `da_id`
(integer record id, as returned by `search_das` or `nearby_das`). Returns
`{data: DA record}` with the same field set as above.

**`nearby_das`** — Find development applications within a radius of a point,
nearest first. Parameters: `lat`, `lng` (WGS84 decimal degrees), `radius_km`
(default 5, max 50), `category`, `since`, `status_group`, `page`, `limit`
(max 100). Returns the same `{data, meta}` shape as `search_das`, with an extra
`distance_km` on each record.

**`list_categories`** — List every trade category with its record count, for
discovering valid `category` values. No parameters. Returns `{data: [{name,
slug, is_residential, record_count}, ...], meta: {total}}` — categories such as
Renovation / Extension, Swimming Pool / Spa, Granny Flat / Secondary Dwelling
and Demolition.

**`list_councils`** — List councils with coverage and freshness, for discovering
valid `council` values. Parameters: `limit` (max councils to return, default 50).
Returns `{data: [{council, state, record_count, last_lodgement, last_fetched},
...], meta}`.

**`get_stats`** — Coverage summary for the whole dataset. No parameters. Returns
`{data: {total_records, records_last_7_days, date_range: {earliest, latest},
by_state: [...], by_category: [...]}}`.

**`sql_query`** — Run a read-only SQL query for custom aggregation the filter
tools cannot express. **Pro plan only.** Parameters: `query` (a single SELECT
against the `das` table), `params` (optional list of values for `%s`
placeholders). Available columns: id, address, address_suburb, address_postcode,
council_name, council_reference, state, trade_category, sub_category,
application_type, is_residential, lodgement_date, status, cost_of_development,
decision_date, decision_status, on_notice_from, on_notice_to,
number_of_dwellings, lot_count, land_use, building_type, storeys, latitude,
longitude, data_source, date_fetched, documents, info_url. Description and
summary are deliberately unavailable here because council free text can contain
personal contact details. SELECT only, capped at 1000 rows with a 10 second
timeout. Returns `{columns: [...], rows: [[...], ...], row_count, truncated}`.

### Project intelligence

These tools use the same `DALEADS_API_KEY` as every other paid tool. The API
enforces the key's `project_intelligence` entitlement and rights-cleared field
projection; the MCP package does not maintain a second capability list.

**`search_projects`** — Search canonical projects rather than independent DA
records. Parameters: `q`, `state`, normalized `stage`, normalized `project_type`,
`changed_since` (ISO-8601 timestamp), `page`, and `limit` (max 100). The client
sends the provider's canonical `per_page` parameter. Returns a `{data, meta}`
envelope with `contract_version: project-intelligence-v1`.

**`get_project`** — Retrieve one canonical project. Parameter: `project_uid`
(the stable identifier returned by `search_projects`). The current v1 response
contains identity, normalized status, location, linked applications and project
relations. Rights-gated fields are omitted rather than represented as coverage
or conflict metadata.

**`get_project_changes`** — Retrieve durable changes for one project. Parameters:
`project_uid`, optional initial `since`, continuation `cursor`, and `limit`
(max 100). Persist `meta.cursor` after every response. Use a non-null
`meta.next_cursor` only to fetch the next page immediately. Change values remain
redacted until field-level delivery provenance is available.

**`nearby_projects`** — Search canonical projects around a WGS84 point. Parameters:
`lat`, `lng`, `radius_km`, optional `stage` and `project_type`, `page`, and `limit`.

The repository includes `skills/daleads-project-monitoring` for cursor-based
polling. It is installed from the GitHub repository, not bundled inside the
PyPI wheel.

### Property intelligence

**`property_intelligence`** — Full address-level property profile for one
Australian address or coordinate. Parameters: `address` (free text, e.g.
`34 Mary St Clayton VIC`) or `lat` + `lng` together, and optional `components`
(comma-separated subset to return, e.g. `scores.noise,hazards` — available
blocks: das, poi, planning, hazards, environment, transport, utilities,
administrative, public_housing, scores). Returns the resolved address plus
planning (zones, overlays, heritage), hazards (flood, bushfire), environment,
transport, utilities, administrative boundaries, public housing, nearby
development applications, points of interest, scored risk components, and a
`meta` block carrying per-component status and provenance. Requires a key on a
Property Intelligence plan; each lookup counts against the monthly quota unless
the address comes from `property_sandbox_addresses`.

**`property_core`** — Closed score-free property context. Parameters: `address`
(recommended) or `lat` + `lng`. Returns resolved address/parcel identity,
development applications, POI, planning, hazards, environment, transport,
utilities, administrative and public-housing facts, plus response-specific
coverage and source obligations. It never returns scores, surfaces or unknown
future blocks. The key must include the complete explicit Core component set.

### Suburb and regional intelligence

**`find_suburbs`** — Resolve a suburb-name prefix to ABS SAL codes before a
signals call. Parameters: `query`, optional `state`, `limit` (max 100). Returns
the existing licensed Census rows with `sal_code`; repeated names remain
separate rather than being guessed.

**`suburb_signals`** — Census context and privacy-slim development activity for
one SAL code. Parameter: `sal_code`. Returns current/prior 12-month DA-record
counts, momentum, status and dwelling publication coverage, category mix and a
machine contract stating that project deduplication has not been applied. It
never attaches an SA2 absolute population forecast to the SAL.

**`find_sa2_regions`** — Resolve an exact or partial region name to ASGS 2021
SA2 codes. Parameters: `query`, optional `state`, `limit` (max 50). Use the
returned code with `sa2_population_forecast`; never infer it from a suburb name.

**`sa2_population_forecast`** — Code-keyed regional population scenario Beta.
Parameter: nine-digit `sa2_code`. Returns history, model/vintage, housing-
constraint status and matching 1/3/5-year rolling-origin errors. Established
SA2s include low/medium/high scenarios. High-growth and greenfield future values
are withheld while the artifact has no DA dwelling constraint; withheld is not
zero growth.

**`bushfire_screening`** — Focused commercial Bushfire Screening lookup.
Parameters: `address` (recommended) or `lat` + `lng` together. It always requests
exactly `scores.bushfire,hazards.bushfire`, returning subject identity, official
overlay status, licensed hazard hits, modelled vegetation fuel, terrain, available
fire history, coverage and caveats. The standard product does not include
preliminary BAL and is not a certified assessment. Coordinate-only lookups are
labelled as such and must not be treated as a building location.

**`walkability_screening`** — Focused Amenity & Walkability Screening lookup.
Parameters: `address` (recommended) or `lat` + `lng`. It requests exactly
`scores.walkability`: straight-line metres to 24 amenity scenarios plus
disclosed motorway, major-water and regional slope adjustments. It is not a
walking route, isochrone or travel-time result. Read every `coverage` state and
preserve `meta.amenity_sources` attribution when names or coordinates surface.

**`neighbourhood_context`** — Focused Neighbourhood Context Beta lookup.
Parameters: `address` (recommended) or `lat` + `lng` together. It requests
exactly `scores.heat_island,scores.view_quality`. Neighbourhood Heat keeps its
approximately 1 km temperature separate from 10 m land-cover context and
reports source vintage and borrowed-pixel status. The legacy `view_quality` key
returns the public Landscape Openness product, including six factors,
missing/partial coverage and explicit line-of-sight exclusions. It is not
parcel temperature, live weather, indoor comfort, building energy use or a
guaranteed view.

**`solar_resource`** — Focused Solar Resource Developer Preview lookup.
Parameters: `address` (recommended) or `lat` + `lng` together. It requests
exactly `scores.solar` and returns regional open-horizon GHI/DNI/GTI, PVOUT,
optimum tilt, per-field resolution, vintage, licence and attribution. It does
not identify roof planes, usable area, building or tree shading, obstructions,
tariffs, self-consumption or batteries and must not be used as rooftop design.
**`property_sample`** — Inspect the complete Property Intelligence response shape
before you have a key. **No API key required.** No parameters. Returns the real
production payload for 163 Grattan St, Carlton VIC (a heritage terrace with DA
activity), with every block present.

**`property_core_sample`** — Inspect the closed score-free Property Core v1
contract. **No API key required.** Returns a real Carlton response containing
only the explicit Core fact blocks, coverage and source inventory.

**`suburb_signals_sample`** — Inspect a real Carlton SAL development-signals
Beta response. **No API key required.**

**`sa2_population_forecast_sample`** — Inspect the Carlton SA2 forecast Beta,
including matching rolling-origin error evidence. **No API key required.**

**`property_walkability_sample`** — Inspect the focused Amenity & Walkability
Screening contract for Carlton. **No API key required.** Distances are explicitly
straight-line and no route time is supplied.

**`property_flood_sample`** — Inspect one scored hazard component in detail.
**No API key required.** No parameters. Returns the production `scores.flood`
block for a study-covered point in Rocklea QLD: official 1% AEP modelled depth,
overlay status, terrain context, coverage notes and provenance.

**`property_bushfire_sample`** — Inspect the standard Bushfire Screening contract.
**No API key required.** No parameters. Returns a real Katoomba NSW focused
sample with resolved subject identity, official/modelled evidence, coverage,
attribution and an explicit marker that preliminary BAL is withheld.

**`property_context_sample`** — Inspect the coordinated Neighbourhood Context
Beta and Solar Resource Developer Preview contract. **No API key required.** No
parameters. Returns a real production-shaped Carlton response containing only
Neighbourhood Heat, Landscape Openness and Solar Resource, with their legacy v1
keys, measurement levels, sources, caveats and not-modelled boundaries.
**`property_sandbox_addresses`** — List the addresses you can evaluate for free.
**No API key required.** No parameters. Returns `{sandbox_addresses: [{address,
label}, ...], note}` — 12 real addresses spanning all eight states, chosen for
distinct hazard and planning profiles. Lookups of these addresses through
`property_intelligence` never count toward a key's monthly quota.

## Data boundary

The adapter code and the data returned by DA Leads have separate licence
boundaries. Installing this package does not grant a right to redistribute the
API data. Starter and Scale usage is for internal analysis; customer-facing
embedding, onward access, resale, or redistribution requires an Enterprise
licence. See the [DA Leads Terms](https://daleads.com.au/terms),
[Privacy Policy](https://daleads.com.au/privacy), and
[Data Attributions](https://daleads.com.au/attributions).

The server reuses the DA Leads API authentication, plan limits and privacy
controls. Public API and MCP responses do not expose applicant names.

Copyright 2026 Limon Tech. All rights reserved.
