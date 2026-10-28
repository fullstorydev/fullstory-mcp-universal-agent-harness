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

# Workforce Analysis Foundation

Orients the analyst to a workforce customer's Fullstory org before running a full
automation opportunity analysis. This skill runs first — always — and its output
seeds the workforce automation analysis skill (`workforce-automation-analysis.md`) that follows.

**Expected duration:** 10–15 minutes of MCP calls.
**Output:** Structured in-session summary (prose, no HTML). Not a deliverable.

---

## Phase 0: Analyst Orientation

Ask the analyst the following before making any MCP calls:

> "Before I start, two things I need from you:
> 1. What workflow or process do you want to analyze? (e.g., order management, claims processing, onboarding)
> 2. What is the analysis window? (e.g., last 30 days, last 90 days, a specific date range)"

Wait for the analyst's response. Do not proceed until both answers are given.

Record:
- `target_domain_hint`: the workflow/process the analyst named (used to filter domains in Phase 1b)
- `window_start` and `window_end`: the analysis window as ISO dates (e.g., 2026-07-28, 2026-08-27)

---

## Phase 1: Discovery

### Step 1a — Org Context

Call `discover_org_context` three times in sequence:

```
discover_org_context(query="tools")
discover_org_context(query="most visited domains")
discover_org_context(query="applications")
```

Synthesize results into a short tool stack summary: top 5–8 applications by domain,
noting any that match the analyst's `target_domain_hint`.

### Step 1b — URL Host Breakdown

Build a page-view metric grouped by URL host to establish the domain landscape:

```
build_metric(
  query="page views grouped by URL host",
  output_type="top_n",
  start_date=window_start,
  end_date=window_end
)
```

After receiving the metric definition, verify the grouping dimension is `DIMENSION_URL_HOST`.
If the response shows `DIMENSION_URL` instead, correct it:

```
update_metric(metric_id=..., dimension="DIMENSION_URL_HOST")
```

Then compute:

```
compute_metric(metric_id=...)
```

From the results:
- Identify the top 5–8 domains by page view share
- Present the ranked list to the analyst with percentage shares
- Ask: "Which of these domains is the primary target for your workflow analysis?"
- Wait for confirmation. Record the confirmed domain as `primary_domain`.

### Step 1c — Initial Friction Signals

Call `discover_groups` against the confirmed primary domain:

```
discover_groups(
  domain=primary_domain,
  limit=5,
  start_time=window_start,
  end_time=window_end
)
```

For each group returned, record:
- `group_name`: the name of the friction group
- `count`: number of affected sessions or users
- `metric_url`: the URL from the group response (used for drill-down in the automation skill)

---

## Output: Structured Session-Context Summary

After Steps 1a, 1b, and 1c complete, present this summary in the session:

```
--- WORKFORCE FOUNDATION SUMMARY ---

Customer: [customer name]
Analysis window: [window_start] → [window_end]
Primary domain: [primary_domain]

Tool stack (top domains by page-view share):
1. [domain] — [X]%
2. [domain] — [X]%
3. [domain] — [X]%
...

Initial friction candidates (from discover_groups):
- [group_name] | [count] sessions | [metric_url]
- [group_name] | [count] sessions | [metric_url]
...

NEXT STEP: Run the workforce automation analysis skill (`workforce-automation-analysis.md`). It will build on this context
to score and rank automation opportunities. Keep this summary visible — the
automation skill will ask for: primary_domain, window_start, window_end,
and the friction candidate list above.
--- END FOUNDATION SUMMARY ---
```

Do not produce an `index.html`. This summary is a research artifact only.
No deliverable is created by this skill.
