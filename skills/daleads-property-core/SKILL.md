---
name: daleads-property-core
description: Retrieve score-free Australian property context from DA Leads for due diligence, site research, planning and public-record evidence. Use when address/parcel identity, DAs, POI, planning, hazards, environment, transport, utilities or administrative facts are needed without modelled scores. Do not use it as professional, statutory or title advice.
---

# DA Leads Property Core

Use `property_core`. Prefer a full street address; use coordinates only when the
user supplied the actual subject point. Call `property_core_sample` first when
the response shape or licence boundary is unclear.

Before interpreting the response:

1. Confirm `resolved.address`, parcel identifiers, match warnings and
   `meta.product_contract.subject_identity`. A coordinate result is not proof of
   a street address or building identity.
2. Check top-level `completeness`, `degraded_components` and every relevant
   `meta.coverage_status`. `not_assessed` and `unavailable` are not clear results.
3. Preserve on-parcel versus nearby distinctions, especially for development
   applications and environmental/hazard evidence.
4. Read `meta.attribution.sources`. Retain stated credits; entries marked
   `schedule_required` need the licence schedule before onward use.
5. Treat geometry as conditional. An omitted shape can reflect product/source
   rights and does not negate the accompanying identifier or finding.

The Core contract intentionally excludes `scores`, `surfaces` and unknown future
blocks. Do not reconstruct a score from the factual layers or call a missing
field a zero.

Report in this order: resolved subject, parcel identity, relevant on-site facts,
nearby context, coverage/degradation, source obligations, then the appropriate
specialist or official verification step.
