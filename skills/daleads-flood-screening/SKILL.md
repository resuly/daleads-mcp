---
name: daleads-flood-screening
description: Screen an Australian property for flood context through DA Leads. Use for acquisition triage, portfolio review and explaining national model evidence beside official mapped or study evidence. Do not use it as a hydraulic model, flood certificate, insurance decision or professional flood assessment.
---

# DA Leads Flood Screening

Use `flood_screening`. Prefer a full street address; use coordinates only when
the user supplied the actual property point. Call `property_flood_sample` first
when the contract is unfamiliar.

Before interpreting the result:

1. Confirm the resolved address, parcel identity and match warnings. Do not
   substitute a suburb centroid or treat coordinate context as parcel proof.
2. Keep the modelled `scores.flood` result separate from official evidence in
   `hazards.flood`, `official_layer` and any named study. One must not speak for
   the other when official coverage is incomplete or unavailable.
3. Read `overlay_basis`, coverage status and source vintage. A clear result from
   a partial library is not national proof that no official mapping applies.
4. Treat `flood_depth` as study-specific evidence only where its source, AEP,
   units and coverage are present. Missing depth means the current study library
   does not cover the point; it is not zero depth or zero risk.
5. Keep HAND, terrain, water proximity and design rainfall as screening inputs.
   Do not convert an official H1-H6 hazard class into metres.
6. Preserve every applicable attribution and response caveat in reports.

Report in this order: resolved subject, official mapped/study evidence, modelled
score and label, depth where genuinely covered, terrain/water/rainfall context,
coverage gaps, then the next action. Material property, design or insurance
decisions require the relevant authority records and a qualified flood expert.
