---
name: fullstory-mcp-expert-guide
description: >
  Operational playbook for the Fullstory MCP — for teams engineering reliability and
  determinism into their agentic AI workflows. Use whenever you're calling Fullstory MCP
  tools. Covers: picking the right primitive (metric vs segment vs visual session review),
  reading structured definitions for confidence in what will be computed, shaping metric
  definitions inline via compute_metric, the open → view/diff → close lifecycle for visual
  session inspection, and assembling replay URLs from retrieved IDs.
---

## Step 0 — Org Foundation Check (runs before every MCP analysis)

Before calling any Fullstory MCP tool, check whether an org foundation exists for the org being analyzed. This is mandatory — not just for efficiency, but for correctness.

The segments, metrics, funnels, elements, and pages in a customer's Fullstory org aren't arbitrary objects. They're the ones the customer's team built, refined, and actually uses to analyze their business. They encode how that customer defines conversion, engagement, struggle, and value — their data model, in their terms. When Claude builds analytical objects from scratch, it's guessing at that model. The org foundation is a short, dated record of what earlier analyses found about this org. It is not a catalogue: it cannot tell you what exists in the org, only what was found, built and checked before, and when.

### 0a. Identify the target org

Extract the org ID from the conversation. Sources in priority order:
1. Explicitly stated by the analyst ("analyze o-XXXXX-eu1", "for Acme Corp")
2. Present in a Fullstory URL the analyst pasted (look for `/ui/[org-id]/`)
3. Returned by a prior MCP tool call in this session
4. Discoverable via `discover_org_context` (call it once if org is unknown)

If the org ID cannot be determined, ask: "Which Fullstory org are we analyzing? I need the org ID (e.g. `o-XXXXX-na1`) to check for an existing org foundation."

### 0b. Check for an org foundation

Search for an `org.yaml` whose `org_id` is this org, using your own file search tools, under `clients/` and, in a customer harness, `org-foundation/`. The folder holding it is the org folder. If more than one matches, list them and ask which; never pick one yourself.

**If the org folder holds `org-foundation.md` → read it before making any MCP calls.** Read it in full; read `org-foundation-index.md` only when a name misses in it.

Then apply these rules:

- **Use a Known objects ID directly when its row is `confirmed` and under 30 days old. Do not rebuild an object that already exists.**
- A row that is `unconfirmed`, `changed`, `missing`, or more than 30 days old is a lead, not a fact: re-check it through the MCP (`get_funnel`, `get_segment`, `get_metric`, `get_journey`, and `get_pages` if it is offered, or the pages in the `discover_org_context` results) before an analysis relies on it, then update the row with `/update-org-foundation`.
- The foundation does not list what exists. For "what funnels exist?", ask the MCP (`get_funnel` with a narrow `regex`), then record what you used.
- Only call `build_segment` or `build_metric` for questions the foundation and the MCP do not already cover, and record what you built.

**If only an old semantic layer exists** (an `org.yaml` beside a `semantic-index.yaml`): use it as a lead in the same way, tell the analyst once that layers are deprecated, and suggest `/update-org-foundation`, which carries its IDs across. This is not a stop condition.

**If neither exists → prompt before proceeding:**

Do NOT start the analysis. Ask the analyst:

> "No org foundation found for [org-name]. Without one, I have to build segments, metrics, and funnels from scratch — and those objects are guesses at how this customer analyzes their data, not the real thing. The segments, metrics, and funnels already in this org are the ones the customer's team built and actually runs their analysis on. Anything I build from scratch is an approximation of that model.
>
> Run `/create-org-foundation` first? It starts small and grows as you analyze."

If the analyst says **yes / build it**: invoke `/create-org-foundation` before doing anything else. If this harness does not list that command, tell them the org foundation has to be created by their Fullstory team.

If the analyst says **no / skip / proceed anyway**: reply with exactly this, then stop and wait:

> "So you want me to YOLO this analysis without using the customer org's existing instrumentation as a guide. Confirm that's what you want."

If they confirm: proceed with the standard Build → Confirm → Compute workflow. Do not raise the org foundation again this session.

### 0c. Drift detection (during analysis)

As analysis proceeds, watch for these signals that the foundation has drifted from the live org:

- A segment built on a foundation element ID returns 0 sessions (or a fraction that's implausibly low)
- A metric using a foundation metric ID returns an error or empty result
- `discover_org_context` returns element names or IDs that don't match what's in the foundation

If any of these appear, pause and flag:

> "Something from the org foundation is returning 0 or unexpected results — the row may be stale. Selectors change, elements get renamed, and instrumentation evolves. Run `/update-org-foundation` to re-check before continuing?"

Do not silently replace drifted IDs with freshly built objects. Surface the drift and let the analyst decide.

### 0d. Surface the foundation context to the analyst

At the start of the analysis, confirm what was loaded:
- **With a foundation:** "Ready — [N] confirmed, [N] unconfirmed, and [N] missing rows on file for [org-name]."
- **Without (YOLO confirmed):** "Proceeding without an org foundation. Building fresh objects."

Do not enumerate the foundation's contents — just confirm it was loaded and will be used.

---

# Fullstory MCP — Expert Guide

This skill is for teams engineering reliability into their agentic AI stack — workflows where every result needs to be auditable, reproducible, and demonstrably aligned with intent. Exploratory use of the Fullstory MCP doesn't require it; production agentic systems benefit from the discipline it codifies. LLMs are inherently non-deterministic, so reliability has to be engineered in at the workflow layer — that's what this skill is.

The Fullstory MCP exposes three categories of tools, and the difference shapes how you use them:

- **Authoring tools** translate a natural-language `query` or `refinement` into a saved, structured definition: `build_segment`, `build_metric`, `update_segment`, `update_metric`. As with any natural-language interface to a structured system, it's worth a quick read of the resulting definition to confirm the translation captures your intent — much like reviewing the SQL a text-to-SQL tool generated before running it on production data.
- **Read & compute tools** (some, such as `get_opportunities`, `get_opportunity`, `get_managed_funnels` and `get_pages`, are StoryAI Premium only and absent on some orgs) return exactly what's stored or computed in Fullstory: `get_segment`, `get_metric`, `compute_metric`, `get_view_counts`, `get_sessions`, `get_session_events`, `get_pages`, `get_managed_funnels`, `get_opportunities`, `get_opportunity`, `get_opportunity_stats`, `get_sessions_for_opportunity`, `discover_org_context`, `discover_groups`.
- **Visual session review tools** render what a user actually saw and let you compare moments in time: `session_open`, `session_view`, `session_diff`, `session_close`. These hold server-side state — open and close are paired (see *Visual session review* below).

The skill in one sentence: **the structured definition is the contract — inspect it, then compute against it.**

## Principles

These are the invariants the workflow guidance below operationalizes:

- **Treat the structured definition as the contract.** Natural-language queries and auto-generated names are summaries; the structure is what compute runs against, so it's the artifact you inspect, version, and reason about.
- **Source IDs from tools, never reconstruct them.** LLMs are well known to fabricate plausible-looking IDs; anything in a URL, definition, or follow-up call should trace to a tool response.
- **Pair stateful operations.** Every allocation has a release (`session_open` ↔ `session_close`); every authoring call has a corresponding read (the returned definition). Skipping either side breaks the chain.
- **Match the path to the durability you need.** `metric_id` is the stable, audit-friendly handle for anything persistent or referenced downstream; `metric_definition` is for inline, one-off shaping.
- **Prefer deterministic paths when they exist.** Every LLM-mediated step is non-deterministic by nature; every structured step is deterministic. Validator-targeted edits, `metric_definition` adjustments, and ID substitutions are deterministic — re-prompting goes back through the translator.
- **Search structured data for fields by name, not by visual scan.** When verifying a property of a definition, response, or tool schema, locate the field via deterministic keyword search (grep, JSON path, the IDE's find). Visual scanning of nested JSON is a recurring failure mode for LLM agents — missed fields produce confidently wrong conclusions.

The rest of this skill is the operational expression of these.

## Fullstory's data model (and which tool fits)

Understanding the shape of the data tells you which tool to reach for:

- **Session** — the atomic unit. A continuous window of user activity. Every event lives inside a session.
- **Anonymous user** — sessions are attached to an anonymous user (cookie/device-level). When that user is identified (login, API identify call, etc.), Fullstory links their sessions across devices and platforms, so cohorts can span multi-device, multi-platform journeys.
- **Event** — an action within a session (click, page view, custom event, etc.). Every event has a page context, so any event can be refined by the page it happened on and that page's properties — e.g. "clicked X **on** page Y **where** page_property_1 = Z" is expressible at event scope in both metrics and segments.

Tool selection follows from this:

| You want… | Use… | Returns |
|---|---|---|
| A count / rate / trend for one event type, optionally narrowed by a cohort | **`build_metric`** + `compute_metric` | A numeric result (user, session, or event count) |
| A user/session list defined by a multi-step behavioral sequence (within one session or across sessions) | **`build_segment`** + `get_sessions` | The list of users/sessions matching the sequence |
| A count of users in a multi-step sequence | **`build_segment`** to define the cohort, then attach via `update_metric(metric_id, segment_id=...)` and `compute_metric` | A numeric count of the cohort |
| To see what a specific user actually saw at a moment in time, or what changed on screen between two moments | **`session_open`** + `session_view` / `session_diff` (then `session_close`) | A rendered screenshot and component hierarchy, or a visual diff |

Heuristic: reach for a **segment** when the behavior is a sequence ("did X, then did Y"); reach for a **metric** when the question is a count for a single event, optionally narrowed by a segment cohort; reach for **visual session review** when you need to see what the user saw, not just what fired. Page-and-property refinement is event-scoped and works in either metrics or segments.

## Build → Confirm → Compute

The workflow has three beats: build the definition, confirm it expresses your intent, compute against it. The middle beat is where reliability is engineered in.

1. **Build.** Call `build_*` / `update_*`. Keep queries crisp — short, specific phrasings translate more cleanly and serve as their own documentation when you revisit them later. Capture the ID and the structured definition from the response: that JSON is the contract, and exactly what compute will run against. For fresh drafts (URLs containing `/metrics/create/...` or `/segments/.../?create=true`), the build response is your canonical source — `get_metric` / `get_segment` are designed to *search* the catalog of saved objects by regex, not as echo-back for what you just created.

2. **Confirm.** Work from the structured definition when precision matters — the auto-generated name is a human-readable summary, the structure is the compute spec. Read these dimensions deliberately; they're the choices the translator has to make and the ones that matter most for downstream interpretation:
   - **Aggregation** — `default` (event count) vs. `unique: UNIQUE_AGGREGATION_SESSION` (session count) vs. `unique: USER` (user count). These count different things; pick the one matching the question.
   - **Event filter** — `event: {}` (any activity), `event.primary.visitedUrl.any` (page views), `event.primary.click.any` (clicks), etc. The event filter defines the universe being counted; confirm it matches the question.
   - **Unit of measurement** — users vs. accounts vs. organizations; sessions vs. pageviews.
   - **Page scope** — path/title match vs. full URL with query parameters; page-property filters present and correct.
   - **Filter scope** — segment-level vs. event-level; AND vs. OR semantics.
   - **Time range** — defaults to `last_30_days` if not specified. In the definition look for `timeRange.startTime` / `endTime` (e.g. `NOW/DAY-6DAY` → `NOW/DAY+1DAY` = a 7-day window).
   - **Output type** — `single_number`, `top_n`, or `trend` matches the question shape.
   - **Grouping dimension** for `top_n` — present and correct.

   If the definition needs adjustment, two paths: for a one-off compute, edit the `metric_definition` JSON locally and pass it directly to `compute_metric` (see *Direct compute with `metric_definition`* below); for a definition you intend to keep, call `update_metric` / `update_segment` with a `refinement` and re-read the resulting definition.

   Validation feedback from `build_metric` / `compute_metric` carries JSON-pointer paths into the definition — target the specific node to adjust rather than reauthoring. To verify or substitute any ID referenced in a definition, use `discover_org_context` (its results include the pages), `discover_groups`, or `get_pages` if it is offered.

3. **Compute.** `compute_metric` produces the numeric result. Surface it alongside the `metric_url` so the user can drill in further in the Fullstory UI.

## Direct compute with `metric_definition`

`compute_metric` accepts either `metric_id` **or** `metric_definition` — never both. The `metric_definition` parameter (experimental in this beta) lets you compute against an inline definition you've shaped yourself. The most common use is taking a definition `build_metric` produced, making a targeted adjustment (a different enum, an attached segment, an adjusted filter), and computing directly without persisting an intermediate save.

When to use which path:

- **`metric_id`** (preferred) — for any metric you intend to reuse, share, or follow up on (`get_sessions_for_metric`, `update_metric`, etc.). This is the default flow: `build_metric` → `compute_metric(metric_id=...)`. It's also the audit-friendly default — if a downstream system needs to trace what was computed, a `metric_id` is a stable reference back to the spec.
- **`metric_definition`** — for an inline adjustment to a definition `build_metric` returned, without re-authoring. The compute response still returns a `metric_id` for the persisted (unnamed) metric, so you can follow up if needed.

Rules:

- Exactly one of `metric_id` or `metric_definition` must be set. Passing neither or both is rejected up front.
- The `metric_definition` schema mirrors what `build_metric` returns. The surface is experimental during beta; for anything you intend to keep, the `metric_id` path is stable.
- Time-range params (`time_range`, `start_date`, `end_date`) override the definition's embedded time range for this compute, on both paths.
- Inline segment references in the definition are honored — no need to call `update_metric` to attach segments before computing on the definition path.
- The validator runs on the definition before compute. Feedback carries JSON-pointer paths into the definition; use them to target the exact field to adjust.

This path is for adjusting a build_metric-produced definition, not for authoring from scratch — always start from `build_metric` so the structural shape is grounded, then shape inline as needed.

## Funnels: express them as segments

In Fullstory's data model a funnel is a special case of a behavioral sequence, so funnels are expressed through `build_segment` rather than a dedicated builder. `build_metric`'s `output_type` covers `single_number | top_n | trend`; `get_managed_funnels` lists funnels already authored in the Fullstory UI.

To express a funnel ad-hoc, use `build_segment` with the steps phrased as an ordered sequence ("users who did X **and then** did Y"). Confirm in the returned `definition` that you have a `behaviors` array (one entry per step) and `constraints.inOrder: true` — the `inOrder` flag is the difference between "did these events in this order" and "did these events at all", so it's worth a quick check.

Then surface matching sessions with `get_sessions(segment_id=...)`, or attach the segment to a metric via `update_metric(metric_id, segment_id=...)` followed by `compute_metric` for step-by-step counts.

## Visual session review

When the analytics workflow surfaces a session worth inspecting — an outlier from `get_sessions`, a representative session for a metric, a specific user reported by support — the **Agentic Session Review** tools render it visually so you can see what the user actually saw and did, not just what events fired.

### The open → view/diff → close lifecycle

These tools form a strict lifecycle. Order matters, and balancing open with close keeps your concurrent-session budget available for the next investigation.

1. **`session_open(device_id, session_id)`** — opens a session for inspection. Returns a `client_id` (your handle for subsequent calls) and a summary of events with timestamps so you can identify interesting moments. Must be called first; `session_view` and `session_diff` operate against a valid `client_id`. Source the `device_id` / `session_id` from `get_sessions` or `get_sessions_for_metric` rather than from any user-pasted string.
2. **`session_view(client_id, page_id, timestamp)`** — renders a screenshot and component hierarchy as the user saw it at `timestamp`. Use this to confirm what was on screen at a specific moment (form state, error banner, page layout, cart contents).
3. **`session_diff(client_id, page_id, to_ts)`** — compares two timestamps and returns a screenshot with highlighted changes plus a text summary of component modifications. Useful for pinpointing the moment something changed on screen.
4. **`session_close(client_id)`** — **always call this when the investigation concludes, including on the error path.** Treat the `client_id` like a file handle: open and close are paired. Closing promptly returns the slot to your concurrent-session budget.

### Practical notes

- **Walk forward through the session in timestamp order.** Sequential access is the natural traversal pattern and the best-performing one — much like scrubbing forward through a video versus jumping at random.
- **Source timestamps from `get_session_events`, not guesses.** When you need to inspect a specific event (e.g. the click of interest), pull its timestamp from `get_session_events` and pass it to `session_view`.
- **Pair with the analytics workflow.** A common pattern: `build_metric` → `compute_metric` → `get_sessions_for_metric` → `session_open` on a representative `session_id` → `session_view` at the relevant timestamp → `session_close`. Carry IDs through verbatim from each step.
- **Visual review vs. event data.** Use `get_session_events` when the question is *what fired, in what order, with what properties* — structured data, good for programmatic analysis. Use `session_view` / `session_diff` when the question is *what the user saw* — "did the error banner actually render?", "what did the cart look like when they abandoned?". The two compose: use the event stream to find the right timestamps, render screenshots only at those moments.

## Replay URLs — assemble from retrieved IDs

Session replay URLs are composed of several IDs in a specific structure. Assemble them only from values you have actually retrieved from tool responses — guessing or transforming IDs from memory leads to URLs that look plausible but point nowhere.

### Canonical format (always safe)

```
https://{region}/ui/{orgId}/session/{sessionId}
```

This lands the user at the start of the session — the right default when you don't have a specific event to deep-link to.

### Deep-link format (jump to a specific event)

```
https://{region}/ui/{orgId}/session/{sessionId}:({sessionId}!{eventId}({parentId}({rootId})))
```

Worked example (replace placeholders with values from tool responses):

```
https://app.fullstory.com/ui/{orgId}/session/{sessionId}:({sessionId}!{eventId}({parentId}({rootId})))
```

Use the deep-link form only when every inner ID is available verbatim from a tool response. If you don't have all the IDs, use the canonical format — it's always safe.

### Where each component comes from

| Field | Source |
|---|---|
| `region` | `app.fullstory.com` for US orgs, `app.eu1.fullstory.com` for EU orgs. Read from the host of any `metric_url` / `segment_url` / `session_url` already in the conversation — these surface the correct region for the org you're working with. If nothing has been returned yet, default to `app.fullstory.com` (US); don't infer the `eu1` variant from the user's location. |
| `orgId` | A short alphanumeric token. Read from the path of the first `metric_url` / `segment_url` / `session_url` in the conversation and reuse. |
| `sessionId` | `get_sessions` response. Use verbatim. |
| `eventId`, `parentId`, `rootId` | `get_session_events` response, only when you need to deep-link. Use verbatim. |

If an MCP tool returns a replay URL directly, prefer that URL over anything you would construct yourself.

## Pre-response invariants

Before returning an answer that involves Fullstory data, confirm:

- [ ] I chose the right primitive: a **metric** for an event count, a **segment** for a multi-step sequence or a user/session list. Page-and-property refinement is at event scope inside either.
- [ ] For every `segment_id`, `metric_id`, or inline `metric_definition` I'm citing, I read the structured definition (from the build/update response, or the definition I passed to `compute_metric`) and confirmed it expresses the user's intent — filter, aggregation, time range, page scope, output type.
- [ ] If I adjusted a definition or refined an object, I re-read the resulting definition end-to-end.
- [ ] Any validation feedback from `build_metric` / `compute_metric` was addressed at the precise node identified by the JSON-pointer path.
- [ ] Every numeric result came from `compute_metric` or another read tool.
- [ ] If I opened a session with `session_open`, I called `session_close` with the same `client_id` once the investigation finished (including on the error path).
- [ ] Every replay URL was either returned by a tool or assembled from IDs that appeared in tool responses.
- [ ] `region` and `orgId` came from a URL returned earlier in the conversation, not from assumption or the user's location.
- [ ] The `metric_url` from the build/update/compute step is surfaced so the user can drill in further in the Fullstory UI.

If any invariant doesn't hold, fix it before responding.

## When this skill applies

Activate whenever any of these are true:

- You're about to call `build_segment`, `build_metric`, `update_segment`, or `update_metric`.
- You're about to call `compute_metric` with a `metric_definition` (the direct compute path).
- You're about to call `session_open`, `session_view`, `session_diff`, or `session_close` (the visual session review lifecycle).
- You're about to include a Fullstory replay URL in a response.
- You're about to present counts, breakdowns, trends, or comparisons from Fullstory.
- The Fullstory MCP workflow is on a reliability- or determinism-sensitive path (production agentic systems, auditable analytics, customer-facing AI surfaces).

This skill composes with `fullstory:general-analysis` and `fullstory:comparisons` — those describe *which* analytics workflow to run; this one is the operational playbook for executing it reliably. When a workflow ends in an unexpected result, the sibling skill `fullstory-mcp-feedback` captures structured feedback to send back to the Fullstory team.

---

## Activation Conditions

**`fullstory-mcp-expert-guide`** activates whenever Claude is about to call any Fullstory MCP authoring or compute tool (`build_segment`, `build_metric`, `compute_metric`, `session_open`, etc.). Enforces the Build → Confirm → Compute discipline: treat the structured definition as the contract, source all IDs from tool responses, pair stateful operations, prefer deterministic paths. This is the foundational reliability layer that makes analyses auditable and reproducible.
