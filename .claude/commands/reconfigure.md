# /reconfigure — Update your setup
# Ships in every harness. Re-runs persona selection. Re-runs Workforce only for OSS.
# Never wipes workspace-memory.md. Never creates a new directory.

> **This skill updates your configuration.** It will ask for your role again and, if needed, whether your org uses Workforce Analytics. Your session memory and prior decisions are preserved.

---

## Principles

- **P-1: Never wipe memory.** Do not delete, truncate, or overwrite `workspace-memory.md`.
- **P-2: No mkdir.** Do not create any directory. Write only to existing locations.
- **P-3: Preserve what was not asked.** Only update the fields that were re-asked.
- **P-4: Voice.** Do not name internal files, skill names, or kit vocabulary in any response.

---

## Step 1 — Detect Runtime

Same as setup: detect AskUserQuestion, request_user_input, or plain-text fallback. Set PICKER.

---

## Step 2 — Persona Re-selection

Always runs.

Use PICKER with the same persona options as setup:
- Question: "Which role best describes how you use Fullstory data?"
- Options: Engineering / Dev · Product Management · UX / Design · Data / Analytics · Customer Support · Customer Experience / CX · Account Management · Marketing

Wait for selection. Store as `PERSONA`.

---

## Step 3 — Workforce Re-selection (OSS only)

Check `harness.yaml` for a `workforce:` field.

- **If `workforce:` is present** (named customer harness): skip this step. Workforce is CSE-locked. Do not ask.
- **If `workforce:` is absent** (OSS harness): use PICKER — "Does your org use Fullstory Workforce Analytics?" Options: **Yes** · **No / not sure**

If the answer changed from the current `workspace-config.yaml` value:

**No → Yes:**
1. Copy `skills-library/workforce/workforce-analysis-foundation.md` to `.claude/commands/`.
2. Copy `skills-library/workforce/workforce-automation-analysis.md` to `.claude/commands/`.
3. Read `skills-library/workforce/product-workforce.md` as interpretive context. (This file stays in `skills-library/workforce/` — it is not a command and must not go in `.claude/commands/`.)
4. Update `WORKFORCE = true`.

**Yes → No:**
1. Overwrite `.claude/commands/workforce-analysis-foundation.md` with empty content using the Write tool.
   Overwrite `.claude/commands/workforce-automation-analysis.md` with empty content using the Write tool. (Do not use shell `rm`.)
2. Note: interpretive context from `product-workforce.md` stays loaded for this session only.
3. Update `WORKFORCE = false`.

**No change:** proceed without touching files.

---

## Step 4 — Write workspace-config.yaml

Overwrite only the `persona:` and `workforce:` fields. Preserve any other fields.

```yaml
persona: "{PERSONA}"
workforce: true   # or false
```

Do NOT write a new CLAUDE.md. Do NOT create any new directory.

---

## Step 5 — Reload Rail

Read `INDUSTRY` from `harness.yaml`. Load `rails/rail-{PERSONA}-{INDUSTRY}.yaml` from this folder. If absent: tell the user "Your setup is missing a configuration file — contact your Fullstory team." Do not fall back.

Confirm: "Updated. Persona: {PERSONA}." No other user-visible output.

---

## "Change my setup" phrasing

This skill is also triggered by the inline phrase detection in the main session rules. If invoked via `/reconfigure` in Claude Code, follow the steps above. If triggered by phrase detection in Cowork (no slash available), run the same steps inline in the thread.
