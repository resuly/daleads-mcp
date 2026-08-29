---
name: daleads-suburb-signals
description: Analyse DA Leads suburb development activity and regional population scenarios while keeping ABS SAL and SA2 geographies separate. Use for suburb research, planning activity, portfolio comparisons or population scenario questions. Do not treat raw DA counts as projects or SA2 forecasts as suburb headcounts.
---

# DA Leads Suburb Signals

Choose the geography before calling a data tool:

- For a named suburb's Census context and development activity, resolve the
  exact SAL with `find_suburbs`, then call `suburb_signals` using its `SAL...`
  code.
- For population scenarios, resolve the ASGS 2021 region with
  `find_sa2_regions`, then call `sa2_population_forecast` using its nine-digit
  SA2 code.

Never infer a SAL or SA2 code from the name, and never copy an SA2 absolute
population into a SAL result. Names repeat and the two boundaries do not nest
one-to-one.

For SAL signals:

1. State that `record_unit=development_application_record` and
   `project_deduplication=not_applied`; several applications can belong to one
   development.
2. Read status and dwelling coverage before comparing activity. Sparse council
   publication can make a low count incomplete.
3. Keep the 2021 Census denominator visible when quoting applications per 1,000
   residents.

For SA2 forecasts:

1. Read `forecast.status`, `model.suburb_type`, `housing_constraint` and the
   matching rolling-origin validation metrics.
2. A `withheld_quality_gate` forecast is not zero growth. Report the history and
   why future values are withheld.
3. Treat Beta scenarios as regional exploration, not valuation, statutory
   evidence or guaranteed dwelling demand.

Use the keyless `suburb_signals_sample` and
`sa2_population_forecast_sample` when demonstrating either contract.
