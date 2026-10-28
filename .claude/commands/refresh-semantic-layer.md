---
name: refresh-semantic-layer
description: >
  Refresh the saved name-to-ID lookup files for your Fullstory org, using only the Fullstory
  analytics MCP. Run it when an element, funnel or segment returns nothing, or after your
  org changes.
---

# Refresh Semantic Layer

> **Deprecated:** semantic layers are replaced by the org foundation; use `/update-org-foundation` (it carries this layer's IDs across). This command keeps working for harnesses that still carry a layer.

Updates the existing lookup files for this org by reading from Fullstory through the analytics MCP. It reads everything it needs through MCP tools. The only thing it can create in Fullstory is the optional pair of usage-ranking metrics, and only with the user's consent. It never asks the user to copy anything out of their browser or developer tools, and it never calls Fullstory web addresses directly. Use MCP tools only.

---

## Principles

- **Merge, never overwrite.** Refresh changes only the keys listed in Step 4. Every other key is kept exactly as it is.
- **No text matching to decide what something is.** Report names exactly as the customer defined them. Anything that cannot be resolved by ID stays unresolved.
- **Never present a partial result as complete.** Every refreshed section carries a coverage note, and gaps are stated in the summary.
- **Say what cannot be refreshed.** If an MCP tool for something does not exist or fails, name what was not refreshed. Do not work around it.

---

## When to Run

- An element, segment or funnel consistently returns zero results
- You want to capture newly created analytics objects
- The org's instrumentation has changed (selectors renamed, pages restructured)

---

## Step 0 — Find the layer

1. Establish the org from the MCP connection (the `discover_org_context` response or the first tool response). State which org it is and let the user correct you. Use that org ID below.
2. Locate the layer with this finder, which covers both harness layouts (a harness built for a named customer keeps the layer under `semantic-layer/<org-id>/`; the open-source harness keeps it under `clients/<org-id>/semantic-layer/`):

```bash
find ./clients ./semantic-layer -name org.yaml 2>/dev/null | xargs grep -l "<org-id>"
```

The layer directory is the parent of the matching `org.yaml`.

- **More than one match:** list the matches and ask which one to refresh. Never pick one yourself.
- **No match:** tell the user there is nothing to refresh. If this harness lists `/build-semantic-layer`, tell them to run that first; otherwise tell them the lookup files have to be built by their Fullstory team. Then stop.

Never write a backup or copy of any layer file inside `clients/` or `semantic-layer/`. A second `org.yaml` would match the finder.

---

## Step 1 — Read what is stored

Read `org.yaml` in the layer directory and `semantic-index.yaml` if it exists. Look for:

```yaml
semantic_layer_source: analytics-mcp       # how the layer was built (never change this value)
customer_declared_objects:                 # objects the customer prioritized
  segments: [...]
  funnels: [...]
  metrics: [...]
  journeys: [...]
```

and, in `semantic-index.yaml`, a `layer_settings` block (`fullstory_writes`, `kit_metrics`).

- If `semantic_layer_source` is `analytics-mcp`, this layer was built by listing the whole org. Refresh it the same way (Step 2, listings).
- For any other source, refresh only the customer's declared objects. If `customer_declared_objects` is stored, use it without asking. If it is not, ask:

> "To refresh, I need to know which analytics objects matter most to your team. For each of these, list the names or paste the Fullstory URLs and I'll read the IDs from them.
>
> 1. Segments: which user or session segments do you use most?
> 2. Funnels: which conversion flows do you track?
> 3. Metrics: which computed metrics matter most?
> 4. Journeys: which journey maps do you reference?"

Wait for the answer. Pasting a Fullstory page URL is fine. Read IDs from these patterns:

- Segment: `.../segments/details/<id>`
- Funnel: `.../funnels/details/<id>`
- Metric: `.../metrics/details/<id>`
- Journey: `.../journeys/details/<id>`

Store the declaration in `org.yaml` as `customer_declared_objects` (adding the key if absent) so it is not asked again.

---

## Step 2 — Fetch (read-only MCP)

None of these calls write anything.

| Section | Call | Notes |
|---|---|---|
| Declared objects | `get_segment`, `get_funnel`, `get_metric`, `get_journey` with `id` | For every declared or already-recorded ID. A failed lookup means the object is gone: see Step 4. |
| Pages | `get_pages`, or the pages in the `discover_org_context` results if `get_pages` is not offered | Keep pages that have a name. Count the unnamed ones; do not list them. |
| Funnels | `get_funnel` with `regex: ".*"`, `limit: 25`, paging with `offset` | Listing layers only. Collect up to 100. Record `total_matched`. Do not use any StoryAI-only funnel listing: it covers only monitored funnels and does not exist in every org. |
| Segments | `get_segment` with `regex: ".*"`, `limit: 25`, paging with `offset` | Listing layers only. Collect up to 100. Record `total_matched`. |
| Journeys | `get_journey` with `regex: ".*"`, `limit: 25`, paging with `offset` | Listing layers only. Collect up to 50. Record `total_matched`. |
| Metrics | `get_metric` with `regex: ".*"`, `limit: 25`, paging with `offset` | Listing layers only. Collect up to 50. Record `total_matched`. |

When a section's `total_matched` is larger than what you collected, write `coverage: partial` for that section with both numbers (for example `collected: 100, total: 819`) and say so in the summary. For a layer that is not a listing layer, also tell the user how many more objects exist than are in the layer, and offer to add specific ones if they name them.

**Journey responses** include `journey_id`, `name`, `journey_url`, `direction` (`start` or `end`) and `journey_description`. Record only the ID, name, URL and direction. Do not record who created an object.

---

## Step 3 — Usage ranking (optional, needs consent)

Ranks elements and custom events by usage, using the same two metrics as the build skill.

- If `layer_settings.kit_metrics` holds a recorded metric ID, call `get_metric` with that `id`, then compute it with `compute_metric` and the recorded metric ID. Create nothing. Always compute by ID: `compute_metric` with a definition saves a new metric on every call.
- If there is no recorded metric ID and `layer_settings.fullstory_writes` is `read_only`, skip ranking.
- If there is no recorded metric ID and `fullstory_writes` is not set, and this harness does not list `/build-semantic-layer` (the metric definitions live in that skill), skip ranking and say in the summary that usage ranking was not refreshed.
- If there is no recorded metric ID, `fullstory_writes` is not set, and `/build-semantic-layer` is available, ask once:

> **One setup choice: should this create anything in your Fullstory account?**
>
> To rank your site's elements and events by usage, I need to save two chart definitions (called metrics) in your Fullstory account. They hold no session data. If they appear in your metrics list, they are safe to delete.
>
> - **Create the metrics (recommended)**: you get ranked lists of elements and events.
> - **Read-only: create nothing in Fullstory**: I only read from your account. You will get refreshed saved objects, but no usage ranking for elements and events.
>
> This choice is only about creating things inside Fullstory. Either way, nothing about your users' sessions is saved to your computer.

Record the answer in `layer_settings.fullstory_writes` (adding the block if absent). If they choose to create the metrics, build them exactly as `/build-semantic-layer` describes, record the returned metric IDs in `layer_settings.kit_metrics`, and compute by ID. Never modify an existing metric.

Resolve ranked element IDs by calling `discover_org_context` with the IDs themselves as the `queries` (up to 50 per call). Unresolved IDs keep their ID with `name: null`. Do not search by words.

---

## Step 4 — Merge into the layer

Match records by ID, whatever shape the file uses. Edit in place, changing only the lines for the keys below, and keep comments, ordering and every other line exactly as they are.

**Refresh may write only these keys:**

- `name`, unless the stored name is the live name followed by an annotation (for example `Rate Limit (overview)` or `Revenue (2 visits/30d) — note`): an annotated name is kept as it is, because the annotation may hold counts or notes from the original build
- the rendered definition text (for example a funnel's `funnel_description`)
- `clicks_30d`
- `rank` and `unnamed`, written together with `clicks_30d` in `elements.yaml`, only on records that already carry those keys or in layers whose `semantic_layer_source` is `analytics-mcp`; element records without them (for example in a named-harness layer) are left untouched
- `coverage`
- `refreshed: <YYYY-MM-DD>` on every section it updated, and on `org.yaml`
- `layer_settings.fullstory_writes`, only when absent or blank
- `layer_settings.kit_metrics.<key>`, only when absent or blank. A non-blank recorded metric ID is never overwritten, except one whose `get_metric` lookup failed: replace that one with the ID of the metric created to replace it
- `customer_declared_objects`, only when the key is absent
- the generated date (`semantic_layer_generated` in `org.yaml`, `generated` in `semantic-index.yaml`), only when `semantic_layer_source` is `analytics-mcp`
- new records, only when `semantic_layer_source` is `analytics-mcp`, written with just the fields MCP returned
- `missing_as_of: <YYYY-MM-DD>`, see below

**All other keys on every record are preserved byte-for-byte.** That includes fields refresh cannot regenerate, such as tiers, analytics references, groupings, issue counts and visit or volume counts from the original build. Never change `semantic_layer_source`. Never write creator emails.

**Removed objects.** If the ID lookup for a recorded object fails, set `missing_as_of: <date>` on that record. Never delete it, and never leave it looking current. An object that is merely absent from a capped listing is not deleted; only a failed ID lookup marks it missing.

**Files.** Only the layer's own YAML files are edited. `priority-index.md` is regenerated, using the same deterministic ordering as the build skill (coverage notes; top elements by `clicks_30d`; funnels as returned; top custom events as ranked; counts), only when `semantic_layer_source` is `analytics-mcp`. For any other layer it is left untouched, as are `README.md` and every non-YAML file.

**Coverage.** In the coverage block add `dashboards: not refreshable via MCP (current as of <date>)`, using the layer's original build date. MCP has no dashboard tool, so anything derived from dashboards in an existing layer keeps the value it had at build time.

---

## Step 5 — Report to the user

Give a short summary:

1. How many records were updated, added and marked missing, per section.
2. Coverage notes for anything partial.
3. What could not be refreshed and why (always include the dashboard-derived details, with the date they are current to).
4. If ranking ran or metrics were created: the metric IDs, and that they are safe to delete if they appear in the Fullstory metrics list.

---

## Drift Recovery

If this skill is already running, you are already doing a drift recovery. After the refresh, confirm how many objects were updated and which previously recorded objects were marked missing (deleted or renamed in the org).

If an element consistently returns zero results after refresh, it may have been renamed or removed. Ask the customer whether to keep it as it is or update the selector.

For further help, refer to `REFRESH.md` in this harness's root directory.
