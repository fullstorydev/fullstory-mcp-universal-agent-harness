# Build Org Context

Build a complete digital experience context bundle for a Fullstory org. Produces five structured markdown context files, a replayable job log, and a multi-tab HTML context report — all built from live Fullstory MCP data. The bundle is designed to give any new AE, CSE, SE, or PS immediate situational awareness of the org's digital experience without needing to run a single query themselves.

---

## When to invoke

Use this skill when anyone asks to:
- Build org context for a new or existing customer
- Get up to speed on a customer's digital experience before an account meeting
- Onboard to a new account
- Replay context analysis on a second org for the same customer
- Understand what's happening across a customer's umbrella

---

## Pre-Flight — MEMORY.md Check

Before asking anything, silently read `MEMORY.md` in the current working directory. If the customer already has a context bundle listed there, surface it before asking intake questions:

> "I see Acme already has a context bundle from [date]. Do you want to build context for a different org in their umbrella, or refresh the existing one?"

If `MEMORY.md` doesn't exist, proceed to Phase 0.

---

## Phase 0 — Intake

Ask all of the following in **one single message**. Do not proceed until you have all answers.

```
Before I build the context bundle, I need a few things:

1. NEW OR EXISTING CUSTOMER?
   - New: I'll set up the directory structure from scratch
   - Existing: Which org are we building context for?

2. UMBRELLA OR STANDALONE?
   Is this org part of a Fullstory umbrella account, or is it standalone?
   - Umbrella: What is the umbrella account name and umbrella ID? (e.g., "Acme · u-EXAMPLE-eu1")
   - Standalone: This org will live at the top level of /clients/

3. ORG DETAILS
   - Org display name (e.g., "Acme Member - Web - USA")
   - Org ID (e.g., "o-XXXXX-eu1")
   - Region: US (api.fullstory.com) or EU (api.eu1.fullstory.com)?

4. WEB OR MOBILE?
   Is this org a web property or a native mobile app?
   - Web: browser-based — has URLs, pages, LCP/CLS/INP, form abandonment, page refresh
   - Mobile Native: iOS or Android SDK — has screens (no URLs), taps, crashes, app launch time
   - Mobile Web: a mobile browser experience — treat as Web

5. CUSTOMER HQ CITY
   What city is this customer's headquarters in? (Used to filter internal employee sessions from
   analysis — HQ sessions skew behavior and are excluded from all session reviews.)

6. PS/ADVANTAGE STATUS
   Does this customer have Fullstory Professional Services hours, or are they a Fullstory
   Advantage Services customer? (Affects PS plug in deliverables)
```

---

## Phase 1 — Directory Setup

### 1a. Create directory structure

**If umbrella:**
```
clients/
  [Account Name (umbrella-id)]/        e.g. "Acme (u-EXAMPLE-eu1)"
    [Org Name (org-id)]/               e.g. "Acme Corp - Web - USA (o-XXXXX-eu1)"
```

**If standalone:**
```
clients/
  [Org Name (org-id)]/                 e.g. "Acme Corp (o-XXXXX-na1)"
```

Run `mkdir -p` for the full path. Never create a client folder without the org subdirectory ready.

### 1b. Create customer.yaml

At the top of the account directory (umbrella level, or org level if standalone):

```yaml
customer: "slug-kebab-case"
display_name: "Display Name"
umbrella_id: "u-XXXXX-eu1"       # omit if standalone
org_id: "o-XXXXX-eu1"
region: "eu"                      # or "us"
org_type: "web"                   # "web", "mobile_native", or "mobile_web"
hq_city: "Dallas, TX"            # used to filter internal employee sessions
professional_services: false
advantage_services: false
notes: ""
created: "YYYY-MM-DD"
```

### 1c. Initialize job-log.jsonl

Create an empty `job-log.jsonl` file in the org directory. All subsequent MCP steps will be appended here using the job-log runner.

**Binary preference:** Use `./dist/job-log` if present (no Python required); fall back to `python3 job-log.py` if not. Set once per session:

```bash
JOB_LOG=$([ -x ./dist/job-log ] && echo ./dist/job-log || echo "python3 job-log.py")
```

Log format reference:
```bash
# Non-artifact step (read/compute tool):
$JOB_LOG log-step \
  --client "Account Name (umbrella-id)" \
  --org "Org Name (org-id)" \
  --play "org-context-root" \
  --step 1 \
  --tool "discover_org_context" \
  --params '{"queries": [...]}' \
  --purpose "What this step establishes" \
  --output-doc "org-context-root.md"

# Artifact step (build/update tool that produces an ID):
$JOB_LOG log-artifact \
  --client "Account Name (umbrella-id)" \
  --org "Org Name (org-id)" \
  --play "org-context-root" \
  --step 5 \
  --tool "build_metric" \
  --params '{"query": "..."}' \
  --artifact-type metric \
  --artifact-id "395428225" \
  --artifact-name "Page Views by Named Page" \
  --purpose "Traffic distribution across the site" \
  --output-doc "org-context-root.md"
```

---

## Mobile Native Branch — What Changes

If `org_type: "mobile_native"` — read this section before Phase 2 and apply these overrides throughout. If `org_type: "web"` — skip this section entirely.

### What does NOT exist in native mobile

| Web concept | Mobile reality |
|---|---|
| URLs / page paths | Screen names only — no URLs |
| LCP (Largest Contentful Paint) | Not applicable — browser paint metric |
| CLS (Cumulative Layout Shift) | Not applicable — no document layout |
| INP (Interaction to Next Paint) | Not applicable — no browser paint pipeline |
| RefreshedPageByPage | No pull-to-refresh equivalent in Fullstory mobile signals |
| AbandonedFormByPage | Mobile forms don't abandon the same way — skip |
| Console errors | No browser console — use native exception signals instead |

### What IS different in native mobile

**Navigation:** Screen transitions replace URL navigations. Fullstory maps screen names to page IDs — the same DIMENSION_PAGE_DEF_ID grouping works, but the "pages" returned are app screens (e.g., "Lot Detail Screen", "Search Results Screen").

**Frustration signals — mobile-first priority order:**
1. `AppCrashByPage` — crashes on specific screens — the #1 mobile frustration signal, equivalent to what RefreshedPageByPage + AbandonedFormByPage represent for web
2. `RageClickByElement` — rage taps on UI elements (Fullstory uses "click" terminology even for taps)
3. `DeadClickByElement` — dead taps — user taps something that doesn't respond
4. `ErrorClickByElement` — error taps
5. `NetworkErrorByPathNoStatusZero` — API call failures — still critical for mobile (all data comes from API)

**Performance signals — mobile-first metrics:**
- App launch / cold start time (if instrumented)
- Screen load / render time per screen
- Network request latency by endpoint — critical; mobile networks are less reliable
- Crash rate by screen (from AppCrashByPage)
- App version as a dimension — regressions show up in version comparisons
- OS version + device model — fragmentation-driven bugs

**Skip in Phase 2:**
- Step 8 (LCP by page) — skip entirely for mobile native
- Step 9 (CLS by page) — skip entirely for mobile native

**Replace with in Phase 2:**
- Step 8 MOBILE: Build `discover_groups` scoped to `AppCrashByPage` — get crash rate by screen. Then build a metric for crash rate trend: `"count of app crashes by named page, last 30 days"`.
- Step 9 MOBILE: Build a metric for network error rate by endpoint: `"count of network errors by URL path, last 30 days"`. These are the API failures affecting the mobile experience.

**Session stories for mobile:**
- Open sessions around crash timestamps or rage-tap moments
- Describe: what screen the user was on, what they tapped, whether the crash/tap-failure blocked their goal
- Note the device model and OS version — mobile bugs are often device/OS-specific
- Look for patterns: same crash on multiple sessions = systemic; isolated = edge case

**HTML report Performance tab → rename to "App Performance":**
- Replace LCP/CLS/INP tables with: crash rate by screen, network error rate by endpoint, app version breakdown
- Headline KPI tiles: crash rate %, affected sessions, most-crashed screen
- No stat-narrative about web vitals — narrate crash impact and API failure patterns instead

**Sub-agent adjustments for mobile:**
- `org-context-performance.md` prompt must say: skip LCP/CLS/INP. Focus on: crash rate by screen, network error rate, app version regression analysis, device model fragmentation.
- `org-context-frustration.md` prompt must say: no RefreshedPageByPage or AbandonedFormByPage. Prioritize AppCrashByPage, rage taps, dead taps.
- `org-context-errors.md` prompt must say: no console errors. Native exceptions + network errors are the primary signal types.
- `org-context-suspicious-activity.md`: same as web — bot/synthetic traffic patterns apply to mobile SDK orgs too.

---

## Phase 2 — Root Context Play

Build `org-context-root.md`. This is both the global context summary and the orchestration manifest for sub-agents. Run all steps in order. Log each step to job-log.jsonl as you go.

### Step 1 — Verify MCP connection (log as step 1)

Call `discover_org_context` with queries that match the customer's known domain:
```
["product/lot/listing", "auction/checkout/purchase", "bid/order/buy", "member/user/account", "search/find/browse", "[customer-name]"]
```

Adapt the queries to the customer's industry. Confirm that the page names, element names, and event names returned match the expected customer — not the CarGo demo org or any other org. If you see CarGo data, stop and tell the analyst: the MCP is pointed at the wrong org.

### Step 2 — Inventory site sections (log as step 2)

Call `discover_org_context` with queries covering primary navigation areas:
```
["home", "login", "search", "dashboard", "payment", "checkout", "registration", "account", "cart", "product"]
```

Adapt to the customer's business. The goal is to find all major page categories.

### Step 3 — Inventory funnels (log as step 3)

Call `get_funnel` with `regex: ".*"` and `limit: 25`. Study what conversion flows the customer team has already defined — this tells you what they care about measuring and what problems they're already investigating.

### Step 4 — StoryAI opportunities (log as step 4)

Call `discover_groups` with `relative_time_range: "30d"` and `limit: 5`. This returns all signal types: UncaughtExceptionsByText, NetworkErrorByPathNoStatusZero, ConsoleErrorsByText, DeadClickByElement, ErrorClickByElement, RageClickByElement, AbandonedFormByPage, RefreshedPageByPage.

Store: every group_id, default_metric_id, user_count, user_pct, group_id_fallback.

### Step 5 — Page view distribution (log artifact as step 5)

**Build:**
```
query: "count of page views grouped by named page, last 30 days"
output_type: "top_n"
time_range: "last_30_days"
```

**After building — ALWAYS confirm the definition before computing:**
- Check the grouping dimension. It must be `"builtInProperty": "DIMENSION_PAGE_DEF_ID"` (named page).
- If it shows `DIMENSION_URL_PATH` instead — the build used URL path grouping, which is too granular for any site with unique-URL item/product/lot pages.
- Fix: call `update_metric` with `refinement: "group by Fullstory named page instead of URL path"`. Re-read the definition to confirm.

**Then compute.** The result gives traffic distribution across the site's named pages.

### Step 6 — Time on page (log artifact as step 6)

Build a metric for median time on page:
```
query: "median total time on page grouped by named page, visited page is any, last 30 days"
output_type: "top_n"
```

**After building — critical check:** Read the returned definition and verify the `event` field contains a `visitedUrl` filter. It must look like `"event":{"primary":{"visitedUrl":{"any":{}}}}`. If the event filter is absent from the definition, the metric will return all zeros — page duration is only a valid property on pageview events. Call `update_metric` with `refinement: "add filter: visited page is any"` and re-read the definition before computing.

Do the same for active time on page:
```
query: "median active time on page grouped by named page, visited page is any, last 30 days"
```
Same fix applies if the event filter is missing.

### Step 7 — Entry and exit page distribution (log artifacts as steps 7–8)

Build and compute two metrics:
- `"count of sessions where entry page is each named page, grouped by named page, last 30 days"`
- `"count of sessions where exit page is each named page, grouped by named page, last 30 days"`

These reveal: which pages users land on directly (deep-link traffic), and which pages they leave from (bounce points and conversion endpoints).

### Step 8 — LCP by page (log artifacts as steps 9–10)

Build and compute:
- `"median Largest Contentful Paint grouped by named page, last 30 days"` → `output_type: "top_n"`
- `"95th percentile Largest Contentful Paint grouped by named page, last 30 days"` → `output_type: "top_n"`

Confirm the definition has an LCP event filter (`largestContentfulPaint`). If not, add via `update_metric`. LCP thresholds: Good ≤2,500ms · Needs Improvement 2,500–4,000ms · Poor >4,000ms.

### Step 9 — CLS by page (log artifact as step 11)

Build and compute:
```
query: "Cumulative Layout Shift by named page, last 30 days"
output_type: "top_n"
```

CLS thresholds: Good ≤0.1 · Needs Improvement 0.1–0.25 · Poor >0.25. Note: the MCP often builds CLS as an average rather than median — acceptable for directional analysis.

### Step 10 — Session stories (log as step 12)

Pull sessions from 2–3 of the most impactful StoryAI signals (prioritize: abandoned form on the primary conversion page, rage clicks on the primary CTA, error clicks on key navigation).

**Session pull rules — non-negotiable:**
- **Exclude the customer's HQ city** (from customer.yaml `hq_city`). HQ sessions are internal employees — they skew behavior.
- **Minimum:** duration ≥ 60 seconds AND events ≥ 50. Shorter/smaller sessions don't provide enough narrative.
- **Use** `get_sessions_for_opportunity` with the `default_metric_id` and `group_id` from discover_groups output — these are proactive metric type strings (e.g., `"RageClickByElement"`), not saved metric IDs.

For each session: call `session_open`, use `get_session_events` or `review_zoom` to read the narrative, identify whether the frustration signal actually disrupted what the user was doing, then call `session_close`. Write a 2–4 sentence session story capturing: who the user is, what they were trying to do, what went wrong, and what it means.

### Step 11 — Write org-context-root.md v1

Write the file to the org directory. It must include:

1. **Org header** — org name, org ID, umbrella ID, region, replay base URL, API key env var
2. **Sub-agent orchestration manifest** — a table directing each sub-agent to its focused lens, with: context file to produce, priority page IDs to investigate, starting StoryAI metric types
3. **Critical methodology rules block** — must contain these verbatim:
   - *Error severity is determined by UX impact, not volume.* Pull sessions. Review at the error timestamp. Did the user fail, refresh, or abandon? = high. Did they continue unbothered? = low severity regardless of count.
   - *Session pull rules:* Exclude HQ city. Duration ≥ 60s AND events ≥ 50. Last 7 days for sessions.
   - *Known noise filter:* List any signals confirmed as noise from Step 4. Sub-agents do not investigate noise signals.
   - *Special iFrame surfaces:* If any iFrame-hosted environments are detected (live auction rooms, payment processors, embedded apps), name them explicitly. Errors inside iFrames don't appear in standard page-scoped metrics.
4. **Business context** — what the site does, who the users are, the core user need
5. **Traffic distribution** — top 10 pages by view volume with page IDs
6. **Engagement metrics** — median total time and active time by page (top 10)
7. **Entry and exit pages** — top 10 each
8. **Web vitals** — LCP median + p95 by page, CLS by page
9. **StoryAI signals** — classified as: Confirmed Noise / Needs Session Validation / Confirmed UX-Breaking
10. **Primary user journeys** — 3–5 flows mapped from page inventory and funnel data
11. **Session stories** — 2–3 narrative summaries with session replay URLs
12. **Key funnels** — inventory of defined funnels with IDs and what they measure
13. **Saved metric IDs** — every metric built in this session with ID, name, what it measures, and any gotcha notes
14. **Data quality notes** — org-specific issues: uncategorized pages, known noise, special environments
15. **Open questions** — gaps and questions for sub-agents to resolve

---

## Phase 3 — Sub-Agent Deployment

Deploy all four sub-agents in **parallel** (single message, four Agent tool calls). Each agent:
- Has a self-contained prompt (it has no access to this conversation)
- Reads the org-context-root.md file you just produced as its primary briefing
- Produces exactly one context file
- Must be briefed on: org credentials, the session pull rules, the error severity methodology, the known noise signals, and any org-specific special surfaces

**Sub-agent assignments:**

| File to produce | Focus | Priority pages (by name from root context) | Starting signals |
|---|---|---|---|
| `org-context-frustration.md` | Rage clicks, dead clicks, error clicks, form abandonment, page refreshes | Primary conversion page, primary browse page, checkout/bid flow | RageClickByElement, DeadClickByElement, ErrorClickByElement, AbandonedFormByPage, RefreshedPageByPage |
| `org-context-errors.md` | Console errors, network errors, uncaught exceptions — root cause + UX impact | Conversion page, authenticated entry points | ConsoleErrorsByText, NetworkErrorByPathNoStatusZero, UncaughtExceptionsByText |
| `org-context-performance.md` | LCP/CLS/INP by page, worst performers, conversion impact | Primary conversion page, primary browse page, live/real-time features | Reuse root context metric IDs for LCP and CLS. Build INP metric. |
| `org-context-suspicious-activity.md` | Bot/synthetic traffic volume, distribution, impact on metrics | Org-wide first, then conversion page and browse page specifically | Build segments using DEVICE_ROBOT or Suspicious Activity types |

**Each sub-agent prompt must include:**
1. Org name, org ID, region, replay base URL
2. The full session pull rules (HQ city exclusion, ≥60s/≥50 events)
3. The error severity rule (validate at session level — do not rank by volume)
4. The list of confirmed noise signals from root context (sub-agents skip these)
5. Any special iFrame surfaces to check
6. The exact metric IDs already built (so sub-agents don't rebuild what exists)
7. The output file path
8. The required document structure (executive summary, full inventory with UX verdicts, session evidence, recommendations)

**Metric building note to include in each sub-agent prompt:**
> After calling `build_metric`, always read the returned definition to confirm: (1) the event filter is present and correct, (2) grouping dimension is DIMENSION_PAGE_DEF_ID for page-level analysis. If a metric returns zeros, check the definition first — a missing event filter is the most common cause.

---

## Phase 4 — Root Context v2

Read all four sub-agent output files. Update `org-context-root.md` to reflect:

1. **New root causes identified** — e.g., if the errors sub-agent found the exact line of code causing a bug, add it to the relevant StoryAI signal entry
2. **Severity reclassifications** — signals initially marked "Needs Validation" that sub-agents confirmed breaking or confirmed noise
3. **New signals discovered** — any signals sub-agents found that weren't in the original StoryAI list
4. **CLS root causes** — if performance sub-agent identified what's causing layout shift, add it
5. **Bot impact assessment** — if suspicious activity sub-agent found bot rate >5% on any key page, add a data quality note
6. **Refined open questions** — remove questions now answered; add new ones raised by sub-agents

The root context v2 is the final, authoritative global context document.

---

## Phase 5 — HTML Context Report

Build `context-report-YYYYMMDD.html` in the org directory. This is an internal multi-tab SPA — not a customer deliverable. No PS plug.

**MANDATORY — Visual Pre-flight Protocol before writing any HTML:**
1. Read `_component-index.md` — find the row for your use case
2. Read the snippet file from `_snippets/` listed in that row
3. Adapt the snippet with real data. Do not add new CSS classes or custom styles.

**Required tabs:**

| Tab | Content |
|-----|---------|
| Overview | Business context, headline KPI tiles (page views, sessions, users, conversion rate), conversion funnel vbar (one per report), traffic distribution sparkbar tiles, top 3 confirmed issues as callout + detail cards, primary user journeys as path-cards |
| Frustration | Methodology callout, full signal table (compare-table with b-no/b-partial/b-yes/b-gated badges), session evidence as detail-items with replay links |
| Errors | Noise callout, P1 confirmed errors as detail-items, full inventory as compare-table |
| Performance | INP metric-tiles (newly measured), LCP table, CLS table with root cause callout, stat-narrative after every statistical display |
| Bots | KPI tiles (org-wide rate, key page rates, trend), page distribution table, archetypes as detail-items, filtering rec table |

**Component routing (from _component-index.md):**
- Single KPI with severity badge → `metric-tile` + `sparkbar`
- Headline funnel (one per report) → `vbar-chart` from `_snippets/funnel-vbar.html`
- Dashboard KPI with funnel context → `combo-tile` from `_snippets/kpi-combo-tile.html`
- Numbered user journey flow → `path-card` from `_snippets/path-card.html`
- Signal/issue tables → `compare-wrap` + `compare-table` with design system badges
- Flags and callouts → `callout` / `callout.red` / `callout.orange` / `callout.purple`
- Individual findings → `detail-item.pro` / `.con` / `.note`
- Every stat chart → must be followed by `.stat-narrative` block

**Report header requirements:**
- Org name, org ID, umbrella ID, region
- Generation date (clearly visible)
- "Refresh recommended monthly" note so readers know data freshness

**Color semantics — non-negotiable:**
- Green → entry point, converted/success, healthy, Good rating
- Red/pink → walls, blockage, critical, Poor rating
- Orange → survivors, pass-through, warning, Needs Improvement rating
- Purple → annotations, secondary insight, methodology notes

---

## Phase 6 — Finalize

### 6a. Export playbook

Run:
```bash
JOB_LOG=$([ -x ./dist/job-log ] && echo ./dist/job-log || echo "python3 job-log.py")
$JOB_LOG export-play \
  --client "[Account Name (umbrella-id)]" \
  --org "[Org Name (org-id)]" \
  --play org-context-root
```

This writes `playbook-org-context-root.json` to the org directory. This is the machine-readable recipe for replaying the exact same analysis on another org in the umbrella — hand it to a fresh agent with the new org's credentials.

### 6b. Update MEMORY.md

Add an entry under the customer:
```
## [Customer Display Name]
- [YYYY-MM-DD] Org context bundle: [Org Name] — [org-id]
  Files: org-context-root.md, org-context-frustration.md, org-context-errors.md,
         org-context-performance.md, org-context-suspicious-activity.md,
         context-report-YYYYMMDD.html
```

### 6c. Report to analyst

Tell the analyst what was built, where the files are, and the top 3 findings from the root context — the ones most likely to matter in the next account conversation.

---

## Hard Rules for This Skill

1. **Log every MCP call.** Every `build_metric`, `update_metric`, `compute_metric`, `get_funnel`, `discover_groups`, `discover_org_context`, `get_sessions_for_opportunity`, `session_open`, `session_close` call gets logged to job-log.jsonl before moving to the next step. The log is the replay recipe.

2. **Confirm metric definitions before computing.** Never call `compute_metric` on a metric you didn't read the definition of. Two failure modes to check every time: (a) grouping by URL path instead of DIMENSION_PAGE_DEF_ID — always refine for sites with unique-URL item pages; (b) missing event filter on duration metrics — add `visitedUrl.any` or the metric returns zeros.

3. **Severity by UX impact.** Never report an error or frustration signal as high-severity based on event count alone. Pull a session. Watch what the user does after it fires. If they continue unbothered — it's low severity regardless of volume. Document the session URL and timestamp as evidence.

4. **Session pull rules are always active.** HQ city exclusion + ≥60s duration + ≥50 events. No exceptions. These rules prevent internal employee behavior from contaminating the analysis.

5. **Design system only.** No custom CSS for any visualization. Every chart, tile, or table must map to a row in `_component-index.md`. Read the snippet. Adapt. Do not fork.

6. **One vbar per report.** The `vbar-chart` (full vertical bar chart) appears once in the HTML report as the headline conversion funnel on the Overview tab. All other funnel references within the report use `combo-tile` or `sparkbar` tiles.


8. **PS plug rule.** Include the PS plug in the HTML report only if `professional_services: false` AND `advantage_services: false` in customer.yaml. Never in field guides. Role-based variant: SE/Sales Engineer variant vs. all-other-roles variant (see CLAUDE.md).
