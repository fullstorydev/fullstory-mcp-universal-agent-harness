---
name: fullstory-mcp-feedback
description: >
  Guides the user through filing structured feedback about a Fullstory MCP workflow.
  Activate when the user wants to report something didn't work, validate something that
  did, or invokes this skill explicitly (e.g., /fullstory-mcp-feedback). Auto-extracts what's
  already in the conversation (tools called, IDs, transcript snippet), asks the user only
  for what can't be inferred, and produces a clean structured report ready to route to the
  Fullstory team.
---

# Fullstory MCP — Feedback Skill

This skill turns the LLM into a structured-feedback collector for Fullstory MCP workflows. The goal is to produce a report the Fullstory team can act on without a follow-up round — high-fidelity signal captured in the moment of failure (or success), with minimal friction for the user.

This skill is the companion to `fullstory-mcp-expert-guide`. The expert guide is the operational playbook for using the MCP reliably; this skill captures structured feedback about how that workflow went. Feedback on the expert-guide skill itself — whether it helped, did nothing, or got in the way — is one of the most useful signals you can collect.

## When to activate

Trigger this skill when any of these are true:

- The user types something like "report a bug," "this didn't work," "give feedback," "send this to Fullstory," or invokes the skill explicitly (e.g., `/fullstory-mcp-feedback`).
- A Fullstory MCP workflow just ended in an unexpected result or visible error and the user expresses dissatisfaction or asks for help reporting it.
- The user wants to send positive validation feedback ("this worked great, want to make sure they know").
- *Proactive offer (use once, don't repeat):* After a workflow that ended in a validation error, a clearly off-target result, or a user expressing frustration, you may offer once: "Want me to capture that as structured feedback?" If declined, drop it.
- **Kit Calibration (Mode C):** The analyst says "the output felt generic," "this signal didn't fit," "the audience framing was wrong," "rail calibration feedback," or similar phrases indicating the *kit's interpretation quality* was off rather than an MCP tool failure.

## Mode C — Kit Calibration

Mode C activates when interpretation quality feedback is given — distinct from Mode A
(MCP tool bug) and Mode B (positive validation). It routes to the derivation correction
log, rail observation log, or gate observation log based on classification.

### Collection flow

Ask the analyst in a single message:
1. **Observation** (free text, 1-3 sentences): What felt off?
2. **Classification** — which category best fits?
   - **(a) Derivation/signal issue** — the signal set was wrong for this audience+industry
   - **(b) Rail content/framing issue** — the language or framing felt off
   - **(c) Analysis Start Gate behavior** — gate asked for the wrong thing, pre-filled incorrectly
   - **(d) MCP tool issue** — route to Mode A
3. For (a) and (b): audience slug, industry, which signal or framing element, what would be better.
4. For (c): which gate step, what was unexpected.

### Routing

**Classification (a) — derivation/signal issue** — call `log_correction()`:

```bash
python3 - <<EOF
import sys
sys.path.insert(0, '.')
from derive import log_correction
log_correction(
    audience='{AUDIENCE}',
    industry='{INDUSTRY}',
    original_signals={ORIGINAL_SIGNAL_LIST},
    corrected_signals={CORRECTED_SIGNAL_LIST},
    analyst_note='{OBSERVATION}'
)
print("Logged to _workshop/derive-corrections.yaml")
EOF
```

**Classification (b) — rail content/framing issue** — append to `_workshop/rail-observations.yaml`:

```bash
python3 - <<EOF
import yaml
from pathlib import Path
from datetime import date

obs_file = Path('_workshop/rail-observations.yaml')
if not obs_file.exists():
    obs_file.write_text('observations: []\n')
data = yaml.safe_load(obs_file.read_text())
data['observations'].append({
    'date': date.today().isoformat(),
    'audience': '{AUDIENCE}',
    'industry': '{INDUSTRY}',
    'element': '{FRAMING_ELEMENT}',
    'observation': '{OBSERVATION}',
    'suggested_correction': '{SUGGESTION}'
})
obs_file.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))
print("Logged to _workshop/rail-observations.yaml")
EOF
```

**Classification (c) — gate behavior** — append to `_workshop/gate-observations.yaml`:

```bash
python3 - <<EOF
import yaml
from pathlib import Path
from datetime import date

obs_file = Path('_workshop/gate-observations.yaml')
if not obs_file.exists():
    obs_file.write_text('observations: []\n')
data = yaml.safe_load(obs_file.read_text())
data['observations'].append({
    'date': date.today().isoformat(),
    'gate_step': '{GATE_STEP}',
    'observation': '{OBSERVATION}',
    'expected': '{EXPECTED}'
})
obs_file.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))
print("Logged to _workshop/gate-observations.yaml")
EOF
```

**Classification (d):** Route to Mode A (existing behavior).

Note: `rail-observations.yaml` and `gate-observations.yaml` are team knowledge — not gitignored. They should be committed.

## How to run the flow

### 1. Confirm the scope

Briefly restate what feedback you're about to collect, e.g., *"Looks like you want to report on the metric you just built that returned page views instead of clicks. Want me to capture that?"* If the conversation has no recent Fullstory activity, ask what they're providing feedback about and accept a pasted transcript or description.

### 2. Auto-fill from conversation context

Before asking the user anything, scan the recent conversation and pre-fill what you can:

- **Tools called** — which MCP tools fired (`build_metric`, `compute_metric`, `session_open`, etc.)
- **Reproducibility IDs** — `metric_id`, `segment_id`, `session_id`, `client_id`, `orgId`, `region` (extracted from any `metric_url` / `segment_url` / `session_url` in the conversation)
- **Symptom** — what the agent returned or did that the user is flagging
- **Transcript snippet** — the 2–5 turns that capture the moment of failure

Show the user what you've pre-filled and ask them to correct anything that's off. This is faster and more accurate than re-collecting from scratch.

### 3. Ask only what you can't infer

For everything that isn't already in the conversation, ask the user. Use structured questions (e.g., `AskUserQuestion` in Claude Code) where the interface supports them; otherwise use plain prompts. The fields to collect:

- **Goal** *(free text)* — "What were you trying to learn from this workflow?"
- **Root cause hypothesis** *(free text, skip for positive disposition)* — "Where do you think it went wrong? Best guess is fine — engineering finds even partial hypotheses useful."
- **Expected behavior** *(free text)* — "What should have happened?" For positive disposition, repurpose as "What behavior validates this is working as designed?"
- **Disposition** *(single-select)* — captures both directions of feedback:
  - **Issues:** `blocker` / `workaround found` / `speedbump` / `minor`
  - **Validation:** `validation` (the feature works as designed end-to-end) / `positive feedback` (delight, praise, or roadmap-positive signal)
- **Expert-guide skill role** *(single-select)* — `helped` / `no effect` / `got in the way` / `wasn't loaded`
- **Contact opt-in** *(yes/no)* — "OK for the Fullstory team to reach out to clarify?"

Skip any question where the conversation context already gives you a confident answer — confirm with the user instead of asking from scratch. ("Looks like disposition here is `workaround found` since you ended up computing it manually — does that match?")

**Adapting fields for positive disposition.** When disposition is `validation` or `positive feedback`:
- Rename **Symptom** → **What worked**
- Skip **Root cause hypothesis** (or rename to **What enabled the success** if you have a clear answer)
- Reframe **Expected behavior** as **Behavior that validates this** — what was observed that confirms the feature works
- It's fine to combine `validation` with secondary engineering observations in the same report — flag them under a separate **Engineering observations** heading so engineering can route the positive signal and the small concerns independently

### 4. Generate the report

Produce the payload in the format below. Show it to the user for final review. Let them edit any field before they send it — their words, not yours, where the field is free text.

### 5. Route it

Use the routing instructions in *Where to send it* below. If those aren't filled in for the customer's environment, default to: "Paste this into whatever channel you use to communicate with the Fullstory team."

## Report format

```markdown
# Fullstory MCP feedback

**Date:** {ISO date}
**Org / region:** {orgId or "not captured"} / {region or "not captured"}

## Goal
{free text — what they were trying to learn}

## Tools called
{checklist of MCP tools that fired in the workflow, e.g.:}
- `build_metric`
- `compute_metric`
- `session_open` → `session_view` → `session_close`

## Reproducibility IDs
- `metric_id`: {value or "n/a"}
- `segment_id`: {value or "n/a"}
- `session_id`: {value or "n/a"}
- `client_id`: {value or "n/a"}

## Symptom *(or "What worked" for positive disposition)*
{what the agent returned or did — for positive feedback, describe what the
workflow produced that confirms the feature works}

## Root cause (user's hypothesis) *(skip for positive disposition)*
{free text — best guess at where it went wrong; "unknown" is acceptable}

## Expected behavior *(or "Behavior that validates this" for positive disposition)*
{what should have happened, or for positive feedback: what was observed that
confirms the feature works as designed}

## Engineering observations *(optional, for mixed positive + minor concerns)*
{any secondary observations engineering may want to route separately from the
primary disposition}

## Disposition
{Issues: blocker / workaround found / speedbump / minor}
{Validation: validation / positive feedback}

## Expert-guide skill role
{helped / no effect / got in the way / wasn't loaded}

## Transcript snippet
{2–5 turns that capture the moment of failure, PII-scrubbed — see PII note below}

## Follow-up
Contact OK: {yes / no}
```

### PII note

Before including transcript snippets or IDs, ensure they contain no end-user PII (email addresses, names, account identifiers from the customer's own users). Fullstory IDs (`metric_id`, `session_id`, etc.) are safe — they're internal handles. End-user data captured *inside* a session replay should not be pasted into the report.

## Where to send it

**Customer: edit this section to point at your feedback channel.** Defaults below are placeholders.

- **Default** — paste the report into whatever channel you use to communicate with the Fullstory team (Slack DM with your account exec, support ticket, or `mcp-feedback@fullstory.com`).
- **Suggested customizations** — replace this list with your actual routing:
  - Internal Slack channel: e.g., `#fullstory-feedback`
  - Email alias: e.g., `mcp-feedback@yourcompany.example`
  - Ticket system: e.g., Linear/Jira project `FS-MCP`

## Tone and style

- **Be efficient.** Reliability-engineering customers don't want a wizard. Ask only what you can't infer; auto-fill aggressively and confirm rather than re-collect.
- **Be specific.** Echo back what you've extracted from the conversation so the user can correct it.
- **Capture the user's words.** For free-text fields, use what they say verbatim. Engineering wants the raw signal, not your summary of it.
- **One pass, no follow-ups.** Don't drip questions across multiple turns if you can ask them all in a single structured prompt.
- **Respect a "no thanks."** If the user declines the proactive offer, don't re-offer in the same session.

## Composes with

- `fullstory-mcp-expert-guide` — the operational playbook. Feedback on whether that skill helped or got in the way is one of the highest-value signals captured here.

---

## Activation Conditions

**`fullstory-mcp-feedback`** activates when a Fullstory MCP workflow ends unexpectedly or the user wants to report something. Auto-extracts tools called, IDs, and the transcript snippet from context, then guides collection of the remaining fields. Produces a structured report ready to route to the Fullstory team. Can also capture positive validation feedback.
