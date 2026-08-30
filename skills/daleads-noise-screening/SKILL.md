---
name: daleads-noise-screening
description: Screen road, rail and aircraft noise at an Australian property through DA Leads. Use for acquisition triage, portfolio comparison and explaining modelled noise evidence. Do not use it as a site measurement, LA90 result, acoustic compliance assessment or professional design advice.
---

# DA Leads Noise Screening

Use `noise_screening`. Prefer a full street address; use coordinates only when
the user supplied the actual subject point. Call `property_sample` first when
the response shape is unfamiliar and inspect only its Noise fields. That sample
is a generic schema preview; its other fields are not part of the Noise product
and do not prove any entitlement.

Before interpreting the result:

1. Confirm the resolved address, parcel identity and match warnings. A
   coordinate result is location context, not proof of a particular building.
2. Keep the numeric screening score separate from `lden_db`, day/night levels
   and facade-sector estimates. They are model outputs, not measurements at the
   requested property.
3. Read `confidence_range_db` and `measured_validation`, including its state,
   instrument count, bias, MAE and date. Do not generalise one state's evidence
   to another state or present the interval as regulatory uncertainty.
4. Treat dominant road/rail records as model inputs and source context. Do not
   infer an exact facade exposure, indoor level or statutory limit.
5. For `scores.aircraft_noise`, distinguish an assessed overlay result from
   `not_assessed` or unavailable coverage. Absence of a mapped overlay does not
   prove absence of aircraft noise.
6. Preserve response attribution and licence obligations wherever source names,
   coordinates or evidence are surfaced.

Report in this order: resolved subject, score and modelled dB evidence, dominant
sources and facade pattern, aircraft assessment, validation/confidence limits,
coverage gaps, then the next action. Decisions needing compliance or design
evidence require site measurements and a qualified acoustic consultant.
