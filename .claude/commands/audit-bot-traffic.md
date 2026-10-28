# Audit Bot Traffic

Quantify and characterize synthetic, automated, and robotic traffic on a customer's Fullstory org. Separates real user behavior from bots, test scripts, crawlers, and other non-human sessions. Produces a clean traffic picture and shows whether synthetic traffic is distorting the customer's DX metrics.

## When to invoke

Use this skill when a analyst asks to:
- Find out how much bot or synthetic traffic is in Fullstory
- Understand if automated scripts are polluting their data
- Explain why metrics look wrong or spiky
- Verify the quality of their Fullstory data before building analysis on top of it
- Check whether Linux sessions should be included in their reports

---

## Detection Method: Fullstory Suspicious Activity Signals

Fullstory natively classifies non-human sessions using its **Suspicious Activity** feature (Enterprise and Advanced plans). This is the primary detection method — more accurate and more specific than OS or UA string checks alone.

Suspicious Activity signals are organized into five types. For synthetic traffic audits, focus on:

**Automation** — Bot behavior and absence of human interaction
- `Headless Browser` — highest-confidence bot signal; fires on 0×0 viewport, "Headless" in UA, or known tool signatures (PhantomJS, Puppeteer, Selenium, Playwright, Cypress)
- `No Pointer Movement` — interactions present but no mouse movement; can fire on keyboard-only users (lower confidence alone)
- `No Pointer Curve` — straight-line cursor jumps with no natural arc; bots move directly between coordinates
- `No User Activity` — page loaded but zero interactions; typical of crawlers
- `Full Page Resize` — viewport resized to full document height; screenshot-capture technique used by scrapers

**AI** — AI-powered non-human traffic
- `AI Crawler` — GPTBot, ClaudeBot, Google-Extended, DeepSeekBot, Bytespider, PerplexityBot (collecting training data)
- `AI Agent` — autonomous agents completing tasks: AmazonBuyForMe, Claude-Web, GoogleAgent-Mariner, Manus-User
- `AI Assistant` — ChatGPT-User, Claude-User, Gemini-Deep-Research (browsing on behalf of a user during chat)
- `AI Vendor` — traffic from known AI company IP ranges (OpenAI, Google, Microsoft, Perplexity, Apple)

**Network** — Infrastructure-based origin signals
- `Cloud Network` — GCP, AWS, Azure, Oracle, IBM, DigitalOcean IP ranges; typical of bot infrastructure (may also fire for legit users on cloud VDI)
- `Consumer Private Network` — Apple Private Relay and similar; obscures real IP but not inherently non-human

**Also note — not synthetic traffic but worth surfacing separately:**
- **Security** signals (`SQL Injection`, `XSS Injection`) — active attack attempts on forms/URLs
- **Content** signals (`Credential Pair`, `Field Enumeration`, `Multiple Emails`) — fraud and credential-stuffing patterns

**Fallback (if Suspicious Activity is unavailable):** Check for Linux OS user agents and UA strings containing "HeadlessChrome", "PhantomJS", "Selenium", "Playwright", "Puppeteer", "bot", "crawler", "spider" as a lower-precision proxy.

---

## Pre-Flight — MEMORY.md Check

Before asking the analyst anything, check if `MEMORY.md` exists in the current working directory. If it does not exist, create it silently with the standard blank structure and proceed.

---

## Phase 0 — Intake

Ask in a single message:

```
Before I begin, a few things:

1. CUSTOMER NAME
   What customer's Fullstory org are we auditing?

2. TIME WINDOW
   What period should we analyze? Default is last 30 days.

3. CONTEXT (optional)
   Is there a specific concern that triggered this?
   (e.g., "metrics look off", "session count seems too high", "we see strange traffic patterns")
```

---

## Phase 1 — Quantify Synthetic Traffic

### 1a. Total Traffic Baseline

Build a metric: total unique sessions, no filters. Compute it. This is the raw denominator.

### 1b. Automation-Type Suspicious Activity

Call `build_segment` with: "sessions where Suspicious Activity type is Automation". Compute:
- Total Automation-type sessions in the time window
- As a percentage of all sessions

Then pull `Suspicious Activity is Headless Browser` specifically (sub-segment or refine the segment). Headless Browser is the highest-confidence signal — call it out separately in the summary.

### 1c. AI-Type Suspicious Activity

Call `build_segment` with: "sessions where Suspicious Activity type is AI". Compute count and percentage. This captures AI crawlers, AI agents, and AI assistants browsing on behalf of a chat user — all non-human.

### 1d. Cloud Network Traffic

Call `build_segment` with: "sessions where Suspicious Activity is Cloud Network". Compute count and percentage. Note: may include legit users on cloud-hosted VDI — interpret in context of other signals.

### 1e. Combined Non-Human Volume

Combine Automation-type + AI-type sessions (Cloud Network kept separate as it has more ambiguity). Compute:
- Total non-human sessions (Automation + AI)
- As a percentage of all sessions
- Cloud Network as a separately noted additional signal

**Fallback if Suspicious Activity is not available on this org:** Build segment: sessions where OS contains "Linux" OR user agent contains "HeadlessChrome" OR "PhantomJS" OR "Selenium" OR "Playwright" OR "Puppeteer". Note this is a lower-precision proxy.

Present to the analyst before proceeding:

> Synthetic traffic found:
> - Automation-type (bots, headless browsers): [N] ([X]% of all sessions)
>   - Headless Browser specifically: [N] — highest-confidence signal
> - AI-type (crawlers, agents, assistants): [N] ([Y]% of all sessions)
> - Cloud Network origin: [N] ([Z]% of all sessions) — may include cloud VDI users
> - Combined non-human (Automation + AI): [N] ([X+Y]% of all sessions)
>
> This means approximately [X+Y]% of sessions in Fullstory are not real users.

---

## Phase 2 — Characterize Synthetic Sessions

Pull 5 sessions using `get_sessions` with the Automation-type Suspicious Activity segment. Review for:
- What specific Suspicious Activity signals fired on each session? (Headless Browser vs. No Pointer Movement vs. No User Activity)
- What pages are they hitting? (health check endpoints, specific flows, crawling broadly)
- Are they triggering conversion events?
- What's the session duration and page count?

**Common patterns and what they mean:**

| Pattern | Suspicious Activity signals | Most likely source |
|---|---|---|
| Hits 1–2 pages, immediate exit, No User Activity | No User Activity | Health check or uptime monitor |
| Completes full checkout flow at superhuman speed | No Pointer Curve, Headless Browser | Synthetic order testing / QA automation |
| Crawls many pages rapidly, No User Activity | No User Activity, Cloud Network | Search crawler or scraper |
| Hits login page repeatedly | Multiple Emails, Field Enumeration, Credential Pair | Credential stuffing or brute force |
| Full user journey, realistic timing, Cloud Network only | Cloud Network | Load test or legitimate cloud VDI user |
| AI Crawler signals | AI Crawler | Training data collection or web indexing |
| AI Agent signals | AI Agent | Autonomous task completion (form filling, browsing) |

If AI-type sessions were found in Phase 1, pull 2–3 from that segment as well and note what they were doing.

Note what type(s) of synthetic traffic the customer has. This context shapes the severity of the recommendation.

---

## Phase 3 — Distortion Check

This is the "so what" — does synthetic traffic actually change the analysis?

Compute the following metrics **twice**: once with all sessions, once with synthetic sessions excluded (use the Automation + AI combined segment from Phase 1e as the exclusion filter).

| Metric | All sessions | Real users only | Delta |
|---|---|---|---|
| Rage click rate (rage clicks ÷ sessions) | | | |
| Dead click rate | | | |
| Abandoned form rate | | | |
| Avg session duration | | | |
| Top page by volume | | | |

If delta on any metric is >5%, synthetic traffic is meaningfully distorting the customer's data. Flag this prominently — it means every analysis they've done to date may be skewed.

**StoryAI Opportunities note:** When distortion is Moderate or High, also note that some pre-ranked StoryAI Opportunities may be artificially elevated by synthetic traffic — issues concentrated among bot sessions will surface as opportunities even if real users never experience them. This is worth mentioning in the recommendation as a reason to re-run analysis with synthetic traffic excluded.

---

## Phase 4 — Security and Fraud Signals (Always Check)

These signals are separate from synthetic traffic volume — they indicate active attacks or fraud patterns and should always be surfaced even if bot volume is low.

**Security signals:**
- Build segment: "sessions where Suspicious Activity is SQL Injection". Compute count.
- Build segment: "sessions where Suspicious Activity is XSS Injection". Compute count.
- Any non-zero count here = active attack attempts on the customer's application. Flag as a security finding, not a data quality issue. These should be escalated to the customer's security team.

**Content/fraud signals (if applicable to the customer's use case):**
- `Credential Pair` — email:password pasted into a form field. Indicates credential stuffing.
- `Field Enumeration` — 3+ distinct values entered in the same field. Username/promo code probing.
- `Multiple Emails` — 2+ distinct emails submitted on the same page. Credential stuffing or account enumeration.
- `Disposable Email` — temporary email services used at signup. Indicates fake account creation or trial abuse.

Build a segment for Content-type signals if the customer has a login page, signup flow, or checkout. Compute count and note.

Present these findings in a separate callout in the report — distinct from the "synthetic traffic distorting your metrics" narrative.

---

## Phase 5 — Other Signals Worth Noting (Optional)

If Phase 1 volume is low (<1% Automation + AI), or if the analyst wants a fuller picture, also check:

- **Very-short sessions**: sessions under 3 seconds with 0 interactions. Build a metric: session count where duration < 3s. High volume here = additional synthetic or tracking pixel traffic that Fullstory captured but didn't record meaningfully.
- **Single-page sessions at scale**: pages that appear as the only page in a large number of 1-page sessions may be hit by crawlers or monitoring tools even if the UA resolved to a non-Linux OS.

---

## Phase 6 — Report Generation

Generate a self-contained HTML report using `_starter.html`.

**Header:**
- "[Customer] Traffic Quality Audit"
- Subtitle: "Real vs. Synthetic Session Analysis | [Time Window] | [Date]"

Set `data-sync-pair="[customer-slug]-traffic-audit-[YYYY-MM]"` on `<html>`.

### Report Structure

**Section 1: Traffic Composition** (`data-sync-section="composition"`)

Headline KPI tiles:
- Total sessions
- Real user sessions (non-synthetic)
- Synthetic sessions
- Synthetic %

A plain-language summary of what types of synthetic traffic were found and what they most likely represent.

**Section 2: Distortion Impact** (`data-sync-section="distortion"`)

The before/after table from Phase 3. If any metric shifted >5%, call it out as a finding: "Your [rage click rate / form abandonment / avg session duration] is [X] when synthetic sessions are included. With real users only, it is [Y]. This [understates / overstates] the true user experience."

**Section 3: Synthetic Session Characterization** (`data-sync-section="characterization"`)

What are the synthetic sessions doing? Plain-language description of the patterns observed in Phase 2, broken down by signal type:
- Automation-type: what tool or behavior pattern they appear to represent
- AI-type: what AI crawlers or agents were detected and likely doing
- Cloud Network: whether it appears to be bot infrastructure or cloud VDI

**Section 4: Security and Fraud Signals** (`data-sync-section="security"`)

Only include this section if any Security or Content signals were found in Phase 4.

For Security signals (SQL Injection, XSS Injection): present as a finding separate from the bot traffic discussion. Use an amber or red callout block:

> **Active attack signals detected:** Fullstory recorded [N] sessions containing SQL Injection patterns and [N] sessions containing XSS Injection attempts during this period. These are not data quality issues — they indicate someone actively probing your application for vulnerabilities. Your security team should review these sessions.

For Content/fraud signals: present as a separate finding with session count and the specific pattern observed (credential stuffing, fake account creation, etc.).

**Section 5: Recommendation** (`data-sync-section="recommendation"`)

One of three conclusions:

- **Low impact** (< 1% synthetic): "Synthetic traffic is negligible. No action required, but all future analysis should exclude Linux to maintain clean segments."
- **Moderate impact** (1–5% synthetic, <5% metric distortion): "Synthetic traffic is present but not materially distorting DX metrics. Recommend applying the Linux exclusion filter to all future Fullstory analysis as standard practice."
- **High impact** (>5% synthetic OR >5% metric distortion): "Synthetic traffic is meaningfully distorting your Fullstory data. Every metric your team has been reporting from Fullstory may be skewed. Recommend immediate action: apply the Linux exclusion filter to all segments, and re-run any analysis used in business reporting."

**Footer:** time window, segment definitions used, data source.

---

## Phase 7 — Field Guide Generation

Generate a companion field guide using `_field-guide-starter.html`. Internal only.

Set `data-sync-pair="[customer-slug]-traffic-audit-[YYYY-MM]"` on `<html>`.

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

1. Open with: "Before we build any analysis, I want to show you something about the quality of your Fullstory data."
2. Present the traffic composition — let the synthetic % land before explaining what it means.
3. Walk the distortion table: "Here's what your metrics look like with all traffic vs. real users only." If there's a meaningful delta, pause and let that sink in.
4. Characterize what the synthetic sessions appear to be — don't alarm unnecessarily if it's just QA automation.
5. Close with the recommendation: here's the filter, here's why we apply it to everything going forward.

**Section 2: Presenter Notes** (`data-sync-section="presenter-notes"`)

- If it's QA/testing traffic: this is actually a sign of a healthy engineering practice, just not relevant to DX analysis.
- If it looks like a crawler: ask whether the customer has any known SEO or monitoring tooling that hits their production environment.
- If SQL Injection or XSS signals were found: frame this separately from the bot discussion — this is an active security issue, not a data quality issue. They should involve their security team. Suggest correlating with WAF logs.
- If Credential Pair or Field Enumeration signals were found on the login page: this is credential stuffing — worth escalating to their fraud/security team.
- If AI Agent signals were found: mention that autonomous AI agents (not crawlers — actual task-completing agents) are browsing their site. This is emerging behavior and may have implications for their product experience design.
- If distortion is high: validate that any existing dashboards or reports this team has built from Fullstory data should be re-examined. This is a trust moment — handle carefully.

**Section 3: Discovery Questions** (`data-sync-section="discovery"`)

- Does your team run synthetic tests or load tests against your production environment?
- Do you have any uptime monitoring tools that hit pages in your app?
- Have you ever filtered your Fullstory data by operating system before?
- Are there any dashboards or reports your team pulls from Fullstory that you rely on for business decisions? (Sets up the re-examination conversation if distortion was high.)
- Do you use any SEO crawling or indexing tools?

**Section 4: Session Evidence** (`data-sync-section="session-evidence"`)

The synthetic session links from Phase 2, labeled by likely type:
```
Linux Sessions (likely [QA automation / health check / crawler]):
  • [Session URL 1]
  • [Session URL 2]
  • [Session URL 3]
```

---

## Output

```
./clients/[customer-slug]/traffic-audit-[YYYY-MM]/
./clients/[customer-slug]/traffic-audit-[YYYY-MM]/field-guide/
```

Save:
- `index.html` — deliverable
- `field-guide/index.html` — internal companion

Update `MEMORY.md`:
```
- [YYYY-MM-DD] Traffic Quality Audit: traffic-audit-[YYYY-MM]
```

Open the field guide:
```bash
open ./clients/[customer-slug]/traffic-audit-[YYYY-MM]/field-guide/index.html
```

Report to the analyst:
- Total synthetic session percentage
- Whether distortion is Low / Moderate / High
- What type(s) of synthetic traffic were found
- Reminder: click "Open Report →" in the field guide to view the deliverable alongside it
