# Build Cohort Comparison Report

Build a Fullstory Cohort Comparison Report — a side-by-side analysis of how two or more distinct user groups experience a digital property differently. Surfaces where experiences diverge, which group struggles more, and what's driving the difference. Delivered as a self-contained HTML report with a companion field guide.

## When to invoke

Use this skill when a analyst asks to:
- Compare how different user groups experience the site (mobile vs. desktop, new vs. returning, paid vs. free, region A vs. region B)
- Understand why one segment converts better than another
- Find out whether a known issue affects all users or just a specific group
- Build a report showing differential experience across user cohorts

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
   - A direct URL, a local file path, or "Skip" for text-only branding.

3. THE COMPARISON QUESTION
   What are we comparing? Describe the two (or three) groups.
   Examples:
   - "Mobile users vs. desktop users"
   - "Users who saw the error vs. users who didn't"
   - "Users who came from paid ads vs. organic"
   - "Returning customers vs. first-time visitors"
   - "Users in the US vs. users in the UK"

4. THE NORTH STAR METRIC
   What is the most important outcome for this customer — the action that represents
   success? (e.g., completed checkout, submitted a form, started a free trial)
   This is what we'll measure across all cohorts.

5. TIME WINDOW
   What time period should this cover? Default is last 30 days.

6. AUDIENCE
   BUSINESS (executives, VPs) or TECHNICAL (engineers, product managers)?
```

---

## Phase 1 — Cohort Definition & Segment Building

Based on the analyst's answer to question 3, work out the segment definitions for each cohort.

### 1a. Check for Named Context

Call `discover_org_context` with the key terms from the analyst's cohort description (e.g., "mobile", "error", "paid", "returning"). Look for named pages, defined events, or custom variables that can anchor the segments precisely.

### 1b. Define and Build Segments

For each cohort (2 or 3 maximum), define the segment in plain language, confirm with the analyst, then build it:

> Here's how I'll define your cohorts:
>
> Cohort A — [Name]: [plain language definition]
> Cohort B — [Name]: [plain language definition]
>
> Does this match what you had in mind?

After confirmation, call `build_segment` for each cohort in parallel.

**Common cohort patterns and how to build them:**

| analyst says | Segment approach |
|---|---|
| Mobile vs. desktop | Device type filter — "mobile" or "desktop" in the segment |
| New vs. returning | Session count: first session ever vs. 2+ prior sessions |
| Saw an error vs. didn't | Behavioral: included/excluded a console error or crash event |
| Paid vs. organic | Source/medium custom variable if tagged; or URL parameter filter |
| Converted vs. didn't | Behavioral: included/excluded the Revenue Event or conversion page visit |
| Geographic | Location filter by country or region |

If the cohort cannot be built from available data, tell the analyst clearly and suggest the closest alternative.

---

## Phase 2 — North Star Metric Across Cohorts

### 2a. Conversion Rate per Cohort

Call `discover_org_context` with the North Star terms the analyst provided. Find the matching defined event or page visit that represents the conversion.

Build a metric: count of the conversion event, single number. Attach each cohort segment in turn and compute:

- Cohort A conversion rate: [conversion count] ÷ [total sessions in segment]
- Cohort B conversion rate: same
- (Cohort C if applicable)

**The conversion rate gap is the headline of this report.** If one cohort converts at half the rate of another, that is the lead finding.

### 2b. Session Volume per Cohort

Compute total sessions and unique users per cohort. Present as context — a group representing 2% of users doesn't carry the same urgency as one representing 40%.

---

## Phase 3 — Friction Signal Comparison

### 3a. StoryAI Pre-Check

Before running `discover_groups`, call `get_opportunities` for each cohort's `segment_id` in parallel, only if it is offered. If it is not offered, say once, in plain words, that this org does not have the StoryAI Opportunity tools and the analysis continues without StoryAI Confirmed badges. Never present a finding as StoryAI Confirmed without a real `get_opportunities` result, never stall, never report a dead connection, and never invent a result. When it is offered: Note which opportunities Fullstory's AI has pre-ranked for each cohort. Any friction signal found in Phase 3b that matches a pre-ranked Opportunity must be marked with `<span class="storyai-badge">★ StoryAI Confirmed</span>` in the report HTML.

### 3b. Discover Friction Signals

For each cohort, call `discover_groups` scoped to the cohort's `segment_id`. Collect the top frustration and error groups for each:

- Dead clicks by element
- Rage clicks by element
- Error clicks by element
- Abandoned forms by page
- Console errors by text
- Network errors by path
- Refreshed pages by page
- Cursor thrashing (build a separate `top_n` metric per cohort)

Run all cohorts in parallel.

**Then compare:**

For each signal type, compare:
1. Is this issue present in all cohorts, or concentrated in one?
2. How different is the rate across cohorts? (same absolute counts mean different rates if cohort sizes differ)
3. Are there issues that appear in Cohort A but not Cohort B (or vice versa)? These are the most actionable findings — they're definitively exclusive to a group.

---

## Phase 4 — Web Vitals Comparison

Build web vitals metrics (LCP, INP, CLS, FCP, TTFB) at p75 for each cohort segment in parallel. Compare:

| Vital | Cohort A | Cohort B | Delta | Status |
|---|---|---|---|---|

Apply Google's thresholds: LCP < 2.5s Good; INP < 200ms Good; CLS < 0.1 Good; FCP < 1.8s Good; TTFB < 800ms Good.

A large performance gap between cohorts (e.g., mobile p75 LCP = 4.2s vs. desktop p75 LCP = 1.8s) is a high-priority finding and almost always actionable by the engineering team.

---

## Phase 5 — Journey Comparison

For each cohort, build a metric: page views grouped by page (top_n). Compare the top 5 pages per cohort.

Look for:
- **Diverging paths**: cohorts that go to different pages after a shared starting point
- **Dead ends**: pages where one cohort exits at high rate vs. the other
- **Friction concentration**: a page that appears in one cohort's top-5 but not the other's, especially if that cohort has worse conversion

---

## Phase 6 — Session Evidence

For the top 3 divergent findings (issues that are present in one cohort and absent or minimal in the other), pull 3 session links per cohort showing the contrast:

- 3 sessions from the struggling cohort showing the problem
- 3 sessions from the healthy cohort showing the absence of the same problem (or a clean path through)

Use `get_sessions` with each cohort's `segment_id`.

This contrast is the most compelling evidence — watching the same step go wrong for one group and smoothly for another is immediately actionable.

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

Generate a self-contained HTML report using `_starter.html` as the base.

**Header personalization:**
- Customer logo + name
- "[Customer] Cohort Comparison: [Cohort A] vs. [Cohort B]"
- Subtitle: "Prepared by Fullstory | [Time Window] | [Generation Date]"

Set `data-sync-pair="[customer-slug]-cohort-[YYYY-MM]"` on `<html>`.

**Tone rules:** business audience = no jargon, user impact in plain language; technical audience = specific signals, element selectors, error text.

### Report Structure

**Section 1: The Headline Gap** (`data-sync-section="headline"`)

The single most important number: the conversion rate difference between cohorts. State it as a headline KPI tile for each cohort, with a third tile showing the gap.

3-sentence narrative brief: what is this comparison, what is the headline finding, and what does it mean for the business?

**Section 2: Cohort Profiles** (`data-sync-section="profiles"`)

One card per cohort showing: user count, session count, conversion rate, and 2–3 distinguishing characteristics (e.g., top pages, device split, primary entry point).

**Section 3: Friction Comparison** (`data-sync-section="friction"`)

A side-by-side comparison of frustration signals. For each signal type:
- Which cohort has it worse and by how much
- Whether it appears exclusively in one cohort (flag this prominently)
- Qualitative interpretation: what does this mean for that user group?

Issues exclusive to one cohort get a dedicated full treatment block (same format as Critical Issues in the DX Hotspot Snapshot). Issues present in both but worse in one get a comparative callout. Any issue matching a StoryAI Opportunity from Phase 3a: output `<span class="storyai-badge">★ StoryAI Confirmed</span>` as actual HTML immediately after the issue title — never as plain text.

**Section 4: Performance Gap** (`data-sync-section="performance"`)

Side-by-side web vitals table with color-coded status (Good / Needs Improvement / Poor) per cohort. If a vital is Good for one cohort and Poor for another, flag it as a differential performance problem.

**Section 5: Journey Divergence** (`data-sync-section="journey"`)

Side-by-side top-5 page paths per cohort with annotation on where they diverge and what that means.

**Section 6: Session Evidence** (`data-sync-section="session-evidence"`)

For each top finding: 3 sessions from the struggling cohort + 3 sessions from the healthy cohort, clearly labeled.

**Footer:** time window, data source, cohort definitions (plain language) for reference.

---

## Phase 8 — Field Guide Generation

Generate a companion field guide using `_field-guide-starter.html` as the base. Internal only — never share.

Set `data-sync-pair="[customer-slug]-cohort-[YYYY-MM]"` on `<html>`.

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
- How to open the conversation (set up why comparing these groups matters)
- How to present the headline gap (pause here — let the number land)
- Walk through friction comparison: emphasize issues exclusive to one cohort
- Performance gap: connect to user experience, not just numbers
- How to close: recommend targeted fixes for the struggling cohort

**Section 2: Presenter Notes** (`data-sync-section="presenter-notes"`)

Per major finding:
- Plain-language translation
- Business impact framing (what does this cost in users, conversions, or revenue?)
- One sentence on what a fix looks like and who owns it

**Section 3: Discovery Questions** (`data-sync-section="discovery"`)

5–8 questions:
- Is the customer aware of this difference between their user groups?
- Have they tried to address the gap before? What happened?
- Does the struggling cohort represent a high-priority segment for the business?
- Who owns the pages or features where the divergence is worst?
- Is this cohort tracked separately in any other business reporting?
- What would it mean for the business if both cohorts converted at the rate of the healthier one?

**Section 4: Session Evidence** (`data-sync-section="session-evidence"`)

All session links organized by finding and cohort:
```
[Finding name]
  Cohort A ([name]):
    • [Session URL 1]
    • [Session URL 2]
    • [Session URL 3]
  Cohort B ([name]):
    • [Session URL 1]
    • [Session URL 2]
    • [Session URL 3]
```

---

## Output

Create directories:
```
./clients/[customer-slug]/cohort-comparison-[YYYY-MM]/
./clients/[customer-slug]/cohort-comparison-[YYYY-MM]/field-guide/
```

Save files:
- `./clients/[customer-slug]/cohort-comparison-[YYYY-MM]/index.html`
- `./clients/[customer-slug]/cohort-comparison-[YYYY-MM]/field-guide/index.html`

Update `MEMORY.md` by adding under the customer's heading:
```
- [YYYY-MM-DD] Cohort Comparison ([Cohort A] vs. [Cohort B]): cohort-comparison-[YYYY-MM]
```

Open the field guide automatically:
```bash
open ./clients/[customer-slug]/cohort-comparison-[YYYY-MM]/field-guide/index.html
```

Report to the analyst:
- Cohort names and sizes
- The headline conversion rate gap
- Number of friction signals exclusive to one cohort (most actionable findings)
- Any significant performance gaps
- Reminder: click "Open Report →" in the field guide to view the deliverable alongside it
