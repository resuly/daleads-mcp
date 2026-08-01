# DA Leads MCP

<!-- mcp-name: io.github.resuly/daleads-mcp -->

DA Leads MCP lets Claude, Cursor and other MCP clients query Australian development applications and address-level property intelligence through the [DA Leads API](https://daleads.com.au/api/).

It exposes 11 tools for DA search, nearby applications, council and category lookups, read-only SQL analysis, property intelligence, keyless samples and sandbox addresses.

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

- `search_das`
- `get_da`
- `nearby_das`
- `list_categories`
- `list_councils`
- `get_stats`
- `sql_query`
- `property_intelligence`
- `property_sample`
- `property_flood_sample`
- `property_sandbox_addresses`

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
