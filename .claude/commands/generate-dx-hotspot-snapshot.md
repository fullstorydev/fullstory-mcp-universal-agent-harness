# Generate DX Hotspot Snapshot

Build a Fullstory DX Hotspot Snapshot for a customer account — a data-driven, executive-ready analysis of the top areas of user struggle across their digital property. Delivered monthly as either a self-contained HTML one-pager or an HTML slide deck.

## When to invoke

Use this skill when a analyst asks to:
- Build a DX Hotspot Snapshot for a customer
- Generate a monthly digital experience review
- Produce a UX health summary for an account meeting
- Create session-backed evidence of where users are struggling

---

## Pre-Flight — MEMORY.md Check

Before asking the analyst anything, check if `MEMORY.md` exists in the current working directory.

If it does **not** exist, create it silently with this content:

```markdown
# analyst Workspace Memory
**Owner:** (run /setup to add your name)

## Active Customers
<!-- One line per active customer -->
<!-- Format: - [Customer Name] — [what you're currently working on] -->

## Recent Deliverables
<!-- Updated each time you complete a report or playbook -->
<!-- Format: - [YYYY-MM-DD] [Customer] — [type]: [report slug] -->
```

Do not tell the analyst you created it — proceed directly to Phase 0.

---

## Phase 0 — Intake

Ask all of the following in a single message. Do not proceed until you have answers to all of them.

```
Before I begin the analysis, I need a few things:

1. CUSTOMER NAME
   What is the name of the customer this report is for?

2. CUSTOMER LOGO
   Where can I find the customer's logo?
   - A direct URL to the logo file, OR
   - A local file path on your machine, OR
   - "Skip" to use text-only branding

3. TIME WINDOW
   What time period should this report cover?
   Default is last 30 days — specify a different range if needed.

4. REPORT FORMAT
   How should this be delivered?
   - ONE-PAGER: A single scrollable HTML page
   - DECK: An HTML slide deck (multi-slide, presentation-ready)

5. AUDIENCE
   Is this for a TECHNICAL audience (engineers, product managers)
   or a BUSINESS audience (executives, VPs, non-technical stakeholders)?
```

---

## During Analysis — Analyst Check-ins

This analysis runs many parallel queries across 6 phases and may take 5–10 minutes. Do not go silent. After completing each major phase, post a brief plain-language status line to the analyst before moving to the next:

- After Phase 1: "I've mapped [Customer]'s top pages and found their conversion goal — [what was found or what the analyst named]. Mapping user journeys now."
- After Phase 2: "Journey mapping done — found [N] main traffic paths. Pulling friction signals now."
- After Phase 3: "Found [N] friction signals across [N] pages. Prioritizing now."
- After Phase 6: "Session links collected for all top issues, plus [N] highlight clip candidates. Generating the report and field guide now."

Keep these to one sentence. No API IDs, segment IDs, metric IDs, or tool names in analyst-facing status messages.

---

## Phase 1 — Discovery

### 1a. Page Inventory

Call `get_pages`, or read the pages in the `discover_org_context` results if `get_pages` is not offered. `discover_org_context` returns pages only when a query matches them, so on that route list what the queries found and do not claim a complete list of pages. Separate pages that have a name from pages with an empty name or none (identify an unnamed page by its `url_pattern` and numeric `page_id`; never guess a name, and never key on `is_user_defined`, which is absent on some pages). Named pages drive the analysis. Note how many unnamed pages exist — high unnamed volume is a tagging gap worth surfacing in the report.

### 1b. Revenue Event Detection

Call `discover_org_context` with queries: `["revenue", "purchase", "order", "booking", "payment", "conversion", "checkout success", "transaction", "complete", "confirm"]`

Look for a **defined event** that fires when a user completes the core goal of the digital property (a purchase, booking, subscription, etc.). This is the conversion anchor for the entire report.

**If no Revenue Event is found**, prompt the analyst:

> Quick question before I dig in — what's the most important action on [Customer]'s site? For example, placing an order, completing a booking, or finishing a signup. That's the goal I'll use as the anchor for this analysis.

Use the analyst's answer as the conversion anchor for the rest of the analysis.

### 1c. Opportunities (StoryAI)

Call `get_opportunities` for the time window, only if it is offered.

- If results return: store them. StoryAI pre-ranks these by impact — they carry extra weight in Phase 5.
- If it is empty or not offered: Say once, in plain words, that this org does not have the StoryAI Opportunity tools and the analysis continues without StoryAI Confirmed badges. Never present a finding as StoryAI Confirmed without a real `get_opportunities` result, never stall, never report a dead connection, and never invent a result. Not all orgs have this feature.

---

## Phase 2 — Traffic & Journey Mapping

Map the dominant user journeys across the site. This tells you which paths matter most and where users fall off.

### 2a. Top 5 Named Pages by Traffic

Build a metric: page views grouped by page name, `top_n`, for the report time window. Compute it. Take the top 5 rows with **named** pages (skip numeric ID rows). These are your primary analysis surfaces.

### 2b. Step 1 → Step 2 (Next Page After Each Top Page)

For each of the 5 named pages, build a metric in parallel:
- Event: Visited Page = ANY
- Filter: Previous Page is [this page]
- Group by: Page
- Output: `top_n`

Build all 5 in parallel. Compute all 5 in parallel. For each result, take the top named next page (skip numeric IDs). You now have the dominant hop from each top page.

### 2c. Step 2 → Step 3 (Extend the Three Most Important Journeys)

For the 3 most significant page-to-page transitions from Step 2b:

1. Build a **segment**: users who visited [page 1] then [page 2], in that order, within the same session.
2. Build a **metric**: Visited Page = ANY where Previous Page is [page 2], grouped by page, scoped to that segment.
3. Compute.

Build all 3 segments and 3 metrics in parallel, then compute in parallel.

### 2d. Identify the Conversion Path and Friction Points

From the journey data, identify:
- **The primary conversion funnel**: the sequence of pages most users traverse toward the Revenue Event.
- **Reverse-navigation pages**: pages where a meaningful share of users go back to a prior page. This is a friction signal — users are confused or reconsidering.
- **Drop-to-unknown pages**: steps where users go to unnamed/untagged pages at high volume. Flag as a tagging gap.
- **Exit pages**: the last named page before sessions end without converting. Friction here directly costs conversions.

Summarize the top 3 confirmed journeys as: `Page A → Page B → Page C (N total transitions, X% reaching step 3)`

---

## Phase 3 — Friction Signal Collection

### 3a. Standard Frustration & Error Groups (Org-Wide)

Call `discover_groups` with no scope — org-wide — to surface the top issues across all standard proactive metrics:

- Dead clicks by element
- Error clicks by element  
- Rage clicks by element
- Abandoned forms by page
- Console errors by text
- Network errors by path
- Uncaught exceptions by text
- Refreshed pages by page
- App crashes by page (mobile)

Set `limit: 10`. Store all returned `(default_metric_id, group_id, group_id_fallback)` tuples.

Also call `discover_groups` with `compare_to_previous: true, comparison_mode: "worsening"` to catch signals trending worse — these get an urgency flag in the report.

### 3b. Cursor Thrashing

Cursor thrashing is not covered by `discover_groups`. Build a separate metric:
- Event: Thrashed cursor
- Output: single number, then `top_n` grouped by page

Compute both. Identify which pages have the highest thrash rates. Cursor thrashing indicates user frustration and confusion — users moving the cursor rapidly without clear intent.

### 3c. Watched Element Analysis

Watched elements are tracked at two moments: when they render into the **DOM** (exists on the page) and when they render into the **viewport** (user actually sees it). These are fundamentally different signals.

**Step 1: Pull top 20 watched elements by volume**

Build a metric: Watched Element events (any), grouped by Element / CSS Selector, `top_n`. Compute. Take the top 20 element names.

**Step 2: Reason through element names**

For each of the 20 names, assess whether the name suggests a potentially negative user experience. Flag elements whose names suggest:
- Loading states: "spinner", "loader", "loading", "skeleton", "progress", "wait"
- Error conditions: "error", "warning", "alert", "invalid", "failed", "retry", "oops", "sorry"
- Empty states: "empty", "no results", "zero", "not found", "unavailable", "none"
- Blocking UI: "modal", "overlay", "interstitial" (context-dependent — assess the name)

Do not flag elements suggesting positive states (e.g., "success", "confirmation", "complete").

**Step 3: DOM vs. viewport analysis for flagged elements**

For each flagged element, build two metrics in parallel:
- Metric A: Watched Element events — rendered into DOM — for this element name
- Metric B: Watched Element events — rendered into viewport — for this element name

Compute both. Interpret:

| Pattern | Meaning | How to flag |
|---|---|---|
| DOM count >> Viewport count (large gap) | Element exists but users rarely or never see it | UX problem — something tracked is off-screen, hidden, or never surfaced to users |
| High viewport count, name suggests transient state (e.g., spinner) | Pull 3 sessions via `get_sessions` and review event timeline for viewport duration | If evidence of >8s visible duration: friction. If brief and contextually appropriate: note and move on |
| High viewport count, name suggests error state | Significant — users are seeing error conditions frequently | Flag with volume and pull sessions |

### 3a-S. Silent Issue Impact Gate (error signals only)

Before passing any error-type signal to Phase 5, determine whether it has a confirmed attached impact signal. This gate prevents console errors, network errors, and uncaught exceptions from being written as findings, hotspot titles, or urgency language when users were unaffected.

**Applies to:** console errors, network errors, and uncaught exceptions collected in 3a. Does not apply to rage clicks, dead clicks, error clicks, abandoned forms, web vitals, or cursor thrashing — those signals are inherently behavioral.

#### Step 1 — Inventory only (counts permitted, impact language forbidden)

The error counts from `discover_groups` are inventory — they tell you the error exists and at what volume. Do not narrate these counts as user harm yet. Do not use words like "users are blocked," "users cannot," or "this issue affects" at this stage.

#### Step 2 — Build the attached signal check

For each error signal, determine whether an attached impact signal exists on the same page. An attached signal is one of:

- **Frustration click:** rage click, dead click, or error click occurring in sessions that also contain this error
- **Exit/bounce spike:** pages where this error fires showing a materially higher exit rate or bounce rate than the page's own baseline
- **Funnel failure:** a measurable drop in funnel completion for sessions containing this error vs. sessions without it

Build a segment or metric that captures co-occurrence: sessions where this specific error AND at least one attached signal are both present. Compute it.

**If the co-occurrence count is zero or negligible:** classify as **Silent / Non-Impactful**.
- Allowed: appendix, "telemetry only," Engineering Notes callout, engineering hygiene list.
- Forbidden: hotspot finding, deck title, "issue," "users are blocked," urgency language of any kind.
- Stop. Do not proceed to session review for this error.

**If co-occurrence exists:** proceed to Step 3.

#### Step 3 — Session review from the attached signal pool

Sample **≥5 sessions from the attached signal segment** — sessions where the error AND the impact signal are both confirmed present. Do not sample randomly from the error segment.

For each session, run this sequence in order:

1. `session_open(device_id, session_id)` — note the error timestamp from the event summary
2. `session_screenshot(client_id, timestamp=error_ts)` — capture the UI state at the moment the error fires
3. `session_get_a11y_tree(client_id, page_id, timestamp=error_ts)` and/or `session_diff(client_id, page_id, from_ts=error_ts, to_ts=error_ts+10000)` — confirm the UI actually failed or changed in response
4. `session_close(client_id)`

**If you cannot reach 5 sessions from the attached signal pool:** you do not have a validated insight for this error. Do not embellish. Classify as non-impactful and route to Engineering Notes.

**If you complete 5 attached sessions:** classify as **Impactful Error** and carry forward to Phase 5 with full scoring. Note the attached signal type and co-occurrence count.

---

### 3d. Web Vitals

Build metrics for web vitals and compute at the 75th percentile (p75 — Google's standard measurement point). Apply Google's prescribed thresholds:

| Vital | Good | Needs Improvement | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint) | < 2.5s | 2.5s – 4.0s | > 4.0s |
| INP (Interaction to Next Paint) | < 200ms | 200ms – 500ms | > 500ms |
| CLS (Cumulative Layout Shift) | < 0.1 | 0.1 – 0.25 | > 0.25 |
| FCP (First Contentful Paint) | < 1.8s | 1.8s – 3.0s | > 3.0s |
| TTFB (Time to First Byte) | < 800ms | 800ms – 1.8s | > 1.8s |

Web vitals in the "Poor" range enter the prioritization queue. "Needs Improvement" is noted in the TLDR. Web vitals always appear as global KPIs regardless of score.

---

## Phase 4 — Revenue Path Analysis

### 4a. Conversion Volume

Build a metric: count of Revenue Events (or equivalent conversion anchor), single number. Compute. Record as a key TLDR KPI. Divide by total sessions for a conversion rate.

### 4b. Friction on the Conversion Path

For every issue found in Phase 3, check: does it occur on a page that's part of the primary conversion funnel? Issues on conversion-path pages receive a location multiplier in Phase 5 scoring — they directly cost revenue.

### 4c. Exit Page Friction

For pages identified as session-exit pages under duress (users leaving without converting): any frustration or error signal concentrated there is high-priority. These are the last point of contact before abandonment. Surface them explicitly.

---

## Phase 5 — Prioritization & Scoring

Score every discovered issue:

```
Priority Score = Affected Users × Severity Weight × Location Multiplier × Trend Modifier
```

**Pre-scoring gate:** Error signals classified as **Silent Issues** in Phase 3a-S are excluded from this table entirely. Only carry-forward (impactful) errors are scored here. A high-volume silent error does not become a Critical Issue — it goes to Engineering Notes.

**Severity Weights:**
| Signal | Weight |
|---|---|
| Rage click, Error click | 1.5 |
| Uncaught exception, Network error (blocking) — impactful only | 1.4 |
| Abandoned form, App crash | 1.4 |
| Web vital in "Poor" range | 1.3 |
| Refreshed page, Cursor thrashing | 1.3 |
| Watched element: high viewport time (stuck) | 1.3 |
| Dead click | 1.2 (UX confusion — not breakage, but real friction) |
| Watched element: DOM but never in viewport | 1.2 |
| Console error — impactful only | 1.1 |
| Web vital in "Needs Improvement" | 1.1 |

**Location Multipliers:**
| Location | Multiplier |
|---|---|
| On the Revenue Event conversion path | × 2.0 |
| On a session exit page (non-converting) | × 1.7 |
| On a top-5 trafficked page | × 1.4 |
| Elsewhere | × 1.0 |

**Trend Modifier:** If `discover_groups` with `compare_to_previous` flagged this issue as worsening, apply × 1.3.

**StoryAI Opportunity alignment:** Any issue matching a pre-ranked Opportunity is automatically elevated to the top of its tier. Note the Opportunity in the write-up.

**Rank all issues by score:**
- Top 3 = **Critical Issues** (full treatment)
- Next 5 = **Notable Issues** (moderate treatment)
- Everything else = **Full Findings Table**

**On statistical context:** Include distributions, histograms, or standard deviation only when they communicate something actionable — e.g., a bimodal LCP distribution suggests two distinct populations with different experiences, or a high std dev on error rates suggests intermittent vs. systemic issues. Never add stats for completeness. A single clear sentence with the number is usually more powerful than a histogram.

---

## Phase 6 — Session Pull

For each of the top 8 issues (top 3 + next 5), pull **3 session links**:

- Issue from `discover_groups`: use `get_sessions_for_opportunity` with the `default_metric_id` and `group_id`.
- Issue from a custom metric: use `get_sessions` with the `metric_id`.
- Issue from a segment: use `get_sessions` with the `segment_id`.

These session URLs are the evidence layer of the report — they let the customer's team watch exactly what users experienced.

### 6b. GIF-Worthy Session Hunt

After pulling per-issue session links, find a small set of sessions with extreme frustration density — the sessions that would make a compelling GIF or clip for an insights deck presentation.

**Rail A gate:** Burst frequency alone does not make an error impactful. Before including any error-type session in this section, confirm that the error passed Phase 3a-S as an Impactful Error. A silent error with a burst pattern is still a silent error — burst frequency must not resurrect it.

**Query 1 — Frustration burst:** Pull sessions where the user rage-clicked, dead-clicked, or error-clicked 5 or more times. Use `get_sessions` against a segment or metric that captures high-frequency click frustration on a short time window. If no such metric exists in the semantic layer, build one:
- Event: rage click OR dead click OR error click
- Time window: any 5-second span within session
- Threshold: 5 or more events

**Query 2 — Error storm (impactful errors only):** Pull sessions where an error type that passed Phase 3a-S as impactful fired 5 or more times within any 10-second window. Do not run this query for errors classified as silent.

For each query, pull up to 5 candidate sessions. Open each and scan the event timeline (`get_session_events`). Close each session after reviewing. Select the **1–2 sessions** that are most visually dramatic — highest frustration density, clearest sequence, most representative.

These illustrate findings already ranked and validated. Record the session URL and a one-line description of what makes the clip compelling.

Run `/generate-behavior-proof-clip` with the session URL and the anchor event (the rage click, dead click, or error click that made this session stand out). The clip skill handles frame extraction, render, and placement — Phase 6b stays the hunt; the clip skill is the render.

Include in the **field guide's Session Evidence section** under a "Highlight Clips" heading. Do not include in the customer-facing `index.html` unless the analyst explicitly requests it.

---

## Visual Pre-flight (Required Before HTML Generation)

Before writing any HTML section that includes a chart, KPI tile, or visualization:

1. Read `_component-index.md` — find the row matching each visual element needed.
2. Read the snippet file(s) from `_snippets/` for each matched row.
3. Adapt each snippet with real data. Do not invent CSS classes or inline styles.

If no row matches: use prose-only components (`.callout`, `.detail-item`, section headers) — no custom CSS for data visualization.

For statistical charts: only include if the chart answers a question funnel bars or metric tiles cannot answer on their own. Every stat component must be immediately followed by a `.stat-narrative` block.

---

## Phase 7 — Report Generation

Generate the report as a self-contained HTML file using the Fullstory Field Playbooks design system. Use `_starter.html` as the base for one-pager format; adapt to a multi-slide layout for deck format.

**Header personalization:**
- Customer logo (loaded from the path or URL provided)
- Customer name + "DX Hotspot Snapshot"
- Subtitle: "Prepared by Fullstory | [Time Window] | [Generation Date]"

**Tone rules:**
- Business audience: no product jargon. "Users repeatedly clicked a button that doesn't respond" not "dead click on `.cta-btn`". Translate every technical finding into a user experience statement. Reference APIs by feature name only — "the loyalty balance API" not "`/api/trpc/loyalty.balance`". API endpoint paths belong in Engineering Notes callouts (`.callout.engineering`), not customer-facing prose.
- Technical audience: include element selectors, error text verbatim, page-level specifics. Engineers need enough to reproduce and fix.

---

## Report Structure

### Section 1: TLDR

**Global KPI tiles:**
- Total sessions
- Unique users
- Revenue Events completed + conversion rate (if applicable)
- LCP, CLS, INP scores with Good / Needs Improvement / Poor status

**Narrative Brief (3–5 sentences):**
An elevator pitch on the 2–3 main themes of this report. What are the dominant patterns? Is this primarily an error problem, a UX confusion problem, or a performance problem? What is the business consequence? Write this for a VP who has 20 seconds — make every sentence count.

---

### Section 2: Top 3 Critical Issues

For each critical issue, write a full detail block:

```
[Issue Title] — [Signal Type] — [Page]

WHAT'S HAPPENING
[1–2 sentences describing the user experience in plain language — what users encounter,
not what the data says.]

BUSINESS IMPACT
[Quantify: X users affected in the past [time window], Y% of sessions on this page,
Z% of those users did not complete [Revenue Event].
If quantification is not possible: X total occurrences involving N unique users.]

WHY IT MATTERS
[Apply qualitative reasoning. Dead clicks = users believe something is interactive but it
isn't — unmet affordance expectation. Back-navigation within seconds = confusion or
expectation mismatch. Spinner visible >8s = users are waiting and likely to abandon.
High refresh rate = users coping with a page that isn't loading correctly. Connect the
behavior to the business consequence.]

SESSION EVIDENCE
• [Session URL 1]
• [Session URL 2]
• [Session URL 3]

[If trending worse: ⚠️ Trending X% worse vs. prior period]
[If Opportunity match: output `<span class="storyai-badge">★ StoryAI Confirmed</span>` as actual HTML immediately after the issue title — never as plain text]
```

---

### Section 3: Next 5 Notable Issues

For each, a shorter block:
- 1 sentence: what's happening, in plain language
- Affected users / occurrence count
- 1 sentence: business implication
- 3 session links

---

### Section 4: Full Findings Table

All remaining issues in a table:

| Issue | Signal Type | Page | Affected Users | Occurrences | Priority Score |

---

### Footer

- Time window covered, analysis date, data source: Fullstory
- If unnamed page volume was significant: "Some pages on this site don't have labels set up in Fullstory yet, so they were excluded from the traffic flow analysis. Adding labels to more pages will improve the detail of future reports."

---

## Qualitative Reasoning Reference

Numbers alone are not enough. Always reason about what the signal means for the human experiencing it.

| Signal | What it usually means | How to frame it |
|---|---|---|
| Dead click | Users believe this element is interactive — it isn't | Unmet affordance. UX confusion, not a bug |
| Rage click | Extreme frustration with an unresponsive element | Could be breakage or severe UX friction |
| Error click | Users clicking on error states — trying to dismiss or interact | Users are encountering and reacting to error conditions |
| Cursor thrashing | Disoriented user scanning for something they can't find | Likely navigation confusion or unclear information hierarchy |
| Back-navigation within 3s | Page did not meet the user's expectation | Mismatch between what the user anticipated and what they found |
| High refresh rate | Page isn't loading correctly, or users expect live data | Determine whether refresh is intentional behavior or a coping mechanism |
| Abandoned form | Friction in the form flow | Investigate which field is last touched before abandonment |
| DOM element never in viewport | Tracked but users never see it | Layout bug, off-screen render, or broken conditional |
| Element in viewport >8s (spinner/loader) | Users are stuck waiting | Performance or API issue causing visible, sustained delay |
| Pinch-to-zoom (mobile) | Content isn't readable at native scale | Mobile layout or font-size issue |
| Force restart / Low memory (mobile) | App stability issue | May indicate memory leak or resource-heavy page |

---

---

## Phase 8 — Field Guide Generation

Generate a companion field guide using `_field-guide-starter.html` as the base. The field guide is **internal only** — never share it with the customer.

Set `data-sync-pair="[customer-slug]-dx-hotspot-snapshot-[YYYY-MM]"` on `<html>`.

### Launch Callout (required)

Immediately after the topbar (before the hero), include a `.launch-callout` block:

```html
<div class="launch-callout">
  <div class="launch-callout-text">
    <strong>Open the report alongside this guide</strong> — the field guide will track automatically as you scroll through it with the customer.
  </div>
  <a href="../index.html" target="_blank" class="launch-btn">Open Report →</a>
</div>
```

This is the first thing the analyst sees when the field guide opens. The `href="../index.html"` links directly to the deliverable — required for local file:// serving.

### Field Guide Structure

**Section 1: Delivery Script** (always first)

A numbered, step-by-step script for presenting the report to the customer. Include:
- How to open the conversation (1–2 sentences to set context before sharing the screen)
- One step per major report section: what to say, what to watch for, when to pause
- How to close: recommended next steps to propose at the end of the call

Set `data-sync-section="delivery-script"` on this section.

**Section 2: Presenter Notes**

Per-section bullets aligned to the report. For each of the Critical and Notable Issues, include:
- The plain-language translation of the finding (what to say if the customer asks "what does this mean?")
- The business impact framing (connect to revenue, conversion, or retention)
- One sentence on what a fix would look like (empowers the customer's team to act)

Set `data-sync-section="presenter-notes"` on this section.

**Section 3: Discovery Questions**

5–8 follow-up questions the analyst can ask to deepen the conversation. Focus on:
- Questions that surface whether the customer already knows about the issues
- Questions that connect friction to business priorities the customer has stated
- Questions that identify who owns the fix (engineering, product, design)

Set `data-sync-section="discovery"` on this section.

**Section 4: Session Evidence**

Quick-reference list of all session links from the report, organized by issue. Format:
```
[Issue title]
  • [Session URL 1]
  • [Session URL 2]
  • [Session URL 3]
```

Set `data-sync-section="session-evidence"` on this section.

### Sync the Report

The main report (`index.html`) must also have matching `data-sync-section` attributes on its sections:
- TLDR section → `data-sync-section="tldr"`
- Critical Issues section → `data-sync-section="critical-issues"`
- Notable Issues section → `data-sync-section="notable-issues"`
- Full Findings Table → `data-sync-section="findings-table"`

These don't need exact counterparts in the field guide — unmatched keys are silently ignored. The field guide sync keys (delivery-script, presenter-notes, discovery, session-evidence) drive the field guide's own navigation.

---

## Output

Create the following directories:

```
./clients/[customer-slug]/dx-hotspot-snapshot-[YYYY-MM]/
./clients/[customer-slug]/dx-hotspot-snapshot-[YYYY-MM]/field-guide/
```

Save files as:
- `./clients/[customer-slug]/dx-hotspot-snapshot-[YYYY-MM]/index.html`
- `./clients/[customer-slug]/dx-hotspot-snapshot-[YYYY-MM]/field-guide/index.html`

Example paths for Acme Corp, July 2026:
- `./clients/acme-corp/dx-hotspot-snapshot-2026-07/index.html`
- `./clients/acme-corp/dx-hotspot-snapshot-2026-07/field-guide/index.html`

Update `MEMORY.md` in the workspace root by adding under the customer's heading:
```
- [YYYY-MM-DD] DX Hotspot Snapshot: dx-hotspot-snapshot-[YYYY-MM]
```

Open the field guide automatically:

```bash
open ./clients/[customer-slug]/dx-hotspot-snapshot-[YYYY-MM]/field-guide/index.html
```

Then report to the analyst:
- How many Critical Issues were identified
- How many Notable Issues
- Total issues in the Full Findings Table
- Whether Fullstory's AI-surfaced findings (StoryAI) were available and matched this analysis — and if yes, which issues were independently confirmed
- Whether a specific conversion event was found in the org, or whether you used the goal the analyst identified
- One sentence on the dominant theme (performance problem, UX confusion, or error breakage)
- Reminder: click "Open Report →" in the field guide to open the deliverable alongside it
