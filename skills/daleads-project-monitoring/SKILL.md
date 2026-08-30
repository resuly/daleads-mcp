---
name: daleads-project-monitoring
description: Find, explain and monitor canonical Australian development projects with DA Leads Project Intelligence. Use when a task concerns one real project across multiple applications, its current normalized status, recent redacted change events or nearby projects. Do not use for a simple search of independent DA records.
---

# DA Leads Project Monitoring

Project Intelligence groups related planning applications into a stable canonical
project. Keep that distinction visible: an application is source evidence about a
project, not necessarily the project itself.

Use the tools in this sequence as the task requires:

1. Call `search_projects` with the narrowest known state, project name, stage or
   type. Use `changed_since` for a portfolio-wide update, not for one project's
   event history.
2. If several candidates remain, show the user the stable `project_uid`, state,
   returned location, application UIDs and DA record IDs needed to disambiguate.
   Do not choose from a name match alone.
3. Call `get_project` before making a substantive claim about one project. Treat
   the returned identity, status, location, linked applications and relations as
   separate fields. Do not claim fields the response does not contain.
4. Call `get_project_changes` for history or incremental monitoring. On subsequent
   requests, persist `meta.cursor` after every response. Use `meta.next_cursor`
   only to fetch another page immediately when it is non-null.
5. Use `nearby_projects` only from a supplied or reliably resolved WGS84 point.
   State the radius; do not substitute a suburb centroid without saying so.
6. Use `create_project_watch` only when the user explicitly wants persistent
   callbacks and has supplied a public HTTPS receiver. Reuse one stable
   `idempotency_key` when retrying the same creation. Save the signing secret
   from the create response; `list_project_watches` intentionally omits it.
7. Use `list_project_watches` to inspect registrations and
   `deactivate_project_watch` to stop one. Deactivation does not erase its
   delivery audit trail. It suppresses pending work but cannot recall an HTTPS
   request already in flight; that attempt remains explicit in the audit.
   Cursor polling remains the simpler default when the user has no callback
   receiver.

When interpreting a response:

- Report the canonical project, current normalized status, important linked
  applications and returned event timestamps separately.
- Change values are currently redacted. The API omits rights-blocked fields and
  does not yet return per-project coverage or conflict metadata. An omitted field
  is not evidence that the underlying fact is absent.
- Never upgrade a candidate link or low-confidence association into a confirmed
  project relationship. If sources disagree, explain the conflict.
- Do not infer freshness beyond the returned source/update timestamps.
- Callback payloads remain redacted and receivers must deduplicate the stable
  `Idempotency-Key` header. A callback is a notification to re-read the Project;
  it is not permission to infer withheld change values.
- Do not seek or expose natural-person applicant or owner details. Company and
  professional roles may be used only when the response marks them deliverable.

If Project Intelligence returns 401, explain that the API key is missing or
invalid. For 403, explain that the key lacks the server-side
`project_intelligence` entitlement; do not try another product key or bypass the
gate. For an empty result, report the query and say that the current API does not
provide coverage metadata; do not claim that no project exists.
