> **Requires: Fullstory Workforce**
>
> This skill analyzes workforce automation opportunities using Fullstory session
> replay data. It is designed for customers who use Fullstory's Workforce product —
> a configuration that captures cross-application user activity for process mining.
>
> If your customer does not use Fullstory Workforce, the session patterns this skill
> looks for (cross-app switching, manual task cycles, high URL-host breadth) will
> not be meaningfully present in their org. The skill will still run, but findings
> will not reflect real workforce inefficiency.
>
> Check: open `customer.yaml` for this customer. If `workforce: false`, stop here
> and confirm with the customer whether they have the Workforce product before
> proceeding.

---

# Workforce Automation Analysis

Scores and ranks workforce automation opportunities using Fullstory Analytics MCP.
Field-kit port of the Wayfinder `workforce-automation-analysis` skill. Wayfinder-only
tools are replaced with Analytics MCP equivalents; limitations are documented explicitly
in the deliverable.

**Prerequisite:** the workforce analysis foundation skill (`workforce-analysis-foundation.md`) must have run in this session.
Check session context for a `--- WORKFORCE FOUNDATION SUMMARY ---` block containing
`primary_domain`, `window_start`, `window_end`, and `friction_candidates`.
If not present, run the workforce analysis foundation skill (`workforce-analysis-foundation.md`) first and return here.

**Expected duration:** 30–45 minutes of MCP calls.
**Output:** `index.html` deliverable.

---

## Before Starting

Confirm from the foundation summary in session context:
- `primary_domain`: the confirmed target domain
- `window_start` and `window_end`: the analysis window as ISO dates
- `friction_candidates`: the list of groups from `discover_groups` (name + count + metric_url)

If any of these are missing, stop and ask the analyst to provide them or re-run
the foundation skill before continuing.

---

## Tool Mapping (Analytics MCP Port Reference)

| Wayfinder tool | Status in Analytics MCP | Field kit equivalent |
|---|---|---|
| `discover_context` | Not available | Removed — analyst provides workflow context; `discover_org_context` substitutes |
| `discover_org_context` | Available | Identical call |
| `query_workflow_instances` | Not available | Session count metric as proxy (Phase 1a) |
| `query_workflow_events` | Not available | Session duration metric as proxy (Phase 1b) |
| `get_aggregate_workflow_metrics` | Not available | Removed — session estimates replace; caveat written into output |
| `analyze_workflow_instance` | Not available | Removed — Phase 2 session review handles deep dives |
| `build_metric` | Available | Identical call |
| `compute_metric` | Available | Identical call |
| `update_metric` | Available | Identical call |
| `get_sessions` | Available | Identical call |
| `analyze_session` | Not available (Wayfinder sub-agent) | `session_open` + `get_session_events` + `session_close` |
| `discover_groups` | Available | Called in foundation skill; results consumed as context — do not call again |
| `submit_report` | Not available (Wayfinder output) | `index.html` deliverable via `_starter.html` template |

---

## Phase 1: Session-Based Workflow Signals

**Important — read before proceeding:** Phase 1.1 metrics are session-based proxies.
Fullstory Workforce workflow instance data (exact cycle time, handoff counts,
per-instance app switching) requires a Wayfinder-connected org. Scores derived
from Phase 1.1 are directional, not precise. The deliverable must include the
mandatory caveat block from Phase 4.

### Step 1a — Volume Proxy (Instance Count Approximation)

Replaces: `query_workflow_instances` + `query_workflow_events`

```
build_metric(
  query="count of sessions where URL host is {primary_domain}",
  output_type="single_number",
  start_date=window_start,
  end_date=window_end
)
compute_metric(metric_id=...)
```

Record the result as `session_count`. This is the proxy for workflow instance volume.

### Step 1b — Duration Proxy (Cycle Time Approximation)

Replaces: `get_aggregate_workflow_metrics` (cycle time component)

```
build_metric(
  query="session duration grouped by URL host where URL host is {primary_domain}",
  output_type="top_n",
  start_date=window_start,
  end_date=window_end
)
compute_metric(metric_id=...)
```

Extract the p50 session duration as `median_session_duration`. This is the proxy for
median workflow cycle time.

### Step 1c — Cross-App Signal (Swivel Proxy)

Replaces: `get_aggregate_workflow_metrics` (app-switching component)

```
build_metric(
  query="count of distinct URL hosts visited per session where primary host is {primary_domain}",
  output_type="single_number",
  start_date=window_start,
  end_date=window_end
)
compute_metric(metric_id=...)
```

Record as `cross_app_breadth` — the average number of distinct domains visited per session.
Higher values indicate more app-switching, a key automation indicator.

### Step 1.2 — Focused Time

Identical to Wayfinder version.

Build a metric for active time on the primary domain:

```
build_metric(
  query="active time on {primary_domain}",
  output_type="single_number",
  start_date=window_start,
  end_date=window_end
)
```

After receiving the metric definition, clone it and swap the `builtInProperty` to `28`
(focused time). Compute both:

```
compute_metric(metric_id=...)           # active time result
update_metric(metric_id=..., builtInProperty=28)
compute_metric(metric_id=...)           # focused time result
```

Compute: `work_type_ratio = active_time ÷ focused_time`
A ratio significantly above 1.0 indicates task-switching rather than focused work.

### Step 1.3 — Interaction Signals

Identical to Wayfinder version.

```
build_metric(
  query="clicks grouped by element on {primary_domain}",
  output_type="top_n",
  start_date=window_start,
  end_date=window_end
)
discover_org_context(query="named events on {primary_domain}")
compute_metric(metric_id=...)
```

Record the top 10 most-interacted elements and any named events that suggest manual
data entry, copy/paste, or repeated form submission.

### Step 1.4 — Friction Candidates (from Foundation)

[Phase 1.4 (`discover_groups`) already ran in the foundation skill — consume friction
candidates from the `--- WORKFORCE FOUNDATION SUMMARY ---` block in session context.
Do not call `discover_groups` again.]

---

## Phase 2: Session Deep Dives

Replaces: `analyze_session` Wayfinder sub-agent
Uses: `session_open` + `get_session_events` + `session_close` (field kit session review protocol)

### Step 2.1 — Session Selection

```
build_metric(
  query="count of page views where URL host is {primary_domain}",
  output_type="single_number"
)
get_sessions(metric_id=..., limit=20)
```

From the 20 sessions returned, select 3 that exhibit the strongest combination of:
- High page count (top quartile of the 20 returned)
- Multi-domain URL pattern (multiple distinct URL hosts visible in session metadata)
- Any friction signals from Phase 1.3 elements or Phase 1.4 friction candidates

### Step 2.2 — Session Review

For each of the 3 selected sessions, run the standard field kit session review:

```
session_open(session_url)
get_session_events(session_id, device_id)
session_close(session_url)
```

Manually extract from each session:
- **Cross-app navigation sequences**: URL host changes within the session (the swivel pattern)
- **Copy/paste and form-fill patterns**: from event types (paste events, input change events)
- **Friction moments**: rage clicks, error clicks, repeated actions on the same element
- **Representative session URL with timestamp suffix**: `{session_url}:{absolute_ms_from_event}`

Do not construct or modify session URLs. Use the exact values from `get_session_events` responses.

### Step 2.3 — Key Moments

From the 3 session reviews, select 5–8 compelling moments that illustrate:
- Cross-app switching burden (user navigating between tools in a chain)
- Manual data re-entry (same data typed into multiple systems)
- Friction on high-frequency tasks (repeated actions suggesting inefficiency)

Format each key moment as:
```
{session_url}:{absolute_ms_from_event} — [one-line description of what the user is doing]
```

---

## Phase 3: Synthesis and Scoring

### Candidate Identification

Gather automation candidates from three sources:
1. Phase 1 signals — elements with high click frequency (Step 1.3), long cycle time (Step 1b), high cross-app breadth (Step 1c)
2. Phase 2 session observations — observed copy/paste chains, manual swivel sequences
3. Phase 1.4 friction groups — groups from `discover_groups` in foundation skill

Consolidate into a ranked candidate list. Eliminate duplicates.

### Automation Classification

For each candidate, assign exactly one of:
- **Fully Automated**: Task can be eliminated — the system can do it without any user input
- **AI-Assisted**: User remains in the loop, but AI can pre-fill, suggest, or validate
- **Process Automated**: Workflow routing or notification logic, not UI interaction

### Scoring

For each candidate, compute:

```
hours_saved = (events_per_month × minutes_per_event × eliminability_pct) ÷ 60
```

Where:
- `events_per_month`: from Phase 1a `session_count` × estimated task frequency per session
- `minutes_per_event`: from Phase 1b `median_session_duration` (for full-workflow candidates) or estimated sub-task time from session observation
- `eliminability_pct`:
  - Fully Automated → 0.80 (20% residual oversight assumed)
  - AI-Assisted → 0.40
  - Process Automated → 0.60

**Caveat statement (mandatory — include in every candidate description and in Phase 4):**
Active/focused time divergence check is unavailable without Wayfinder integration.
Conservative session estimates are used. Cycle time and app-switching data are
session-based approximations. Exact workflow instance metrics require Fullstory
Workforce + Wayfinder integration.

### Sorting

Sort all candidates by `hours_saved` descending.

Compute hero totals:
- **Total Hours Saved/Month**: sum of all candidates' `hours_saved`
- **FTE Equivalent**: Total Hours Saved/Month ÷ 160
- **Automation Candidates**: count of distinct candidates

---

## Phase 4: Deliverable

Produce the deliverable using the standard field kit templates. Check `customer.yaml` for PS/Advantage flags to determine PS plug inclusion.

### `index.html` (customer-facing deliverable)

Use `_starter.html` as the base template.

**Hero KPI row — three tiles:**
- Total Hours Saved/Month
- FTE Equivalent
- Automation Candidates count

**Ranked candidate table:**
| Rank | Workflow | Automation Level | Hours Saved/Month | Primary Tools |
|---|---|---|---|---|

Include one row per candidate, sorted by `hours_saved` descending.

**Key moments section:**
List the 5–8 session deep-links from Phase 2.3, each with a one-sentence description.
Use the exact deep-link URLs — do not modify them.

**Mandatory caveat block — include this HTML verbatim:**
```html
<div class="callout">
  <p><strong>About these estimates:</strong> Cycle time and app-switching data are
  session-based approximations. Exact workflow instance metrics (precise cycle time,
  handoff counts, per-instance app switching) require Fullstory Workforce + Wayfinder
  integration. Conservative session estimates are used throughout. Findings are
  directional — validated against session replay evidence.</p>
</div>
```

Place the caveat block immediately before the ranked candidate table.

---

After producing the file, update `MEMORY.md`:
```
- [YYYY-MM-DD] Workforce automation analysis: [report-slug]
```
