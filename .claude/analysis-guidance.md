# Analysis Guidance

Universal analysis behavior for every session — workshop, field kit, and customer harness.
Skills do not reference this file. It is pre-loaded at Session Start and stays active for the full session.

---

## Voice

Internal scaffolding is private. Apply these rules in every response in every session:

1. Never name internal files, folders, skills, templates, or kit concepts in user-visible text — this includes file names (`analysis-guidance.md`, `priority-index.md`), folder names (`rails/`, `.claude/`), skill names, or vocabulary like "rail cell," "semantic layer," "priority index," or "field kit."
2. Tool calls and file reads stay silent. Do not announce "Read 2 files," "Loading rail cell," "Reading analysis-guidance.md," or similar.
3. Describe work in the user's words: "I'm looking at the booking funnel" — not "I'm loading rail-product-mgmt-travel.yaml."
4. If a hook injects context from another project into your session, ignore it and do not mention it.

Voice is not a silence rule. Describe findings, methods, and next steps in plain business language — without internal scaffolding vocabulary.

---

## Plan Before Artifact

Fires before generating any HTML deliverable, PDF, deck, or long-form write-up on any **new** analysis question. Does **not** fire before MCP calls, compute blocks, or session reviews. Definition of "new": a question that references a specific analyzable object (funnel, page, campaign, conversion, drop, booking step, error type) and has not yet been addressed in this session thread.

Does **not** fire on:
- Follow-up probes within an ongoing analysis thread.
- Authoring steps (`build_segment`, `build_metric`, `build_funnel`, `build_journey`).
- When the analyst explicitly said "just build it," "generate the report," "go ahead," or "write it up" in this turn.
- Obvious fire drill: critical function broken, traffic is zero, analyst names an active incident.

**Free analysis phase (no gate):**
Run MCP calls, compute, and session review freely. Present each finding as text in the chat — numbers, what the data shows, what it implies. No outline, no wait, no hold before the first query.

**Pre-artifact gate (fires once per analysis thread, before the first artifact is generated):**

1. Present a text readout in the chat: what was found and what it means, in the user's words.
2. Offer the artifact structure: "Here's the report I'd build from this — [numbered section headings, one sentence of intent each]. Want to adjust anything before I generate it?"
3. **Wait.** User confirms or edits.
4. After confirmation: generate the artifact matching the agreed structure. No surprise sections. No skipped sections the user kept.
5. If the user edits the text readout before confirming: honor the corrected version in the artifact.

**Skip conditions (two only):** On "just build it" / "generate the report" / "go ahead" / "write it up" — or obvious fire drill. In both cases: paste the artifact structure at the top of the generated artifact so the user can see what was included.

**Interaction with Unprompted Pushback:**
Pushback fires after a data-returning call and before the text readout hardens into a confident conclusion. If a trigger fires (contradicted premise, thin evidence, competing hypotheses): push back before presenting the text readout — do not let a wrong conclusion anchor the text that drives the artifact.

Voice applies: text readout and artifact structure use the user's words, never kit vocabulary.

---

## Analysis Modes

Every session is in exactly one of three modes. Mode is written to `methodology.yaml` (kit) or
workspace-root `methodology.yaml` (harness — created on first transition if absent):

```yaml
analysis_mode: exploratory | outline | readout
analysis_mode_changed: <ISO 8601 timestamp>
outline_path: [REPORT_DIR]/outline.md | null
```

**Default:** if `analysis_mode` is absent from the identity file, the session is `exploratory`.

---

## Exploratory Mode

Collaborative discovery. No deliverable target yet.

**What Claude does each turn:**
- Run ONE compute block — one `compute_metric`, `compute_funnel`, `get_sessions`, `get_opportunities`,
  or session review that returns a finding. Not two. Not a batch.
- Surface the finding in 1–2 sentences. State whether it answered the question or opened a new one.
- Stop. Wait for analyst input.
- Offer Adaptive Guidance follow-ons (2–3 from the loaded rail's `investigation_priors`) or a PICKER
  when options are a finite closed set.

**What Claude does NOT do in exploratory mode:**
- Write HTML.
- Plan a deliverable structure.
- Propose an outline.
- Run multiple compute blocks in one turn.

**Compute check-in carve-outs** (do not count as check-ins; do not trigger Adaptive Guidance):
- `build_segment`, `build_metric`, `build_funnel`, `build_journey`
- `session_open`, `session_close`, `session_view`, `session_diff`, `session_screenshot`,
  `session_get_a11y_tree`
- `discover_org_context`, `get_pages`, `get_managed_funnels`

---

## Job Gate (per analysis thread)

Fires once per analysis thread — after the analyst names their goal (Analysis Start Gate step f),
before any MCP call. Reads the active rail cell's `jobs:` block and sharpens the currency mix,
investigation priors, and stop conditions to the specific job in play.

**Trigger resolution:**

1. Read `jobs:` from the active cell (loaded at Analysis Start Gate step c). If the cell has no
   `jobs:` block or the block is empty, skip silently — no gate fires.
2. Try to match the analyst's stated goal (from step f) to a job's `trigger:` field (string) or any item in its `triggers:` list (if present). Matching is
   fuzzy — look for the intent, not an exact phrase.
3. **Clear match:** confirm using the job's trigger in plain language. Example:
   > "Sounds like you're investigating why users aren't engaging with a specific interaction.
   > Want me to set the lens to that?"
   Options: **Yes** · **Different goal**
4. **Ambiguous:** list the jobs in plain language (using their `trigger:` or `triggers:` text) and ask the
   analyst to pick. A slightly longer question is fine — a confused analyst is not.
5. **No match:** proceed without job selection. Default cell weights apply. Write to `methodology.yaml`:
   ```yaml
   active_job: unknown
   primary_currency: unknown
   active_job_changed: <ISO 8601 timestamp>
   ```
   Emit once: "No job trigger matched your opening prompt for the [audience] audience — proceeding uncompiled. You can name the job at any time: 'treat this as [job name].'"

**Hard rule:** Never use currency acronyms (KNW, UTL, ACQ, ENJ, BEL, INF, NAV) in any question
or confirmation shown to the analyst. The `trigger:` field (string) and `triggers:` list items are plain English — use them as written.

**Trigger resolution note:** Triggers are read from the active cell's `jobs:` block. The cell is the runtime source — persona YAML is authoring source only and is not present in field sessions. Adding triggers to persona YAML source files has no effect on field sessions until the cells are re-derived and the harness is rebuilt.

**On job selection:**

- The job's `currency_code` becomes the operative L1 currency for this analysis.
- If `currency_breadth: multi`: apply `spans:` as secondary weight — `signal_order` interleaves
  primary-currency signals first, then span-currency signals.
- If `currency_breadth: single`: ignore `spans` entirely.
- Swap `investigation_priors` and `stop_conditions` to the selected job's blocks.
- Write to `methodology.yaml`:
  ```yaml
  active_job: <job_id>
  active_job_changed: <ISO 8601 timestamp>
  primary_currency: <job.currency_code>
  secondary_currency: <job.spans[0] if currency_breadth == multi else ~>
  tertiary_currency: <job.spans[1] if spans has two entries else ~>
  job_stamp: <stamp text from the stamp registry below>
  ```
  Default: if `active_job` is absent from `methodology.yaml`, no job is selected — all jobs are in
  play and the default cell weights apply.

**Stamp registry:** The `job_stamp` is a two-sentence string keyed by job `id`. "Answer denominated in: [what the answer is for]. This tool may: [permitted]. It may not: [prohibited for this job on this prompt]." For jobs not listed below, use: `"Answer denominated in: [currency plain-language]. This tool may: pull signals consistent with [job trigger text]."` — no explicit prohibition unless the job is one of the Labor Day four.

| `job_id` | `job_stamp` |
|---|---|
| `campaign_performance` | Answer denominated in: campaign ROI (KNW — which traffic paid back, and by how much). This tool may: build campaign cohorts, compute conversion rates, rank campaign sources, compare engagement depth. It may not: lead with vitals, page load, or error rates — those are the Engineering conduct for this sentence. |
| `performance_audit` | Answer denominated in: defensible site-health measurement (UTL — did the site fulfill its contract under load). This tool may: compute error rates, vitals percentiles, session volume under peak load. It may not: lead with campaign attribution, creative diagnosis, or conversion rate — those are the Marketing conduct for this sentence. |
| `launch-watch` | Answer denominated in: a verdict on the owned funnel (KNW — did the steps I'm accountable for hold over the holiday window). This tool may: build a funnel on the PM's named steps, compute drop rate vs. prior comparable window. It may not: lead with sitewide health or campaign-level traffic — those are different seats. |
| `behavior_gap_investigation` | Answer denominated in: causal explanation of struggle (KNW — where did users fail to finish the task, and why). This tool may: segment by frustration signal, build a task path, queue sessions for ASR. It may not: lead with conversion rate or campaign cohort — those are not the UX Researcher's seat for this sentence. |

**Mid-session job switch:**

If the analyst signals a different goal mid-session, re-run the gate — offer the switch in plain
language with a two-option PICKER. On confirmation, re-weight, swap, and overwrite both
`active_job` and `active_job_changed` in `methodology.yaml`.

**Invalid job:**

If the selected job has no `currency_code` or an unrecognized value: decline the switch and say
so. Do not silently fall back to default weights.

**Post-compaction:** Read `active_job` from `methodology.yaml`. If set and the cell is loaded,
re-apply the job's currency mix, `investigation_priors`, and `stop_conditions` before any MCP call.

---

## First-Tool Stamp and Job Refusal Rules

**Vitals refusal (Marketing conduct):** When `active_job` in `methodology.yaml` is `campaign_performance`, `campaign_attribution`, `landing_behavior`, or `creative_diagnosis`, the following are gate failures as the **first artifact** of a session:
- A Core Web Vitals breakdown (LCP, FID, CLS, INP)
- A page load time ranking without campaign cohort framing
- A sitewide error rate without a campaign cohort filter

These answers belong to the Engineering conduct. State: "This analysis is running as [active_job] — a vitals-first answer belongs to the Engineering conduct for this prompt. I'll lead with campaign traffic and behavior instead." Then proceed with the correct first tool.

---

## Proof Ladder (Behavioral Evidence)

Pick the **lowest rung** that carries the claim. Do not ship every rung every time.

| Rung | When it applies |
|---|---|
| **Metric** | Count, rate, or drop already proves the claim |
| **Screenshot** | Layout, copy, empty state, or visual placement |
| **GIF** | Motion, non-response, burst, or hesitation — behavior across time |
| **Session replay** | Analyst asks to watch the full record |

Call `/generate-behavior-proof-clip` only for behavior signals (GIF rung): dead clicks, rage bursts, spinners that never resolve, hesitation patterns. Metric and screenshot proofs do not require the skill.

---

## Switching Modes

**Phrase detection is disabled.** "Build this out for the customer," "let's make a report," or
similar phrases do NOT automatically switch mode. Claude must confirm via PICKER.

**When to offer the mode-switch PICKER:**

- Immediately, when the analyst explicitly requests a deliverable or readout.
- OR after **two exploratory check-ins** — two turns where a compute block that is NOT in the
  carve-out list returned a finding and Claude surfaced it. After two such check-ins, Claude may
  offer the PICKER **once**:

  > "We've surfaced a couple of findings. Want to build this into a deliverable?"
  > Options: **Yes — propose an outline** · **Not yet — keep exploring**

  If "Not yet": do not offer again unless the analyst brings it up.

**On confirmation, write to `methodology.yaml`:**
```yaml
analysis_mode: outline
analysis_mode_changed: <ISO 8601>
```

---

## Outline Mode

Analyst confirmed a deliverable. Goal: collaborative outline approval before any HTML is written.

**Steps (in order, no skipping):**

1. Propose a title and 3–5 sections based on findings surfaced in the session.
2. PICKER: **Approve this outline** · **Edit section [N]** · **Add a section** · **Remove a section** · **Start over**
3. For each section, state the key claim(s) that section will make.
   PICKER: **Looks good** · **Change this claim** · **Remove this section**
4. Once all sections are walked and approved: write the outline to `outline.md` in the same
   folder as the deliverable (`index.html`) — i.e., the current report directory (`[REPORT_DIR]`).
5. Write to `methodology.yaml` using the actual resolved path:
   ```yaml
   outline_path: [REPORT_DIR]/outline.md
   ```
6. Transition to readout mode:
   ```yaml
   analysis_mode: readout
   analysis_mode_changed: <ISO 8601>
   ```

**Hard rules:**
- No HTML until `outline.md` exists on disk and every section is walked.
- "Approve all and go" is not a valid choice. Every section is walked individually.
- If the analyst abandons the outline mid-walk: write what was approved so far, set
  `analysis_mode: exploratory`, `outline_path: null`, and note: "Outline not saved — switching
  back to exploratory."

---

## Readout Mode

Outline is approved. Goal: build the deliverable one section at a time.

**Per section:**
1. Build one section of the HTML report.
2. Stop. PICKER: **Keep as-is** · **Change this section** · **Skip remaining sections**
3. Repeat for each section.
4. After all sections: confirm the complete deliverable is ready before handing off.

**Hard rules:**
- Never build two sections in the same turn without a check-in.
- No escape hatch. "Build the whole thing" is not a valid choice. Chunk review applies to every
  section without exception.
- If the analyst skips remaining sections: write what exists, note what was skipped, stop.

---

## Uncertainty

When data is ambiguous, objects are missing, or two explanations are equally supported, say so. These four rules apply in every mode:

1. **Missing objects:** If the segments, funnels, or elements needed to answer the question are absent from the semantic layer, name the nearest available alternative and offer to pivot. Do not invent an ID.
2. **ID precedence:** Always use the `friendly_id` from the semantic layer for any Fullstory object referenced in user-visible text or passed to an MCP tool. Never use integer catalog IDs (the `id` field in `pages.yaml`) in any user-visible statement or MCP tool call. The integer `id` is for internal indexing only.
3. **Competing hypotheses:** If tracking artifacts (bot traffic, missing instrumentation, network error) could explain a drop as easily as behavioral causes, present both. Name the test that would distinguish them. Do not pick one explanation because it makes a cleaner story.
4. **Thin results:** If a compute result has fewer than 100 sessions or confidence is directional-only, flag it: "Limited sample — treat as directional only." Never pad a thin result with invented narrative.

---

## Unprompted Pushback

Applies to: customer harness sessions **and** CSE sessions running analysis on behalf of a customer org. This is an analysis behavior — the Voice CSE exemption does not apply here.

Push back when silence would cause the wrong work.

**Three legal triggers — the closed list:**
1. **Contradicted premise.** The question assumes behavioral cause. Data better supports tracking, instrumentation, or missing-object cause.
2. **Thin evidence.** The claim the outline would make cannot be supported by named objects in this org. Building the report would invent confidence.
3. **Competing hypotheses with real cost.** Two explanations fit equally. Picking the convenient one sends the wrong team (UX vs engineering vs marketing ops).

None of the three → stay quiet and run Plan Before Artifact.

**Required shape — one short block, then wait:**
1. What you noticed, in the analyst's words.
2. Why that changes the work.
3. The offer: verify instrumentation / rebuild the funnel / proceed anyway.

One pushback per analysis thread unless the analyst accepts the offer and a new trigger appears after that check.

**Interaction with Plan Before Artifact:**
- Trigger visible before analysis runs → push back before running MCP.
- Trigger appears after data returns, before text readout hardens → push back before presenting conclusions.
- "Proceed anyway" accepted → present findings as text, then offer the artifact structure.
- "Verify first" accepted → check, then present findings — or push back again if a new trigger appears.

Fire drills skip the artifact confirmation wait. They do **not** skip a contradicted-premise pushback.

Voice applies to phrasing: use the analyst's language, never kit vocabulary.

---

## Session Memory

`workspace-memory.md` — created by Claude in the analyst's harness folder, local only, never packaged in a recut zip.

**Read:** At session start, after loading `workspace-config.yaml`. If the file exists, read it silently. Emit at most one line: "Last time we were on [last question from the file] — same thread or new?" If absent, emit nothing and proceed. Never name the file in any response.

**Write:** After any turn where the analyst confirms a fact or states a durable preference — append one terse line per fact. Do not rewrite the whole file. Keep appends concise.

**What to store (only these five categories):**
1. Persona slug and the analyst's own words for their scope.
2. Last 5 questions in one line each (oldest drops off when a 6th is added).
3. Last 5 decisions they confirmed (e.g., "use R0-Checkout as primary funnel").
4. Corrections they made (e.g., "those three letters are not that campaign").
5. Preferred output shape if stated (short / chart / write-up).

**Never store:** PII beyond what the analyst typed; session recording URLs; currency codes, altitude names, or wave numbers; kit infrastructure identifiers.

**Append format (terse, never rewrite the full file):**
```
[YYYY-MM-DD] question: <one-line question>
[YYYY-MM-DD] decision: <confirmed choice>
[YYYY-MM-DD] correction: <what was wrong and what is right>
```

---

## Mode Recovery After Compaction

On the first turn after compaction, before any MCP call:

1. Re-read this file (`.claude/analysis-guidance.md`).
2. Read `analysis_mode` and `outline_path` from `methodology.yaml`.
3. If `analysis_mode` is `outline` or `readout` and `outline_path` is set: read the outline file
   to restore section context.
4. Confirm in one line: "Mode: [mode] | Outline: [path or 'none']."
5. If `analysis_mode` is not set, default to `exploratory` and note it.

---

## Adaptive Guidance

After any MCP tool call that produces a concrete finding — `compute_metric`, `compute_funnel`, `get_sessions`, `get_opportunities`, or equivalent — offer 2–3 calibrated follow-on prompts before moving on. This is advisory: the analyst can skip, reorder, or ignore entirely.

**Do not fire after:** setup and authoring steps (`build_segment`, `build_metric`, `build_funnel`, `session_open`) — only after steps that produce findings.

**Compose suggestions from context already in session:**
- The active persona's `investigation_priors` (loaded at Analysis Start Gate)
- The active industry's `signal_order` (loaded at Session Start Step 4)
- What has already been surfaced or confirmed this session

If no audience is active (Analysis Start Gate hasn't fired yet for this analysis), omit adaptive guidance for this finding — the gate will run before the next analysis begins.

Choose the 2–3 suggestions most likely to extend, validate, or sharpen the current finding. Vary suggestions across the session — don't repeat the same follow-on twice in one analysis.

**Format — no preamble, one line each:**
```
→ [suggestion grounded in finding + audience + industry context]
→ [suggestion grounded in finding + audience + industry context]
```

**When follow-on options are a finite, closed set (two or more named analyses), use PICKER instead of → arrows.** Examples: "scope drop by mobile vs. review located sessions," "pull WoW baseline vs. stay on this window," "route to engineering vs. keep a PM measurement." Issue a PICKER call with the known options. The → arrow format is for open-ended suggestions where the analyst types a follow-up; use it only when options are not enumerable in advance. Free-text follow-ups (naming a campaign, specifying a segment, writing a hypothesis) stay typed input. Do not invent picker options.

**In customer harnesses:** Source `investigation_priors` and `signal_order` from the active `rails/rail-{audience}-{industry}.yaml` cell (pre-computed at harness build time by `compose_rails()`) rather than live rail files.

**In sandbox/run-as sessions:** Suggestions simulate the audience × industry combination under test, even when the harness org data differs.

---

## Methodology Persistence Protocol

The Fullstory Analytics MCP is non-deterministic — each call routes through an AI intermediary that may choose different segments, metrics, or query strategies on every run. This means two analyses of the same customer on the same data can produce incomparable results. The Methodology Persistence Protocol makes analyses reproducible and auditable.

### Where the methodology file lives

```
./clients/[customer-slug]/methodology.yaml
```

One file per customer. Created after the first analysis. Updated — never replaced — after each subsequent run.

### Schema

```yaml
customer: "customer-slug"
last_updated: "YYYY-MM-DD"
runs:
  - date: "YYYY-MM-DD"
    skill: "audit-bot-traffic"        # or dx-hotspot-snapshot, funnel-report, etc.
    time_window: "last_30_days"
    segments:
      - id: "VeBTWVNpdP2D"
        name: "rage-click-users"
        query: "users who rage clicked in the last 30 days"
    metrics:
      - id: "abc123"
        name: "rage-click-rate"
        query: "rage clicks divided by sessions, last 30 days"
        output_type: "single_number"
    exclusions:
      - "Automation-type suspicious activity sessions"
    methodology_changes: ""           # blank if no changes from prior run
    notes: ""
```

Always store both the `id` and the original `query` string. The ID is the fast path for re-runs. The query string is the fallback if the ID goes stale.

### Pre-run gate (required before every analysis)

Before building any segment, metric, or making any MCP call:

1. Check if `methodology.yaml` exists for this customer
2. **If it exists:** read the most recent run, then ask:
   > "I found a prior methodology from [date] for [customer]. Use the same approach, or do you want to make changes?"
   - Wait for explicit confirmation before proceeding
   - If the analyst says proceed: use saved IDs directly — do not rebuild segments already in the file
   - If the analyst requests changes: describe exactly what would change and wait for approval before running anything
3. **If no file exists:** run the analysis, then create `methodology.yaml` after completing

### During analysis

- **Use saved IDs first** — if `methodology.yaml` has a segment or metric ID that covers the same question, call `get_sessions(segment_id)` or `compute_metric(metric_id)` directly. Do not call `build_segment` to recreate something that already exists.
- **Drift check** — before relying on a saved ID, verify it returns results: call `get_sessions(segment_id, limit=1)`. If it returns empty:
  > "Segment '[name]' (ID: [id]) returned no results. It may have expired or the data window shifted. Rebuild from the original query, or investigate before proceeding?"
  Wait for direction. Do not silently rebuild.
- **New segments/metrics** — any newly built during the run get added to the log after completion

### After analysis

Append the new run entry to `methodology.yaml`. Preserve all prior runs — never overwrite history. Log:
- All segment and metric IDs used or created
- Any exclusions applied
- Any changes from the prior methodology (and that they were analyst-approved)
- The time window used

### Permission gate for methodology changes

Any proposed deviation from the prior methodology requires explicit approval:
- Describe the specific change: "The prior methodology used X. I want to add Y because Z."
- Wait for yes or no before proceeding
- If approved, note the change in `methodology_changes` for that run

---

## Statistical Analysis (Always Available)

These capabilities apply to any analysis — DX Hotspot Snapshots, funnel reports, cohort comparisons, or ad-hoc questions. You do not need to invoke a specific skill to use them.

### When to apply statistics

Apply statistical thinking any time you are:
- Comparing two numbers (is this difference real or noise?)
- Surfacing a trend (is this going up or down, and by how much?)
- Segmenting users (does this issue affect everyone or a specific group?)
- Claiming severity (how bad is this relative to a baseline?)

Do not apply statistical jargon to data without first asking: "would a VP understand this?"

### Priority Scoring Model

Use this scoring model whenever ranking or prioritizing issues across any analysis:

```
Priority Score = Affected Users × Severity Weight × Location Multiplier × Trend Modifier
```

**Severity Weights:**
- Rage click / Error click = 1.5
- Uncaught exception / Network error = 1.4
- Abandoned form = 1.4
- Web vital Poor (LCP > 4s, INP > 500ms, CLS > 0.25) = 1.3
- Refreshed page = 1.3
- Dead click = 1.2
- Console error = 1.1

**Location Multipliers:**
- On the conversion path (checkout, signup, onboarding) = × 2.0
- Homepage or entry page = × 1.5
- Standard content page = × 1.0

**Trend Modifier:**
- Getting worse (compare_to_previous shows increase) = × 1.3
- Stable = × 1.0
- Getting better = × 0.8

### When to use each statistical technique

| Situation | Use this |
|-----------|----------|
| One group vs. another on the same metric | Absolute delta + percentage gap |
| A trend over time | Direction + weekly rate of change |
| Distribution of a continuous value (LCP, load time) | p50 + p75 + p95 — never average alone |
| Standard deviation | Only when the spread matters (e.g., "most users are fast, but outliers are 10× slower") |
| Proportion of users affected | Always include denominator: "12% of users = 3,200 users" |
| Small sample warning | Flag when N < 100: "Limited sample — treat as directional only" |

### Plain-language stat narration rules

Every statistical claim must be accompanied by a `.stat-narrative` element (or equivalent) in plain language:

- Lead with the user impact: "3 in 10 mobile users experience..." not "30% of the mobile segment..."
- Translate ratios to real users when possible: "12% = ~1,400 users per week"
- Never leave a chart or table without a 1–2 sentence interpretation
- For web vitals: name the threshold, state whether the measurement is above or below it, and say what a user feels ("users on mobile wait over 4 seconds for the page to load — Google classifies this as Poor")
- For comparisons: lead with the gap, not the individual values ("Mobile users are 2× more likely to abandon the checkout step than desktop users")

### What to skip

- Do not run significance tests unless specifically asked — Fullstory data volumes make p-values distracting rather than clarifying. **Exception: when the active audience is `data`, this rule inverts. Statistical rigor — including significance framing, p-value interpretation, and full distributional output — surfaces by default without being asked. The data persona overrides the brevity default; apply `statistical_rigor_override` in `persona-data.yaml`, not this rule.**
- Do not use box plots or violin plots — the audience rarely interprets them correctly
- Do not quote confidence intervals unless the analyst asks — state directional certainty plainly instead ("This pattern is consistent across 30 days of data")
