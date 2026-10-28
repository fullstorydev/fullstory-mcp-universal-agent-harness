# Build Fullstory Field Playbook

Build a production-grade Fullstory field asset — competitive playbook, integration value story, or custom microsite — using the Fullstory Field Playbooks design system. Handles the full workflow from intake through content reasoning to final deliverable.

## When to invoke

Use this skill when asked to:
- Build a competitive playbook (Fullstory vs [Partner])
- Build an integration value story (Fullstory × [Partner])
- Build any field-facing microsite, demo page, or sales asset
- Re-skin or adapt an existing playbook for a new partner

---

## Phase 1 — Intake

**Ask all four questions in a single message. Do not proceed until you have answers to all four.**

```
Before I build this, I need four things:

1. CONTENT / DATA
   What are we building? Give me the subject — partner name, asset type
   (competitive vs. integration), and any raw content, talking points, or
   data you already have. Paste it in or describe it.

2. SOURCE URLs
   What should I read? Share links to documentation, product pages,
   competitor sites, API references, or any other sources I should review
   before writing. I'll pull and synthesize them.

3. STORY / NARRATIVE
   What's the core message? Who is the audience (AE, SE, customer, exec)?
   What should someone believe or do after reading this? Give me the
   narrative in your own words — even rough notes work.

4. FIELD GUIDE
   Should this include an internal field guide companion page?
   (Yes = internal presenter notes, talk track, discovery questions,
   objection handlers, positioning guidance. No = prospect-facing only.)
```

---

## Phase 2 — Research

After receiving intake answers:

1. **Fetch every URL** the user provided. Read them carefully.
2. **Identify**: what does the partner/subject do, who is their buyer, what are their genuine strengths, what are their gaps vs. Fullstory.
3. **Inventory Fullstory capabilities** relevant to this asset:
   - Fullcapture / retroactive querying
   - StoryAI Opportunities
   - Anywhere Warehouse (Snowflake, BigQuery, Redshift)
   - Anywhere Activation (real-time signals)
   - FS Skills / semantic decoration
   - Fullstory MCP Server
   - Subtext (IDE integration)
   - FS Conversions
   - Mobile SDKs (native iOS + Android)
4. **Note technical facts** that can be verified (source code, API docs, published specs) vs. claims that need hedging.

---

## Phase 3 — Reasoning & Collaboration

**Before writing a single line of HTML, present a content plan and get alignment.**

Structure the plan as:

```
Here's what I'm thinking before I build:

ASSET TYPE: [Competitive Playbook / Integration Value Story / Custom]
PARTNER: [Name]
AUDIENCE: [AE / SE / Customer / Exec / Mixed]

CORE ARGUMENT
[One sentence. The thing the reader should believe after this page.]

SECONDARY ARGUMENTS (2–4)
• [Supporting point 1]
• [Supporting point 2]
• [Supporting point 3]

PROPOSED SECTIONS
1. [Section name] — [one sentence on what it covers]
2. [Section name] — ...
3. ...

PARTNER STRENGTHS TO ACKNOWLEDGE
[What does the partner genuinely do well? We acknowledge this — it builds credibility.]

HONEST GAPS / WATCH-OUTS
[Where is our argument weakest? Where might the prospect push back?]

FIELD GUIDE: [Yes — will include /field-guide/ | No]

Does this match what you're going for? Any sections to add, cut, or reframe?
```

**Wait for user confirmation or edits before building. Iterate on the plan if needed.**

---

## Evidence Standards — Live Fullstory Links

**Every quantitative claim must link to the Fullstory artifact that produced it.** Reports without live links are assertions. Reports with links are evidence. This is non-negotiable.

### What to link

| Claim type | Link target | URL pattern |
|-----------|-------------|-------------|
| Session observations ("user did X") | Session replay | `https://app.fullstory.com/ui/{org}/session/{deviceId}:{sessionId}` |
| Funnel drop-off rates | Managed funnel | `https://app.fullstory.com/ui/{org}/funnels/details/{funnelId}?completed=true&completeSessions=false` |
| StoryAI Opportunity references | Opportunity detail | `https://app.fullstory.com/ui/{org}/storyai/opportunities?issue={opportunityId}` |
| Segment-scoped data | Saved segment | `https://app.fullstory.com/ui/{org}/segments/{segmentId}` |

### Where to embed links

- **Session cards**: every card gets a `↗ View in Fullstory` link via `.session-link` component — use the `session_url` returned directly by `get_sessions_for_opportunity` or `get_sessions`
- **Funnel callouts and visualizations**: add `.evidence-chip` links for each Fullstory funnel referenced
- **Methodology callouts**: list every funnel and signal type used, each with a clickable chip
- **Priority matrices**: each issue row that traces to an Opportunity gets an `.evidence-chip` link inline
- **Field guide monitoring section**: each monitoring scenario links to the relevant funnel for quick access

### How to get real IDs

1. `get_managed_funnels` → `funnel_id` values, only if it is offered
2. `get_opportunities` (org-wide or funnel-scoped) → `opportunity_id` values, only if it is offered
3. `get_sessions_for_opportunity` → `session_url` (already full URL — embed directly), only if it is offered
4. `build_segment` → `segment_id` values

If the StoryAI Opportunity tools are not offered, say once, in plain words, that this org does not have them. Leave those IDs out and say so; never invent one. The playbook continues without them.

**Never fabricate or placeholder-fill IDs.** If you don't have a real ID, say so explicitly and explain how to retrieve it.

### CSS components for evidence links

```html
<!-- Session card link (bottom of .session-card-body) -->
<a href="https://app.fullstory.com/ui/{org}/session/..." target="_blank" class="session-link">↗ View in Fullstory</a>

<!-- Inline chips (in callouts, tables, funnel headers) -->
<div class="evidence-chips">
  <a href="https://app.fullstory.com/ui/{org}/funnels/{id}" target="_blank" class="evidence-chip">↗ Purchase Funnel</a>
  <a href="https://app.fullstory.com/ui/{org}/opportunities/{id}" target="_blank" class="evidence-chip">↗ Opportunity</a>
</div>
```

```css
/* Add to <style> block */
.session-link { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; color: var(--fs-green); font-weight: 700; text-decoration: none; margin-top: 10px; padding: 5px 12px; border: 1px solid rgba(7,199,153,0.25); border-radius: 6px; background: rgba(7,199,153,0.04); transition: background 0.15s, border-color 0.15s; }
.session-link:hover { background: rgba(7,199,153,0.12); border-color: rgba(7,199,153,0.4); }
.evidence-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; }
.evidence-chips.bordered { margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(26,80,80,0.35); }
.evidence-chip { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; color: var(--text-lo); font-weight: 600; text-decoration: none; border: 1px solid var(--border); border-radius: 4px; padding: 3px 9px; letter-spacing: 0.3px; transition: color 0.12s, border-color 0.12s; }
.evidence-chip:hover { color: var(--fs-green); border-color: rgba(7,199,153,0.3); }
```

---

## Visual Pre-flight (Required Before HTML Generation)

Before writing any HTML section that includes a chart, KPI tile, or visualization:

1. Read `_component-index.md` — find the row matching each visual element needed.
2. Read the snippet file(s) from `_snippets/` for each matched row.
3. Adapt each snippet with real data. Do not invent CSS classes or inline styles.

If no row matches: use prose-only components (`.callout`, `.detail-item`, section headers) — no custom CSS for data visualization.

For statistical charts: only include if the chart answers a question funnel bars or metric tiles cannot answer on their own. Every stat component must be immediately followed by a `.stat-narrative` block.

---

## Phase 4 — Build

### File structure

```
[asset-slug]/
├── index.html           ← prospect-facing page
└── field-guide/
    └── index.html       ← internal companion (if requested)
```

Name the folder from the asset slug. Examples:
- `competitor-comparison/` for a Fullstory vs competitor playbook
- `partner-integration/` for a Fullstory × partner integration value story

### Design system

Apply the Fullstory Field Playbooks design system exactly. The full CSS reference is in `_design-system.html` and `_starter.html` in the same directory as this skill file. If those files are present, use them as the CSS source. If not, reconstruct from the spec below.

---

## Design System Reference

### Fonts
```
Prospect page: Manrope (Google Fonts) — weights 300/400/500/600/700/800
Field guide:   JetBrains Mono (Google Fonts) — weights 300/400/500/600/700
```

### CSS Variables — Prospect Page
```css
/* Fullstory brand */
--fs-deep:      #0a2828;
--fs-dark:      #0e3c3c;
--fs-mid:       #135050;
--fs-green:     #07c799;   /* primary accent */
--fs-green-dk:  #059573;
--fs-mint:      #c1f1e6;
--fs-pink:      #ff6f94;
--fs-pink-dk:   #ff2059;
--fs-pink-lt:   #ffdbe4;
--fs-purple:    #9e36f1;
--fs-purple-dk: #7729b5;
--fs-purple-lt: #e9ccff;
--fs-orange:    #ffa12f;

/* Page chrome */
--bg:           #081f1f;   /* body background */
--card:         #0d3333;   /* card background */
--card-2:       #0f3c3c;   /* hover card */
--border:       #1a5050;
--border-lt:    #1e5c5c;
--text-hi:      #e8f8f5;   /* headings, primary text */
--text-md:      #8ec8bf;   /* body text */
--text-lo:      #3d7a76;   /* labels, metadata */

/* Partner brand (set per asset) */
--partner:      [partner primary];
--partner-dk:   [partner dark];
--partner-lt:   [partner light];
```

Partner color examples:
| Partner    | --partner   | --partner-dk | --partner-lt |
|------------|-------------|--------------|--------------|
| Partner A  | `#e8334a`   | `#b91c1c`    | `#fde8eb`    |
| Partner B  | `#ff7070`   | `#d22f2f`    | `#fff0f0`    |
| Adobe      | `#fa0f00`   | `#c00000`    | `#ffe5e5`    |
| Salesforce | `#0061fe`   | `#0040aa`    | `#e5efff`    |
| Contentsquare | `#6366f1` | `#4338ca`   | `#eef2ff`    |
| Glassbox   | `#00b4d8`   | `#0077b6`    | `#e0f7ff`    |
| Quantum Metric | `#7c3aed` | `#5b21b6`  | `#ede9fe`    |

### CSS Variables — Field Guide
```css
--bg:           #080808;
--bg-2:         #0f0f0f;
--bg-3:         #141414;
--border:       #222222;
--border-hi:    #333333;
--amber:        #f59e0b;   /* primary accent */
--amber-dk:     #d97706;
--green:        #22c55e;   /* $ prompt, ✓ bullets */
--red:          #ef4444;   /* objection quotes */
--blue:         #60a5fa;
--purple:       #a78bfa;
--text-hi:      #f1f5f9;
--text-md:      #94a3b8;
--text-lo:      #475569;
--text-dim:     #334155;
--banner-bg:    #451a03;
--banner-border:#92400e;
--banner-text:  #fde68a;
```

### Component Usage Guide

**When to use each component:**

| Component | Use for |
|-----------|---------|
| `hero` | Every page. Integration uses `×` logo row; competitive uses `vs` row |
| `exec-summary` | TOC for longer assets (4+ sections) |
| `section-label + section-title + section-desc` | Every section header |
| `callout` | Verified facts, source attribution, key caveats |
| `problem-grid` | Side-by-side "what they lack / what FS has" |
| `signal-list` | Bulleted capability lists within problem cells |
| `compare-wrap` | Feature comparison table for 8+ capabilities |
| `strength-card` | "Where FS wins / where partner has edge" |
| `detail-item` | Pro/con/note within path cards |
| `path-card` | Integration architecture paths (numbered flow) |
| `scenario-card` | Use case / ROI scenarios (2-col grid) |
| `rec-card + rec-tier` | Recommendations / positioning guidance |
| `ref-cards` | Link grid to external docs (3-col) |
| `exec-link-card` | TOC cards in exec summary (right column) |
| `badge` | b-yes / b-no / b-partial / b-gated in tables |
| `tier-badge` | t-win / t-hard / t-coex / t1 / t2 / t3 in rec tiers |
| `code-block` | JSON/code examples (syntax classes: c-comment, c-key, c-string, c-num, c-method, c-punct) |
| `latency-bars` | Latency comparison for integration paths |
| `data-model` | Field-level mapping between two systems |
| `surface-wrap` | API capability reference table |

**Field guide components:**

| Component | Use for |
|-----------|---------|
| `frame-card` (first = full-width) | Primary argument + supporting frames |
| `presenter-notes` + `pn-bullets` | Per-section scripted bullets (✓ fs / ✗ gap / → point / # note) |
| `dq-item` | Discovery questions with tag + why + if-they-say |
| `obj-card` | Objection with quote header + response + re-frame |
| `pos-row` (pb-win/hard/coex/no) | Positioning guidance |
| `doc-link` | Reference docs (FS + partner) |
| `.section-cmd::before { content: '$ ' }` | Terminal section headers |

### Hero variants

**Integration (×):**
```html
<div class="hero-logos-row">
  <div class="hero-logo-block">
    <img src="https://www.fullstory.com/images/fs_logo.svg" style="height:34px; filter:brightness(0) invert(1);" />
  </div>
  <div class="hero-x">×</div>
  <div class="hero-logo-block">
    <img src="[PARTNER LOGO]" style="height:36px; filter:brightness(0) invert(1);" />
  </div>
</div>
```

**Competitive (vs):**
```html
<div class="hero-vs-row">
  <div class="hero-logo-fs">
    <img src="https://www.fullstory.com/images/fs_logo.svg" style="height:34px; filter:brightness(0) invert(1);" />
  </div>
  <div class="hero-vs">VS</div>
  <div class="hero-partner-name">[Partner]</div>
</div>
```

### Topbar variants

**Integration (co-brand logos):**
```html
<div class="topbar-logos">
  <div class="topbar-logo-fs"><img src="https://www.fullstory.com/images/fs_logo.svg" /></div>
  <div class="topbar-divider"></div>
  <img src="[PARTNER LOGO]" style="height:22px; filter:brightness(0) invert(1); opacity:0.88;" />
</div>
```

**Competitive (badge):**
```html
<div class="topbar-logos">
  <div class="topbar-logo-fs"><img src="https://www.fullstory.com/images/fs_logo.svg" /></div>
  <div class="topbar-badge">vs [Partner]</div>
</div>
```

### Hero gradient headline
```css
background: linear-gradient(130deg, #e8f8f5 0%, #a8d8cf 60%, #07c799 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

### Glow orbs (hero background depth)
```html
<div class="hero-glow-1"></div>  <!-- top-right, green -->
<div class="hero-glow-2"></div>  <!-- bottom-left, partner color -->
```
Glow 2 background: `radial-gradient(circle, rgba([PARTNER RGB],0.05) 0%, transparent 65%)`

### Footer
```html
<footer class="doc-footer">
  <div>
    <img src="https://www.fullstory.com/images/fs_logo.svg"
         style="height:16px; filter:brightness(0) invert(1); opacity:0.4; vertical-align:middle;" />
    &nbsp; [Asset Type] — [Title]
  </div>
  <div>[Category] · [Source note] · [Month Year]</div>
</footer>
```

---

## Branding Rules

- Always "Fullstory" (not "FullStory") — company rebranded
- Logo: `https://www.fullstory.com/images/fs_logo.svg` with `filter:brightness(0) invert(1)` for white version
- Primary green `#07c799` is the Fullstory brand anchor — use consistently as the positive/FS side in all comparisons
- Section labels (`section-label`) use `var(--text-lo)` not green — reserved for data/code callouts
- Hero eyebrow: green for integration, `var(--partner)` for competitive
- Never use partner colors for Fullstory content; never use green for partner content

---

## Field Guide Rules (when included)

- Lives at `[asset-folder]/field-guide/index.html`
- Uses JetBrains Mono throughout — entire page is monospace
- Fixed amber "INTERNAL — NOT FOR PROSPECT SHARING" banner at top
- Topbar format: `~/specops $ [asset-slug]/field-guide` + INTERNAL badge
- Section headers use `$ command` prefix via `.section-cmd::before { content: '$ '; }`
- Hero h1 has a blinking cursor: `<span class="cursor"></span>`
- Talk track: first `frame-card` always spans full width (primary argument), rest are 2-col
- Presenter notes use `pn-bullets` with icon variants: `.fs` (✓ green), `.gap` (✗ red), default (→ amber), `.note` (# dim)
- Objections: verbatim quote in header, 2-col response + re-frame below
- Positioning: `pos-row` with badge column (pb-win green / pb-hard amber / pb-coex purple / pb-no red)
- Footer links back to the prospect page with `→ View Prospect Page`
- The prospect page footer links to the field guide with a subtle internal link

---

## Tone & Content Rules

- Lead with honest acknowledgment of partner strengths — this builds credibility
- Technical claims must be verifiable — cite sources or hedge with "based on published documentation"
- "Widen the room" is the core competitive motion — more stakeholders = more FS value
- Structure arguments from most decisive to least — put the best stuff at the top
- Section descriptions (`section-desc`) should be 2 sentences max — set context, don't repeat the title
- Hero subtitle should be 2–3 sentences — frame the argument before the reader scrolls
- Exec summary left column: 3 paragraphs — what partner does, what FS does, what to take away
- Discovery questions: don't attack the partner — open doors to FS strengths
- Objection re-frames: one quotable sentence the presenter can say verbatim

---

## Output

Produce complete, self-contained HTML files. No external CSS dependencies beyond Google Fonts. All styles inline in a `<style>` block. All JavaScript (if any) inline in a `<script>` block at the bottom.

If a field guide is included, produce both files and clearly label which is which.

After building, confirm:
- [ ] Partner colors set via `--partner-*` variables
- [ ] Both hero variant (× or vs) and topbar variant (co-brand or badge) match asset type
- [ ] All `EDIT:` placeholders replaced with real content
- [ ] Responsive breakpoints included
- [ ] Field guide has INTERNAL banner and links back to prospect page
- [ ] Prospect page footer has subtle link to `/field-guide/` (if field guide included)
- [ ] Every session card has a real `↗ View in Fullstory` link (no placeholder session IDs)
- [ ] All funnel callouts and visualizations link to the Fullstory funnel(s) they reference
- [ ] Priority matrix rows link to Opportunities where available
- [ ] Methodology callout lists funnels and signal types with clickable evidence chips
- [ ] No fabricated or placeholder artifact IDs anywhere in the deliverable
