---
name: daleads-full-property-intelligence
description: Build a rights-aware Full Property Intelligence screen for one Australian property through DA Leads. Use for internal analysis and attributed static customer reports that need the approved factual property blocks plus Noise, Flood and Bushfire scores. Do not treat it as a wildcard entitlement, a professional assessment, an embedded data licence or access to Preview products.
---

# DA Leads Full Property Intelligence

Use `full_property_intelligence`. Prefer a full street address; use latitude and
longitude only when the user supplied the actual subject point. The tool sends
the public Full Self-Serve closed component set and does not accept a caller-
selected component list.

`property_sample` is the available keyless schema preview. It is shared across
provider contracts and can display fields outside public Full Self-Serve. Use it
to learn the envelope only. Never cite a field in that generic sample as proof
that Full includes the field or that the current key is entitled to it.

The Full Self-Serve contract contains:

- base factual blocks: `das`, `poi`, `planning`, `transport`, `utilities`,
  `administrative`, and `public_housing`;
- explicit hazard and environment leaves pinned in
  `contracts/focused-api-v1.json`, including rights-gated factual register
  context where the source and field policy permits it;
- score leaves: `scores.noise`, `scores.aircraft_noise`, `scores.flood`, and
  `scores.bushfire`;
- separate key capabilities for Property Core and Suburb Intelligence. These
  capabilities do not add fields to a Full property response.

It does not request top-level `hazards`, `environment` or `scores`. Those broad
names would automatically inherit later, unreviewed fields.
Factual contamination/register context is not `scores.contamination` and does
not publish the standalone Contamination product. Solar Resource, the standalone
Contamination score/product, Neighbourhood Heat, Landscape Openness, the
Walkability Pilot are outside Full. The included Bushfire component can carry a
preliminary indicative BAL band with range and confidence plus its mandatory
disclaimer; it is not a certified BAL assessment and cannot be used for building
approval. A user may hold one of the excluded products under a separate
entitlement, but that must be established
independently and must not be described as Full.

Before interpreting a response:

1. Confirm the resolved address, parcel identity and match warnings. Coordinate
   context is not proof of a particular building or cadastral subject.
2. Read response-specific coverage, caveats, attribution and licence metadata.
   Missing or unavailable evidence is not a negative finding.
3. Keep factual government or public-record evidence separate from modelled
   score outputs. Preserve the focused Noise, Flood and Bushfire limitations.
4. Do not infer a Preview capability from an extra field in a generic sample,
   an old manual key or cached output. The live server-side entitlement is the
   authority for the current key.
5. For a static customer report, retain attribution, coverage and caveats. Do
   not provide raw onward access, interactive embedding, white labelling,
   resale, special geometry or an SLA under the Self-Serve licence.

Report in this order: resolved subject, material factual findings, Noise/Flood/
Bushfire screening evidence, coverage gaps, attribution and caveats, then next
actions. Planning, design, insurance, acoustic, flood and bushfire decisions
that require professional evidence must be referred to the relevant authority
or qualified practitioner.
