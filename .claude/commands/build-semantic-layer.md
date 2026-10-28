---
name: build-semantic-layer
description: >
  Map a Fullstory org's pages, funnels, segments, elements and events into lookup files,
  using only the Fullstory analytics MCP. Use when the user asks to map their org, or when
  analysis needs org context that has not been built yet. Reads from Fullstory and writes
  local name-to-ID files. Requires the Fullstory analytics MCP; no other connection is
  needed.
---

# Build Semantic Layer

Maps this Fullstory org's pages, elements, events, funnels, segments, journeys and metrics into local YAML files, so analysis skills can look up IDs instead of guessing. Everything is read through the Fullstory analytics MCP.

---

## Principles

- **No text matching to decide what something is.** Sites and apps render in many languages. Never infer an element's meaning, page's purpose or event's role from words in its name or text. Names are reported exactly as the customer defined them. Anything that cannot be resolved by ID is recorded as unresolved.
- **Never present a partial result as complete.** Every section of the layer carries a coverage note. Gaps are stated in the summary.
- **Writes happen inside Fullstory only, and only with consent.** See Step 1.

---

## Capability Check

Before anything else, confirm the Fullstory analytics MCP is connected: call `discover_org_context` with a short `queries` list. Only a connection-level failure means it is not connected; a validation message about the arguments means retry with arguments. If it is not, stop and tell the user: "I need the Fullstory analytics MCP connected to map your org. Connect it, then run /build-semantic-layer again."

---

## Pre-flight

1. State which org the MCP is connected to (from the `discover_org_context` response or the first tool response) and let the user correct you if it is the wrong one. Use that org ID as `[org-id]` in every path below. Do not ask the user for a client name; the org ID names the folder.
2. If `clients/[org-id]/semantic-layer/semantic-index.yaml` exists, this is a **refresh**. Read its `layer_settings` block and reuse the recorded consent choice without asking again. Tell the user the lookup files were last built on `generated:` and that you are refreshing them.

---

## Step 1 — Fullstory write access (first build only)

Ask this once per org. Record the answer in `layer_settings.fullstory_writes` (`allowed` or `read_only`) and never ask again unless the user asks to change it.

Show this, in plain words, exactly once:

> **One setup choice: should this create anything in your Fullstory account?**
>
> To rank your site's elements and events by usage, I need to save two chart definitions (called metrics) in your Fullstory account. They hold no session data. If they appear in your metrics list, they are safe to delete.
>
> - **Create the metrics (recommended)**: you get ranked lists of elements and events.
> - **Read-only: create nothing in Fullstory**: I only read from your account. You will get pages, funnels, segments, journeys and metrics, but no usage ranking for elements and events.
>
> This choice is only about creating things inside Fullstory. Either way, nothing about your users' sessions is saved to your computer. The only files I write locally are the names and IDs of your pages, events, elements and other saved objects.

Do not use the words "skip" or "disable" for the read-only option. Do not proceed until the user picks one.

---

## Step 2 — Inventory (read-only, always runs)

Use these calls. None of them write anything.

| Section | Call | Notes |
|---|---|---|
| Pages | `get_pages`, or the pages in the `discover_org_context` results if `get_pages` is not offered | Keep every page that has a name. Count the unnamed (learned) pages and record the count; do not list them. |
| Funnels | `get_funnel` with `regex: ".*"`, `limit: 25`, paging with `offset` | Collect up to 100. Record `total_matched`. Record name, ID, and the rendered definition (`funnel_description`). Do not use any StoryAI-only funnel listing: it covers only monitored funnels and does not exist in every org. |
| Segments | `get_segment` with `regex: ".*"`, `limit: 25`, paging with `offset` | Collect up to 100. Record `total_matched`. |
| Journeys | `get_journey` with `regex: ".*"`, `limit: 25`, paging with `offset` | Collect up to 50. Record `total_matched`. |
| Metrics | `get_metric` with `regex: ".*"`, `limit: 25`, paging with `offset` | Collect up to 50. Record `total_matched`. |
| Revenue event | `discover_org_context` (any query) | Read the top-level `revenue_event` object. |

When a section's `total_matched` is larger than what you collected, write `coverage: partial` for that section with both numbers (for example `collected: 100, total: 1304`). Say so in the summary.

---

## Step 3 — Usage ranking (needs `fullstory_writes: allowed`)

If `fullstory_writes` is `read_only`, skip to Step 4 and mark elements and custom events `coverage: none (read-only mode)`.

Otherwise, for each of the two rankings (elements, custom events):

1. **Reuse by recorded metric ID only.** If `layer_settings.kit_metrics.<key>` holds a recorded metric ID, call `get_metric` with that `id`. If it returns the metric, compute it (item 3) and create nothing. Never search metrics by name: a metric created through the Fullstory connection is not found by a name search, so a name search can never confirm that one exists.
2. **Create** only when there is no recorded metric ID, or `get_metric` by that ID fails. Save the new `metric_id` as the recorded metric ID, replacing any old one.
   - *Top custom events*: `build_metric` with `output_type: top_n`, `metric_name: "[kit] Top custom events"`, `time_range: last_30_days`, query "count of custom events grouped by custom event name, top 50". Record the returned `metric_id`.
   - *Top clicked elements*: `build_metric` cannot group clicks by element. Call `compute_metric` with this `metric_definition`. The result includes the new `metric_id` (the metric is saved without a list name); record it:

     ```json
     {"id": "metric_builder_result", "name": "[kit] Top clicked elements",
      "metric": {"single": {"aggregation": {"default": {}},
        "event": {"primary": {"click": {"any": {}}}}}},
      "dimensionality": {"dimensionSettings": {
        "dimension": {"builtInProperty": 27},
        "dimensions": [{"builtInProperty": 27}],
        "limit": 50, "sortOrder": "SORT_ORDER_DESC"},
        "timeRange": {"endTime": "NOW/DAY+1DAY", "startTime": "NOW/DAY-29DAY"}}}
     ```

3. **Compute** with `compute_metric` and the recorded metric ID. Record each result row. Always compute by ID: `compute_metric` with a definition saves a new metric on every call, so never pass a definition for a ranking that already has a recorded metric ID.

Never modify an existing metric. The only metrics this skill ever computes are ones whose IDs this workspace recorded. A new workspace (a different folder, or a layer with no recorded metric ID) creates its own pair.

---

## Step 4 — Resolve names by ID

Each ranked element row is either a 12-character element ID or a raw CSS selector (an element nobody has named yet).

- For IDs, call `discover_org_context` with the IDs themselves as the `queries` (up to 50 per call). An ID query returns the exact element with its name and selector. Do not search by words.
- Anything that does not resolve keeps its ID, with `name: null`.
- Raw selector rows are recorded as `unnamed: true` with the selector. Do not label them.

For funnel steps, journeys and segments, resolve any element, event or page IDs the same way (ID query first). Unresolved IDs are recorded as IDs with `name: null`.

Defined events and user properties are listed only if a funnel, segment, journey or metric references them, plus the revenue event. State in the summary that this list is built from references, not from a full catalog.

---

## Step 5 — Write local files

Write to `clients/[org-id]/semantic-layer/` (create it if absent). The expert guide finds a layer by locating an `org.yaml` that contains the org ID, and reads the other files from that same directory, so `org.yaml` must be written into this directory, not above it.

| File | Contents |
|---|---|
| `org.yaml` | Org ID, org name, generated date, source. The org name comes from the user if they offered one; otherwise leave it blank. Never invent one. No staff names, no internal fields. |
| `priority-index.md` | The expert guide reads this first. Deterministic ordering only, in this order: coverage notes; top elements by `clicks_30d` (rank, name or ID); funnels as returned (name, ID); top custom events as ranked; counts of segments, journeys, metrics and pages. Do not rank by guessed importance and do not describe what any item means. |
| `semantic-index.yaml` | Compact name-to-ID lookup. |
| `elements.yaml` | Ranked elements: rank, ID, name or `null`, selector, clicks_30d, `unnamed` flag |
| `pages.yaml` | Named pages: ID, name. Count of unnamed pages. |
| `events.yaml` | Custom events (ranked if available) and referenced defined events. Revenue event flagged. |
| `funnels.yaml` | ID, name, rendered definition |
| `segments.yaml` / `journeys.yaml` / `metrics.yaml` | ID, name, plus journey direction and URL |
| `README.md` | Coverage summary and how to refresh |

`org.yaml` format:

```yaml
org_id: [org-id]
org_name: "[org name if the user offered one, otherwise blank]"
semantic_layer_generated: "YYYY-MM-DD"
semantic_layer_source: analytics-mcp
```

`semantic-index.yaml` format:

```yaml
org: [org-id]
name: "[org name if the user offered one, otherwise blank]"
generated: "YYYY-MM-DD"
layer_settings:
  fullstory_writes: allowed          # or read_only
  kit_metrics:
    top_clicked_elements: "[metric id or blank]"
    top_custom_events: "[metric id or blank]"
coverage:
  pages: complete
  funnels: {collected: 100, total: 819}
  segments: {collected: 100, total: 1304}
  journeys: {collected: 50, total: 186}
  metrics: {collected: 50, total: 6835}
  elements: ranked-top-50            # or none (read-only mode)
  custom_events: ranked-top-50       # or none (read-only mode)
  defined_events: referenced-only
segments:
  "Segment name": segment_id
funnels:
  "Funnel name": funnel_id
elements:   # ranked by clicks_30d; unnamed selectors are in elements.yaml only
  "Element name": element_id
metrics:
  "Metric name": metric_id
pages:
  "Page name": page_id
events:
  "Event name": event_id_or_name
journeys:
  - id: "<journey_id>"
    name: "<name>"
    url: "<journey_url>"
    direction: "<start|end>"
```

**Population check:** if every analytics section (funnels, segments, elements, pages, events, metrics) is empty, treat the build as failed: tell the user, and write none of these files, including `org.yaml`, so the expert guide does not find an empty layer.

---

## Step 6 — Report to the user

Give a short summary:

1. Counts per section, with the coverage note for anything partial.
2. If ranking ran: the top 10 elements and top 10 custom events, and how many of the top 50 elements resolved to a name.
3. If read-only: one plain sentence, "I did not rank elements or events because you chose read-only mode; ask me to change that if you want rankings."
4. If metrics were created: their IDs, and that they are safe to delete if they appear in the Fullstory metrics list. Say that a new workspace creates its own pair.
5. How to refresh: run /build-semantic-layer again. It reuses the recorded metrics and will not create new ones.

---

## Hard Rules

- The only writes allowed in Fullstory are creating up to two metric definitions in Step 3, and only when `fullstory_writes` is `allowed`. Never modify or delete anything that already exists. The only metrics ever computed are ones whose IDs this workspace recorded.
- Never infer meaning from names or text. Report names verbatim; record unresolved items as unresolved.
- Never report a partial section as complete.
- Never write session data, user data or event payloads to local files. Only names, IDs, selectors and counts.
- Write the brand as "Fullstory", with a lowercase "s".
