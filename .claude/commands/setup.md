# Harness Bootstrap — v1.0
# Ships as setup.md in every named-customer harness zip.
# Runs in the harness folder. This folder is the workspace — no second directory is created.

> **You are in the harness folder — this is your workspace.** Your job is to configure this
> session for the user's persona and walk them through onboarding. No directory is created outside this folder.

---

**Voice rule:** Internal scaffolding is private. In every response: never name internal files, folders, skills, templates, or kit concepts in user-visible text. Tool calls and file reads stay silent. Describe work in the user's words, not technical infrastructure terms.

---

## Principles (non-negotiable)

- **P-1: This folder is the workspace.** Never create a directory outside this folder, and never invent a new workspace location. Do not instruct the user to open Claude from a different location. Analysis starts in this session.
- **P-2: One subfolder, inside this folder.** The only folder you may create is `rails/`, inside this folder (Step 2c). Write every other file to this folder or to a folder that already exists in it.
- **P-3: Use the tool — never a plain-text menu.** Use `AskUserQuestion` (Claude Code) or
  `request_user_input` (Codex) for all selection steps. A numbered plain-text list is only
  permitted as a last resort when neither tool is available — and when used, emit a warning.
- **P-4: Industry is not a question — for named harnesses.** Read it from `harness.yaml`.
  Never ask a named harness user what industry they are.
  **Exception — OSS harnesses** (`workforce:` field absent from `harness.yaml`): ask industry
  once at first launch, in Step 2b. Never ask again after `workspace-config.yaml` exists.
- **P-5: Hard error on missing cell.** If the selected persona's rail cell is absent, stop
  and direct the user to rebuild. Do not fall back to another cell.
- **P-6: Onboarding is available in this session.** Topics use the signal order for the selected persona. After the first analytical question is answered, onboarding topics are offered as an optional follow-on — not a prerequisite gate.

---

## Step 1 — Detect Runtime Environment

Check which picker tool is available:

- If `AskUserQuestion` is available → `PICKER = AskUserQuestion`. Proceed.
- Else if `request_user_input` is available → `PICKER = request_user_input`. Proceed.
- Else → `PICKER = plain-text`. Emit: `"[WARN] Running in unsupported environment — picker tool unavailable. Using plain-text menus as fallback."` Proceed with numbered lists for all selection steps.

All subsequent picker interactions use `PICKER`.

---

## Step 2 — Read Industry from `harness.yaml`

Read `harness.yaml` from this folder. Extract `industry:`.

If `industry:` is present and non-empty → `INDUSTRY = harness.yaml industry value`. Skip to Step 3.

If `industry:` is absent or empty → discover by glob:
```
glob rails/rail-*-*.yaml → take any filename → extract the last segment before .yaml after the last -
```
If glob returns files → `INDUSTRY = discovered suffix`. Skip to Step 3.

If glob returns zero files → this is an unconfigured OSS harness. Proceed to Step 2b.

---

## Step 2b — OSS Industry Ask (OSS harness only)

Use `PICKER` to ask:

> "What industry best describes your org?"

Options (single-select):
- **Retail** — ecommerce, brick-and-mortar, omnichannel
- **Fintech** — banking, payments, insurance, brokerage
- **SaaS** — subscription software, PLG, B2B
- **Travel** — airlines, hotels, OTAs, cruises, car rental
- **Gaming** — video games, mobile apps, platforms
- **Other** — name your industry

Slug mapping:
| Selection | `INDUSTRY_SLUG` |
|-----------|----------------|
| Retail    | `retail`       |
| Fintech   | `fintech`      |
| SaaS      | `saas`         |
| Travel    | `travel`       |
| Gaming    | `gaming` — then immediately ask: "Which type? **Free-to-play / mobile gaming** or **Regulated betting / casino / sportsbook (igaming)**?" Store the answer as `GAMING_SEGMENT` (`f2p` or `igaming`). `INDUSTRY_SLUG` stays `gaming`. |
| Other     | `generic` — emit the picker once more: "What's the name of your industry? (e.g. healthcare, media, logistics)" Store verbatim as `INDUSTRY_LABEL`. `INDUSTRY_SLUG = "generic"`. |

For all on-list selections, `INDUSTRY_LABEL = INDUSTRY_SLUG`.

Set `INDUSTRY = INDUSTRY_SLUG`. Proceed to Step 2c.

---

## Step 2c — OSS Cell Copy (OSS harness only)

Check whether pre-composed cells are available for the chosen industry:

```
glob cells/{INDUSTRY_SLUG}/rail-*-{INDUSTRY_SLUG}.yaml
```

**If cells are found (expected path — derive.py ran at build time):**
1. Create `rails/` directory in this folder if it does not exist.
2. Copy every file from `cells/{INDUSTRY_SLUG}/` to `rails/`:
   - Each file is already named `rail-{audience}-{INDUSTRY_SLUG}.yaml`.
   - Overwrite any existing file with the same name.
3. Emit internally (not to user): cells copied for industry `{INDUSTRY_SLUG}`.
4. Set `CELLS_READY = true`.

**If no cells found (`cells/` absent or `cells/{INDUSTRY_SLUG}/` empty):**
1. Set `CELLS_READY = false`.
2. Emit one line to the user:
   > "Analysis rails for your industry were not found in this harness. Setup can continue, but I'll be working without calibrated industry context. Contact your Fullstory team to rebuild the harness."
3. Continue — do not stop.

(`CELLS_READY` is an internal variable for this /setup session only. It is not persisted.)

---

## Step 3 — MCP Connection Gate

Verify the agent can reach the user's Fullstory org. Call the `discover_org_context` MCP tool with a short, broad `queries` list, for example `queries: ["pages", "custom events", "revenue event"]`. The tool requires a non-empty `queries` array. 

- **If successful** → note the org name. Continue.
- **If it fails** → look at why before you say anything. Only a connection-level failure (the tool is not available, an auth error, or a transport error) means you cannot reach the org. A validation message about the arguments means retry with a non-empty `queries` list, because the connection is healthy (for example "queries array is required and must not be empty"). Only for a connection-level failure, emit:
  > "Cannot reach your Fullstory org. Make sure the Fullstory MCP server is connected in your Claude settings before continuing. Once connected, start a new session to retry setup."
  Stop. Do not continue past this step until the gate passes.

---

## Step 4 — Picker: Persona

Build the persona list from the rail cells in `rails/`:

```
glob rails/rail-*-{INDUSTRY}.yaml
→ for each filename, extract the slug between "rail-" and "-{INDUSTRY}"
→ sort alphabetically
```

Use `PICKER` with:

- Question: `"Which role best describes how you use Fullstory data?"`
- Options (map slug → display label):
  - `engineering` → `Engineering / Dev`
  - `product-mgmt` → `Product Management`
  - `ux-design` → `UX / Design`
  - `data` → `Data / Analytics`
  - `support` → `Customer Support`
  - `customer-experience` → `Customer Experience / CX`
  - `acct-mgmt` → `Account Management`
  - `marketing` → `Marketing`

Wait for selection. Store the slug as `PERSONA`.

---

## Step 5 — Load Rail Cell

Read `rails/rail-{PERSONA}-{INDUSTRY}.yaml` from this folder.

If the file is absent:
> "The rail cell for persona `{PERSONA}` / industry `{INDUSTRY}` is missing from this harness. This harness needs to be rebuilt — contact the Fullstory team."
Stop. **Do not fall back to another cell.**

Extract:
- `SIGNAL_ORDER` = `signals[*].signal` in list order (first 5 only for onboarding)
- `N_SIGNALS` = total count of `signals` entries

---

## Step 5a — Workforce (OSS only)

Check `harness.yaml` for a `workforce:` field.

- **If `workforce:` is present** (named customer harness): skip this step. Workforce is already configured. Do not ask the user.
- **If `workforce:` is absent** (OSS harness): use `PICKER` with:
  - Question: "Does your org use Fullstory Workforce Analytics?"
  - Options: **Yes** · **No / not sure**

If **Yes**:
1. Set `WORKFORCE = true`.
2. Copy `skills-library/workforce/workforce-analysis-foundation.md` to `.claude/commands/workforce-analysis-foundation.md`.
   Copy `skills-library/workforce/workforce-automation-analysis.md` to `.claude/commands/workforce-automation-analysis.md`.
   Use the Write tool. `.claude/commands/` already exists; do not create any other directory.
3. Read `skills-library/workforce/product-workforce.md` as interpretive context for Workforce analysis.
   (This file stays in `skills-library/workforce/` — it is not a command and must not go in `.claude/commands/`.)
4. Note (internal only): workforce skills and interpretive context are now active.

If **No / not sure**:
1. Set `WORKFORCE = false`.
2. Do nothing with the files — they remain in `skills-library/workforce/` only.

---

## Step 6 — Write workspace-config.yaml

Write `workspace-config.yaml` to the current folder (this is the workspace):
```yaml
persona: "{PERSONA}"
industry_slug: "{INDUSTRY_SLUG}"   # written for OSS harnesses; blank for named harnesses
industry_label: "{INDUSTRY_LABEL}" # same as industry_slug for on-list; verbatim user text for off-list
gaming_segment: "{GAMING_SEGMENT}" # f2p | igaming | "" — only set when industry_slug = gaming
workforce: true   # or false
```

For named harnesses, `INDUSTRY_SLUG`, `INDUSTRY_LABEL`, and `GAMING_SEGMENT` will be empty strings (Step 2b never runs for named harnesses). Write them as empty:
```yaml
industry_slug: ""
industry_label: ""
gaming_segment: ""
```

Do NOT write a CLAUDE.md — one already exists in this folder. Do NOT write any other file.

Echo: `"Workspace configured. Persona: {PERSONA} · Industry: {INDUSTRY} · Workforce: {WORKFORCE}."`

**If the user's opening message contained an analytical question** (any reference to a Fullstory-analyzable concept: funnel, page, campaign, conversion, drop, booking, checkout, session, device, error) — answer it now. Run analysis freely — MCP and compute without waiting. Apply the Plan Before Artifact procedure in `.claude/analysis-guidance.md` before generating any HTML deliverable or artifact. Onboarding topics become an optional follow-up after the first finding, not a prerequisite gate. If the user said only hello or did not ask an analyzable question, ask exactly one question: "What should we look at first?"

**Memory note:** As your sessions progress, Claude will create a file in this folder that persists your confirmed choices, corrections, and scope statements across sessions — so you don't need to repeat them. It stays local to this folder and is never shared with other users.

---

## Persona Slug → personas.json Mapping

When loading topic content from `personas.json` in the onboarding section, use this mapping to resolve the `personas.json` persona key from the cell slug.

<!-- This mapping is implicit in the system. Future: add a cell_slug field to personas.json to eliminate this table. -->

| Cell slug (`PERSONA`) | personas.json key |
|-----------------------|-------------------|
| `engineering` | `engineering` |
| `product-mgmt` | `product-management` |
| `ux-design` | `ux` |
| `data` | `data` |
| `support` | `customer-support` |
| `customer-experience` | `customer-success` |
| `acct-mgmt` | `sales` |
| `marketing` | `marketing` |

Store the resolved key as `PERSONAS_JSON_KEY`.

---

## Onboarding Arc (runs after workspace is written)

The onboarding arc teaches the analyst the five most relevant Fullstory capabilities for their persona and industry. It runs once, in this session, before the analyst begins their first analysis.

### Topic Order

Take `SIGNAL_ORDER[0:5]` — the first five signals from the rail cell. These are the topic keys in presentation order.

### Topic Content

For each signal key in `SIGNAL_ORDER[0:5]`:

1. Open `.claude/commands/personas.json` from this folder.
2. Find `personas[PERSONAS_JSON_KEY].topics[]` where `topics[i].type == signal_key`.
3. If a match is found: use its `type_this` and `expect` fields.
4. If no match: use the signal key as the topic name. Generate plain-language `type_this` and `expect` from context.

### Topic Delivery

For each topic (1 through 5, in order):

```
**Topic {N} of 5 — {topic_name}**

> **Try this:** {type_this}

{expect}

---
```

After each topic, pause and ask: `"Ready for the next topic, or do you have questions about this one?"` Wait before continuing.

After Topic 5:

> "You're set up. Your persona and rail cell are active in this session — start your first analysis now."

---

## MCP Connection Failures During Onboarding

If an MCP call fails during onboarding topics (not the gate in Step 3):

> "The Fullstory MCP connection dropped. Onboarding topics require live data to demonstrate effectively. Check the MCP connection and re-run the affected topic. Your workspace setup is complete — you can start analysis once the MCP is reconnected."

Do not restart the full bootstrap — workspace files are already written.
