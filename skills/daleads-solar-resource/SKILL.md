---
name: daleads-solar-resource
description: Interpret regional, open-horizon solar resource for an Australian address through DA Leads API or MCP. Use for report benchmarks, quote sanity checks, portfolio ranking and upstream site screening. Do not use it as rooftop qualification, panel layout, shading, tariff, battery or financial design.
---

# DA Leads Solar Resource

Use the `solar_resource` MCP tool. Prefer a full street address. Use latitude
and longitude only when the user supplied the actual location.

If the response shape is unclear, call `property_context_sample` first. It is
keyless and shows the focused Solar Resource contract under `scores.solar`.

Before interpreting the result:

1. Confirm `resolved.address`, parcel details and match warnings. The solar
   resource is regional even when the query resolves to a parcel.
2. Read `spatial_resolution_m` per field. GHI/DNI/GTI are approximately 250 m,
   PVOUT and temperature approximately 1 km, and optimum tilt approximately
   4 km. Never give the whole response one blanket resolution.
3. Read `source_metadata.vintage`, `source`, `licence` and `attribution`. State
   an unavailable or unverified source instead of filling a value from memory.
4. Check `open_horizon` and every `roof_model` false flag. Do not infer roof
   planes, usable area, tree/building shade, obstructions or existing panels.
5. If `generation_scenario` is present, describe it as a gross open-horizon
   scenario using the caller's panel-area proxy. It is not measured usable roof
   or an installer yield commitment.
6. Do not calculate savings, payback, self-consumption or battery performance
   without user-supplied tariffs, load and system assumptions from an
   appropriate downstream model.
7. Preserve response caveats and attribution in any client-facing report.

Report in this order: resolved location, GHI/DNI/PVOUT and their individual
scales, source vintage, optional gross scenario, excluded rooftop/economic
inputs, then the next action. For a quote or design, obtain roof geometry,
shade, system configuration, tariffs and installer validation.
