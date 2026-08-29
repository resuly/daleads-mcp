---
name: daleads-bushfire-screening
description: Screen an Australian property for bushfire context through the DA Leads API or MCP. Use for property due diligence, development/design triage, portfolio screening, and explanations of official bushfire mapping versus modelled fuel, terrain and fire history. Do not use it to produce a certified BAL, building approval evidence, construction advice or an insurance decision.
---

# DA Leads Bushfire Screening

Use the `bushfire_screening` MCP tool. Prefer a full street address. Use latitude
and longitude only when the user has supplied a property/building point; never
substitute a suburb or locality centroid.

If the schema or product boundary is unclear, call `property_bushfire_sample`
first. It is keyless and shows the standard commercial response. Preliminary BAL
is intentionally absent from this product.

Before interpreting risk:

1. Check `resolved.address`, `resolved.parcel`, match warnings and
   `scores.bushfire.delivery_contract.subject_identity`. If the match is doubtful,
   explain the mismatch and do not treat the result as the requested property.
2. Keep official mapping separate from the model. `in_zone`, `outside` and
   `unavailable` are different states. Modelled fuel or score must not speak for
   government mapping when the official lookup is unavailable.
3. Read every entry in `scores.bushfire.coverage`. `unavailable` and
   `not_integrated` are data gaps, not evidence that a hazard is absent.
4. Treat the numeric score as a screening index where a higher number means
   lower modelled risk. Do not convert it into a BAL or construction requirement.
5. Preserve the response caveat and attribution when the result is quoted or
   inserted into a report.

Report the result in this order: resolved subject, official overlay status,
modelled score and label, fuel/terrain/fire-history evidence, coverage gaps,
then the next action. For building, planning or permit decisions, the next action
is a site-specific assessment by a suitably qualified bushfire practitioner.
