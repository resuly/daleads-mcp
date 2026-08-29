---
name: daleads-walkability-screening
description: Screen amenity proximity and disclosed walking barriers for an Australian property through DA Leads. Use for site selection, neighbourhood comparison and portfolio triage. Do not use it as a walking-route, isochrone, accessibility-compliance or travel-time result.
---

# DA Leads Amenity & Walkability Screening

Use `walkability_screening`. Prefer a full address; use coordinates only for a
user-supplied subject point. Call `property_walkability_sample` first when the
contract is unfamiliar.

Before interpreting the score:

1. Confirm the resolved subject and `delivery_contract.subject_identity`.
2. Read `screening_contract.distance_basis`; v1 is
   `straight_line_metres` and `route_network_time=not_computed`.
3. Check every entry in `coverage`. A road check can degrade conservatively;
   unavailable water or slope checks can leave the score unadjusted. State the
   consequence rather than calling the address clear.
4. Use `category_scores[*].distance_m`, `nearest`, `options`, `barrier` and
   `water_barrier` as evidence. Do not convert straight-line distance into
   minutes or claim a crossing, entrance or footpath exists.
5. Treat category `count` and `poi_count` as legacy source-row counts, not
   unique businesses. Use `unique_facility_count` and the named options for
   human interpretation. The v1 rail snapshot can overlap rail/tram categories;
   read `screening_contract.transit_mode_boundary`.
6. Preserve `meta.amenity_sources` attribution whenever names or coordinates
   are quoted or rendered.

Lead with `screening_label` and the numeric score, then explain the closest
essential amenities, barrier and slope adjustments, coverage gaps and the next
verification step. For a real trip decision, verify the route in an appropriate
current routing or accessibility service.
