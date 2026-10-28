---
name: session-validation
description: >
  Final validation protocol for any Fullstory analysis. Activates automatically before
  finalizing conclusions or generating a deliverable. Enforces qualitative ground-truth
  by reviewing a minimum of 5 representative user sessions with deep technical inspection
  of DOM state, console logs, and network errors. Ensures quantitative findings are
  backed by observed session evidence, not just aggregated counts.
---

# Session Validation — Final Analysis Validation Protocol

This skill enforces a mandatory qualitative validation layer on every significant finding. Each finding that makes it into a deliverable gets its own session review pass — not one pass for the whole report.

The principle: **quantitative data tells you *what* happened; session review tells you *why*.**

## When to activate

Run this skill once **per significant finding**, before that finding is written into the deliverable. A 10-finding deck gets 10 passes. A 3-critical-issue snapshot gets 3 passes.

"Significant finding" means any issue, friction point, or drop-off that will be presented to the customer or appear in a customer-facing section of the report. Do not batch findings into a single session review pass — each finding must be grounded independently, because the sessions relevant to a rage click on the checkout button are not the same sessions relevant to a network error on the product page.

Concretely, activate this skill at these moments:

- **DX Hotspot Snapshot** — once per Critical Issue (top 3), after Phase 5 scoring identifies them; run each before Phase 7 writes that issue's detail block
- **Funnel Report** — once per top drop-off step (top 3), after Phase 5 scoring; run each before Phase 6 writes that step's detail block
- **Cohort Comparison** — once per primary behavioral difference being surfaced
- **Hypothesis Swarm** — once per hypothesis returning a CONFIRMED verdict, before the executive summary
- **Ad-hoc analysis** — once per distinct finding you're about to present to the user

Do not skip this step for any finding that reaches the customer. If session data is unavailable (zero sessions returned for a specific finding), note it explicitly on that finding and mark it as quantitative-only.

---

## Step 1 — Session Acquisition

### Identify the source object

Sessions must be drawn from the specific Fullstory analysis object at the heart of the investigation. Use the first applicable method:

| Source | Tool |
|---|---|
| A metric | `get_sessions(metric_id=...)` |
| A segment | `get_sessions(segment_id=...)` |
| A StoryAI Opportunity | `get_sessions_for_opportunity(metric_id=..., group_id=..., group_id_fallback=...)` |
| A funnel drop-off | `get_funnel_sessions(funnel_id=..., completed_step=..., did_not_complete=true)` |

Request `limit: 20` — you need a buffer for the discard-and-replace step in Step 3. Preserve the `metric_url`, `segment_url`, or funnel URL from the source object — it is required in the deliverable output.

### The Minimum 5 Rule

You must successfully review and validate **at least 5 representative sessions**. This is not 5 pulled — it is 5 fully inspected and accepted after the quality control step. Pull more sessions when you expect to discard some.

---

## Step 2 — Deep Session Inspection

For each candidate session, perform this inspection sequence. This is an active technical audit, not passive playback.

### 2a. Open the session

```
session_open(device_id, session_id)
```

This returns a `client_id` and a summary of events with timestamps. Scan the event timeline to identify the **focus point** — the timestamp of the specific issue being analyzed (the dead click, rage click, error event, or drop-off moment).

If the focus point is unclear from the summary, call `get_session_events(session_id)` to get the full chronological event transcript.

### 2b. Apply time padding

Identify the focus point timestamp. Inspect the session across this range:

- **Start:** focus point timestamp − 10,000ms (10 seconds before)
- **End:** focus point timestamp + 10,000ms (10 seconds after)

Do not inspect only the moment of the event. User frustration and confusion builds in the seconds before; the consequences play out in the seconds after.

### 2c. Capture the visual and structural state

At the focus point timestamp, call:

```
session_get_a11y_tree(client_id, page_id, timestamp=focus_ts)
```

Read the accessibility tree for the following signals:

- Is the element the user interacted with present and enabled — or is it in a disabled, loading, or error state?
- Are there visible error banners, modal overlays, or blocking interstitials in the tree?
- Is the page structurally incomplete — missing sections, collapsed content, hidden form fields?

Then call `session_diff` to observe what changed in the 10 seconds after the focus point:

```
session_diff(client_id, page_id, from_ts=focus_ts, to_ts=focus_ts+10000)
```

This reveals whether the UI responded — did a button state change? Did an error message appear? Did the page navigate or freeze?

### 2d. Inspect console and network signals

Call `get_session_events(session_id)` to pull the full event transcript. Review events within the padded window (focus − 10s to focus + 10s):

**Console errors:** Look for JavaScript exceptions, warnings, or `console.error` calls firing in the window. A console error immediately before a dead click often reveals a broken event handler — the click registered but the JS failed silently.

**Network errors:** Look for API calls returning 4xx or 5xx status codes in the window. A failed API request just before a form submission failure is direct evidence of a backend cause for user-facing friction.

Record for each session:
- Visual and structural state at the focus point (summary of a11y tree observation)
- Any console errors present (error text, timing relative to focus point)
- Any network errors present (path, status code, timing relative to focus point)
- What the user did in the 10 seconds after the focus point

### 2e. Close the session

Always close the session before moving to the next:

```
session_close(client_id)
```

Treat `client_id` as a resource handle. Open and close are paired — skipping close depletes your concurrent-session budget and violates the lifecycle defined in `fullstory-mcp-expert-guide`.

---

## Step 3 — Quality Control & Replacement

After inspecting each session, assess whether it is a **pristine representative** of the core issue being analyzed.

**Accept the session if:**
- The issue under analysis clearly occurred in this session
- The user's behavior makes sense in the context of the finding
- The console and network state is consistent with the hypothesis being validated

**Discard the session if:**
- The user abandoned the flow for an obviously unrelated reason (idle timeout, navigated away immediately after landing, external interruption)
- The session is synthetic or bot-driven (no pointer movement, machine-speed inputs, Linux + headless UA string)
- The focus event in this session is a different issue than the one being analyzed (e.g., a rage click on a different element than the one flagged)
- Session data is corrupted or incomplete (no events, missing page context)

When you discard a session, pull the next one from your buffer and inspect it. Continue until you have 5 accepted sessions.

**If you exhaust the buffer before reaching 5:** note the total reviewed and how many were accepted, state that all available sessions were reviewed, and proceed with however many were accepted. Never fabricate an accepted count.

---

## Step 4 — Cross-Comparison & Deliverable Output

### 4a. Cross-compare the 5 accepted sessions

After all 5 sessions are accepted, compare them across these dimensions:

| Dimension | Pattern to look for |
|---|---|
| Console errors | Same JS error text across 3+ sessions → systemic code issue, not coincidence |
| Network errors | Same API path + status code across sessions → backend cause, not user error |
| A11y tree state | Same structural state at the focus point across sessions → async timing issue, disabled state, or layout bug |
| Post-focus behavior | Same user action after the focus event (same rage sequence, same abandonment path) → confirms the issue is the cause, not noise |

**Silent issue reclassification (error-type findings only):**

If the finding under review is a console error, network error, or uncaught exception:

First, confirm that the 5 sessions were drawn from the **attached signal pool** — sessions where the error AND a frustration/exit/funnel signal co-occur — not sampled randomly from the error segment. If the source object for this finding is a raw error segment with no co-occurrence filter, stop: rebuild the segment to require an attached signal, then re-sample. Sessions from an unfiltered error segment do not satisfy this validation.

After cross-comparison, assess the impact confirmation:

| Downstream frustration seen in... | Action |
|---|---|
| 2 or fewer of 5 sessions | **Reclassify as Silent Issue.** The error fires, but the attached signal was noise or coincidental. Remove from Critical/Notable Issues. Add an Engineering Notes callout in the report. Do not present it to the customer as an impactful finding. |
| 3 or more of 5 sessions | Confirmed impactful. Proceed with the original finding and severity. Note the fraction in the root cause signal (e.g., "4/5 sessions showed rage clicks following the error"). |

A finding that reaches the 5-session validation step can still be reclassified. Phase 3a-S is the early gate; this is the authoritative gate. Either can stop an error finding from reaching the customer.

Synthesize into a **root cause signal**: the most consistent, observable explanation for the finding across all 5 sessions.

### 4b. Select the Top 2 best sessions

From the 5 accepted sessions, identify the **2 that best illustrate the issue**. The best session is one where:
- The issue is unambiguous — no confounding behavior
- The technical evidence (console, network, DOM) directly supports the root cause signal
- The user's experience is representative of the broader population, not an edge case

For each of the Top 2, record:
- The session replay URL (assembled per the replay URL rules in `fullstory-mcp-expert-guide`)
- A 1–2 sentence description of exactly what happens: what the user encounters, what they do, and what technical signals are present

Example description format:
> "User clicks the Submit button and waits; no visual response follows. A 503 from `/api/checkout` fires 200ms before the click — the button rendered as active but the API was already unavailable."

### 4c. Assemble the Session Validation section

Add a **Session Validation** section to the deliverable for every Critical Issue. Use this HTML structure (adapt classes to the design system already in use in the report):

```html
<section class="session-validation" data-sync-section="session-validation">
  <div class="section-label">Session Validation</div>
  <div class="section-title">Ground-Truth Confirmation</div>

  <p class="stat-narrative">
    [Root cause signal: 1–2 sentences synthesizing what the 5 sessions confirm.
    Lead with the observable pattern, then the technical evidence that supports it.]
  </p>

  <div class="detail-item">
    <div class="detail-label">Best Example — Session 1</div>
    <div class="detail-value">
      <a href="[SESSION_URL_1]" target="_blank">View session →</a>
    </div>
    <div class="detail-note">
      [1–2 sentences: what happens in this session, including any console/network context]
    </div>
  </div>

  <div class="detail-item">
    <div class="detail-label">Best Example — Session 2</div>
    <div class="detail-value">
      <a href="[SESSION_URL_2]" target="_blank">View session →</a>
    </div>
    <div class="detail-note">
      [1–2 sentences: what happens in this session, including any console/network context]
    </div>
  </div>

  <div class="detail-item">
    <div class="detail-label">Source: [Metric / Segment / Funnel Name]</div>
    <div class="detail-value">
      <a href="[SOURCE_OBJECT_URL]" target="_blank">View in Fullstory →</a>
    </div>
    <div class="detail-note">
      Sessions drawn from this [metric / segment / funnel].
      [N] sessions reviewed; [N] validated as representative.
    </div>
  </div>
</section>
```

**Placement:** Insert the Session Validation section immediately after each Critical Issue block in the report. For a single primary finding, place it as the last section before the footer.

---

## Pre-response invariants

Before marking session validation complete and proceeding to the deliverable, confirm:

- [ ] At least 5 sessions were fully inspected (open → a11y tree → diff → events → close), or all available sessions were reviewed if fewer than 5 existed
- [ ] For error-type findings (console error, network error, uncaught exception): `session_screenshot` was called at the error timestamp for each accepted session, in addition to the a11y tree / session_diff step
- [ ] For error-type findings: all 5 sessions were drawn from the attached signal pool (co-occurrence of error AND frustration/exit/funnel signal) — not sampled from a raw error segment
- [ ] Each session was assessed for representativeness before being accepted
- [ ] Discarded sessions were replaced from the buffer until the minimum was met (or the buffer was exhausted)
- [ ] Console and network signals were checked within the 10s padding window for every accepted session
- [ ] The 5 sessions were cross-compared for consistent patterns
- [ ] A root cause signal was synthesized across the 5 sessions
- [ ] The Top 2 best sessions are identified and described with technical context (including any console/network signals observed)
- [ ] The source object URL (`metric_url`, `segment_url`, or funnel URL) is present in the deliverable
- [ ] Every `session_open` call was matched with a `session_close`

If any invariant is unmet, address it before presenting the deliverable.

---

## Composing with other skills

This skill is the mandatory final step before report generation in:

- `generate-dx-hotspot-snapshot` — run after Phase 5 (Prioritization) for the top 3 Critical Issues; each gets its own Session Validation section before Phase 7
- `build-funnel-report` — run after Phase 5 (Scoring) for the top 3 drop-off steps before Phase 6
- `build-cohort-comparison` — run for the primary behavioral difference identified before generating HTML
- `hypothesis-swarm` — run for any hypothesis returning a CONFIRMED verdict before the executive summary

The session inspection lifecycle (open → get_a11y_tree → diff → close) is documented in `fullstory-mcp-expert-guide`. Follow that lifecycle precisely — this skill inherits all its invariants, including the replay URL assembly rules and the concurrent-session budget discipline.

---

## Activation Conditions

**`session-validation`** activates automatically as the final step of any analysis before presenting conclusions or generating a deliverable. Enforces qualitative ground-truth by reviewing a minimum of 5 representative user sessions with deep inspection of DOM state, console logs, and network errors. Produces a Session Validation section for the deliverable containing the top 2 best example session links and the source object link.
