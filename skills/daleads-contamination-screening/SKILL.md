---
name: daleads-contamination-screening
description: Screen an Australian property for contamination evidence through the DA Leads API or MCP. Use for acquisition, development, portfolio and Phase 1 triage where official-register status, historical use, groundwater, landfill and industrial context must remain distinct. Do not use it as a raw register feed, clean-site certificate or environmental assessment.
---

# DA Leads Contamination Screening

Use the `contamination_screening` MCP tool. Prefer a full street address. Use
latitude and longitude only when the user supplied the actual property point;
never substitute a suburb or locality centroid.

If the response shape is unclear, call `property_contamination_sample` first.
It is keyless and shows the screening-only `scores.contamination` contract.
For field meanings and error/metering behavior, use the official focused guide
at `https://daleads.com.au/api/v1/property/docs/contamination`.

Before interpreting the result:

1. Confirm `resolved.address`, parcel details and
   `delivery_contract.subject_identity`. Do not present coordinate-only output
   as a confirmed parcel result.
2. Read `coverage.official_register`. `checked_with_on_site_finding`,
   `checked_clear`, `not_integrated`, `error` and `unavailable` are different
   conclusions. Read `nearby_register_evidence` separately.
3. Read `score_status` before the numeric score. A null score with
   `unavailable_incomplete_coverage` must not be ranked or converted to zero;
   it means the screen withheld an optimistic number because required coverage
   was missing.
4. Keep on-site findings separate from nearby evidence. Historical business,
   licensed activity, storage notifications and industrial proximity are
   context unless the response explicitly attributes them to the subject site.
5. Treat an error or unavailable source as incomplete, never clean. A high score
   or checked-clear register is not evidence that the soil is uncontaminated.
6. Preserve caveats and response-level attribution in reports or quoted output.

Report in this order: resolved subject, official-register status, on-site
evidence, nearby/context evidence, coverage gaps, then the next action. Where
contamination could affect a purchase, development or lending decision, the
next action is a site-history review and, where warranted, a suitably qualified
professional's Phase 1 environmental site assessment.
