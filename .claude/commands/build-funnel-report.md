# Build Funnel Report

Build a Fullstory Funnel Analysis Report for a customer account — a data-driven, executive-ready analysis of where users are dropping out of a critical flow, what's causing the drop-off, and what to do about it. Delivered as a self-contained HTML one-pager with a companion field guide.

## When to invoke

Use this skill when a analyst asks to:
- Analyze a funnel or conversion flow for a customer
- Find out where users are dropping off in a checkout, signup, or onboarding flow
- Build a drop-off analysis report
- Identify what happens to users who don't complete a key flow

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

Proceed directly to Phase 0 without telling the analyst.

---

## Phase 0 — Intake

Ask all of the following in a single message:

```
Before I begin, I need a few things:

1. CUSTOMER NAME
   What is the name of the customer this report is for?

2. CUSTOMER LOGO
   Where can I find the customer's logo?
   - A direct URL to the logo file, OR
   - A local file path on your machine, OR
   - "Skip" to use text-only branding

3. FUNNEL
   What flow do we want to analyze?
   - I'll check if a funnel already exists in Fullstory — OR —
   - Describe the steps you want to measure (e.g., "Homepage → Product Page → Cart → Checkout → Confirmation")

4. TIME WINDOW
   What time period should this cover?
   Default is last 30 days — specify if different.

5. AUDIENCE
   BUSINESS (executives, VPs) or TECHNICAL (engineers, product managers)?
```

---

## Phase 1 — Funnel Discovery

### 1a. Check for Existing Funnels

Call `get_managed_funnels` only if it is offered. If it is not offered, say once, in plain words, that this org does not have the StoryAI Opportunity tools, skip this step and go to 1b. Otherwise present any existing funnels to the analyst:

> I found [N] funnels already set up in Fullstory:
> [list funnel names]
>
> Should I use one of these, or build a new funnel from the steps you described?

If the analyst chooses an existing funnel, proceed with that `funnel_id`. If they want a new funnel, proceed to 1b.

### 1b. Build the Funnel (if needed)

Call `build_funnel` with the steps the analyst described. Present the funnel definition back to the analyst before proceeding:

> Here's the funnel I'll analyze:
> Step 1: [description]
> Step 2: [description]
> ...
> Confirm, or tell me what to adjust.

Wait for confirmation. Then proceed.

---

## Phase 2 — Compute Funnel

Call `compute_funnel` with the `funnel_id`. Record:

- Total users entering the funnel (Step 1 count)
- Per-step counts and conversion rates from the previous step
- Per-step conversion rates from Step 1 (overall through-rate)
- **Drop-off volume** per step: users who completed step N but not step N+1
- **The biggest drop-off step**: the single step with the highest absolute drop-off count

Compute the **overall funnel conversion rate**: Step-final count ÷ Step-1 count.

---

## Phase 3 — Drop-Off Analysis

For the **top 3 steps by drop-off volume**, do the following in parallel:

### 3a. Drop-Off Session Pull

Call `get_funnel_sessions` for each drop-off step with `did_not_complete: true`. Pull 5 sessions per step. These are users who made it to that step but did not continue.

Review the session evidence for patterns: what were users doing just before they left? Were there errors, hesitation, or dead ends?

### 3b. Friction at the Drop-Off Page

For the page associated with each top drop-off step, call `discover_groups` scoped to:
- `funnel_id` — scoped to the funnel
- `dropout_at_step` — the step index (0-based) of the drop-off step

This surfaces frustration and error signals concentrated among users who dropped out at that step specifically — not all funnel users.

Look for: rage clicks, dead clicks, error clicks, abandoned forms, console errors, network errors, high refresh rates.

### 3c. StoryAI Opportunities for Funnel

Call `get_opportunities` with `funnel_id` only if it is offered. These are pre-ranked opportunities Fullstory's AI has identified as impacting this specific funnel. Any opportunities here are automatically elevated in the report. If it is not offered, say once, in plain words, that this org does not have the StoryAI Opportunity tools and the analysis continues without StoryAI Confirmed badges. Never present a finding as StoryAI Confirmed without a real `get_opportunities` result, never stall, never report a dead connection, and never invent a result.

---

## Phase 4 — Comparison (Completers vs. Drop-Offs)

Build two segments:
- **Completers**: users who completed the full funnel
- **Drop-offs at the biggest step**: users who reached the top drop-off step but did not complete it

For each segment, compute:
- A metric: page views grouped by page (top_n) — what pages did completers visit vs. drop-offs?
- Web vitals (LCP, INP, CLS) at p75 — were drop-offs on slower pages?

This surfaces whether the drop-off is a performance problem, a navigation problem, or a content problem.

---

## Phase 5 — Prioritization & Scoring

Score every friction signal found in Phase 3b using the same scoring model defined in CLAUDE.md:

```
Priority Score = Affected Users × Severity Weight × Location Multiplier × Trend Modifier
```

**Severity Weights:** rage click / error click = 1.5 | uncaught exception / network error = 1.4 | abandoned form = 1.4 | web vital Poor = 1.3 | refreshed page = 1.3 | dead click = 1.2 | console error = 1.1

**Location Multipliers:** all drop-off pages are on the conversion path → base × 2.0. Step with highest absolute drop-off → additional × 1.3.

Rank all issues. Top 3 = Critical; next 3 = Notable.

---

## Visual Pre-flight (Required Before HTML Generation)

Before writing any HTML section that includes a chart, KPI tile, or visualization:

1. Read `_component-index.md` — find the row matching each visual element needed.
2. Read the snippet file(s) from `_snippets/` for each matched row.
3. Adapt each snippet with real data. Do not invent CSS classes or inline styles.

If no row matches: use prose-only components (`.callout`, `.detail-item`, section headers) — no custom CSS for data visualization.

For statistical charts: only include if the chart answers a question funnel bars or metric tiles cannot answer on their own. Every stat component must be immediately followed by a `.stat-narrative` block.

---

## Phase 6 — Report Generation

Generate a self-contained HTML report using `_starter.html` as the base.

**Header personalization:**
- Customer logo + name
- "[Customer] Funnel Drop-Off Analysis"
- Subtitle: "Prepared by Fullstory | [Time Window] | [Generation Date]"

**Tone rules:** business audience = plain language, user impact, no jargon; technical audience = element selectors, error text, specifics.

Set `data-sync-pair="[customer-slug]-funnel-report-[YYYY-MM]"` on `<html>`.

### Report Structure

**Section 1: Funnel Overview** (`data-sync-section="funnel-overview"`)

Funnel visualization — a step-by-step waterfall showing:
- Step name, entry count, drop-off count, through-rate, overall rate
- Highlight the biggest drop-off step visually (amber or red)
- Overall funnel conversion rate as a headline KPI

**Section 2: TLDR** (`data-sync-section="tldr"`)

3–5 sentence executive brief:
- What is this funnel and why does it matter?
- Where is the biggest problem?
- What is the business consequence of the current drop-off rate?
- Is it getting better or worse?

**Section 3: Top Drop-Off Steps** (`data-sync-section="drop-off-steps"`)

For each of the top 3 drop-off steps, write a full detail block:

```
[Step Name] — [N] users dropped off here ([X]% of step entrants)

WHAT'S HAPPENING
[What are these users experiencing at this step? What are they failing to do?]

FRICTION SIGNALS
[List the top issues found at this step from Phase 3b: signal type, affected users,
occurrence count. For each, 1 sentence in plain language.]

SESSION EVIDENCE
• [Session URL 1 — from the drop-off session pull]
• [Session URL 2]
• [Session URL 3]

[If StoryAI Opportunity match: output `<span class="storyai-badge">★ StoryAI Confirmed</span>` as actual HTML immediately after the step name heading — never as plain text]
```

**Section 4: Completers vs. Drop-Offs** (`data-sync-section="comparison"`)

A side-by-side comparison showing:
- Navigation paths: where completers went vs. where drop-offs went
- Web vital comparison: LCP / INP / CLS for each segment
- Key takeaway: is this a speed problem, a navigation problem, or a friction problem?

**Section 5: Full Findings Table** (`data-sync-section="findings-table"`)

All friction signals in a table: Issue | Signal Type | Step | Affected Users | Priority Score

**Footer:** time window, data source, funnel ID for reference.

---

## Phase 7 — Field Guide Generation

Generate a companion field guide using `_field-guide-starter.html` as the base. Internal only — never share.

Set `data-sync-pair="[customer-slug]-funnel-report-[YYYY-MM]"` on `<html>`.

**Launch callout** (immediately after topbar, before hero):
```html
<div class="launch-callout">
  <div class="launch-callout-text">
    <strong>Open the report alongside this guide</strong> — the field guide will track automatically as you scroll through it with the customer.
  </div>
  <a href="../index.html" target="_blank" class="launch-btn">Open Report →</a>
</div>
```

### Field Guide Structure

**Section 1: Delivery Script** (`data-sync-section="delivery-script"`)

Numbered presentation steps:
- Opening: how to frame the funnel before showing the numbers
- Step-by-step walk through the waterfall chart
- How to present each drop-off finding
- How to close: what to propose as next steps

**Section 2: Presenter Notes** (`data-sync-section="presenter-notes"`)

Per drop-off step:
- Plain-language translation of each friction signal
- Business impact framing (connect to revenue or retention)
- One sentence on what a fix would look like

**Section 3: Discovery Questions** (`data-sync-section="discovery"`)

5–8 questions:
- Does the team know about these drop-off rates?
- Have they investigated the top drop-off step before?
- What do they think is causing the drop-off?
- Who owns the pages at the top drop-off step?
- Is this funnel used in any business reporting currently?

**Section 4: Session Evidence** (`data-sync-section="session-evidence"`)

All session links organized by step:
```
[Step Name]
  • [Session URL 1]
  • [Session URL 2]
  • [Session URL 3]
```

---

## Output

Create directories:
```
./clients/[customer-slug]/funnel-report-[YYYY-MM]/
./clients/[customer-slug]/funnel-report-[YYYY-MM]/field-guide/
```

Save files:
- `./clients/[customer-slug]/funnel-report-[YYYY-MM]/index.html`
- `./clients/[customer-slug]/funnel-report-[YYYY-MM]/field-guide/index.html`

Update `MEMORY.md` by adding under the customer's heading:
```
- [YYYY-MM-DD] Funnel Report: funnel-report-[YYYY-MM]
```

Open the field guide automatically:
```bash
open ./clients/[customer-slug]/funnel-report-[YYYY-MM]/field-guide/index.html
```

Report to the analyst:
- Funnel name and time window
- Overall conversion rate
- Top drop-off step and its drop-off rate
- How many Critical Issues were found at drop-off points
- Whether StoryAI Opportunities data was incorporated
- Reminder: click "Open Report →" in the field guide to view the deliverable alongside it
