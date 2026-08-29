---
name: daleads-neighbourhood-context
description: Interpret Neighbourhood Heat and Landscape Openness for an Australian address through DA Leads API or MCP. Use for property reports, buyer shortlists, portfolio triage and urban-context comparisons. Do not use it as parcel temperature, live weather, indoor-comfort or energy modelling, or as line-of-sight from a window or storey.
---

# DA Leads Neighbourhood Context

Use the `neighbourhood_context` MCP tool. Prefer a full street address. Use
latitude and longitude only when the user supplied the actual property point;
never substitute a suburb or locality centroid.

If the contract is unclear, call `property_context_sample` first. It is keyless
and shows Neighbourhood Heat and Landscape Openness beside Solar Resource.

Before interpreting the result:

1. Confirm `resolved.address`, parcel details and match warnings. A coordinate
   result is location context, not proof of a particular building.
2. For `scores.heat_island`, read `temperature_resolution_m` and
   `land_cover_resolution_m` separately. Approximately 1 km temperature plus
   10 m land cover is not 10 m temperature.
3. Check `temperature_vintage`, `lst_source`, `lst_offset_m` and
   `lst_pixels_averaged`. An unverified vintage or borrowed pixel must be stated.
   If the UHI comparison is absent, do not reconstruct one.
4. Treat `scores.view_quality` as the compatible v1 key for
   `product=landscape_openness`. Read `missing_factors`, `partial_factors`,
   `factor_weight_completeness` and `degraded` before ranking locations.
5. Check `line_of_sight.modelled`. Do not infer a room, floor, orientation,
   building occlusion or visible target when it is false.
6. Preserve response caveats and attribution in any client-facing report.

Report in this order: resolved subject, Neighbourhood Heat level and scale,
day/night and borrowed-pixel/vintage evidence, Landscape Openness factors and
completeness, then limitations and next action. A site visit, council heat map,
floor-specific 3D study or professional assessment is the next action when the
decision needs finer spatial or sightline evidence.
