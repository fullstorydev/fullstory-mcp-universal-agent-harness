# fullstory-mcp-universal-agent-harness

> IT-23960 — public repository for the Fullstory universal agent harness (this ticket reference is kept from the original two-line README).

An open-source harness that gives a coding agent the context to analyse real user behaviour through the Fullstory MCP, and that is built to be taken apart.

Most of what is here is not an application. It is a set of parts:

- **Analysis skills**, written as prompts you can read, run or lift.
- **A derivation engine** (`derive.py`) that composes interpretive context for an industry and an audience.
- **Actual Session Review**, a discipline built into the skills: a finding is not reported until the sessions behind it have been looked at.
- **A currency model**, a taxonomy of what users (and analysts) are spending effort to get.

Take the parts you want. Each stands alone.

## What is in here

| Path | What it is |
|---|---|
| `.claude/commands/` | The analysis skills, one prompt per file. |
| `.claude/rails/` | Interpretive context the skills load: industry framing, personas, the currency grammar. |
| `derive.py` | The derivation engine. Reads the authored rails and the currency model and composes a cell for an industry and an audience. |
| `cells/` | Pre-composed cells, one per industry and persona pairing, so the harness needs no engine run to use. |
| `templates/` | Report and deliverable scaffolding. |
| `_workshop/field-model/` | The currency model, including `currency-signals.yaml`. This is the file the engine reads. |
| `skills-library/` | Supporting skill material. |
| `harness.yaml`, `BUILD-INFO` | Version and build identity. `BUILD-INFO` carries the git revision the harness was built from and a hash of the files it contains. |

## Getting started

You need a coding agent that can read files and run commands (built for Claude Code) and a connected Fullstory MCP server.

Open a session in this folder and run:

```
/setup
```

The agent asks about your industry and role and configures the harness. There is no file you have to edit first. To describe your Fullstory org to the agent, run `/create-org-foundation`, and `/update-org-foundation` to keep it current.

`derive.py` needs Python and PyYAML (`python3 -m pip install pyyaml`). Using the harness without running the engine needs neither.

## The skills

Each file in `.claude/commands/` is a prompt. Among them:

- `create-org-foundation` and `update-org-foundation` build and maintain a short, dated, local record of what is known about an org. The foundation is not a catalogue: it records what analyses found and built, with a status and a date on every row, and it cannot answer "what exists in this org" from a file.
- `generate-dx-hotspot-snapshot` ranks where users are struggling, backed by live data.
- `build-funnel-report` is drop-off analysis for one conversion flow.
- `build-cohort-comparison` shows how two groups experience the same product differently.
- `audit-bot-traffic` separates synthetic traffic from real users before anything is concluded.
- `hypothesis-swarm` is a rotating multi-agent investigation for discrepancies.
- `generate-behavior-proof-clip` renders a short animated clip of a session as proof of a behaviour, when a metric or a still is not enough. It is a skill, not an MCP tool.
- `fullstory-mcp-expert-guide` is always-active discipline for MCP calls: build, confirm, compute.
- `session-validation` is the Actual Session Review step (see below).
- `refresh-semantic-layer` and `build-semantic-layer` are the older lookup-file commands, deprecated in favour of the org foundation and kept for harnesses that still carry a layer.

## Actual Session Review

Aggregate counts are hypotheses. The `session-validation` skill requires a minimum of 5 representative user sessions to be reviewed for each finding that goes into a deliverable, with inspection of DOM state, console logs and network errors, before the finding is stated as confirmed. Each finding gets its own review pass, not one pass for the whole report. The skills call it before they finalise a conclusion. If you are taking the harness apart for this, `.claude/commands/session-validation.md` is the whole protocol.

## The currency model

The harness interprets behaviour through **currencies**: what a person is spending effort to obtain. The codes appear throughout the YAML, so they are defined here, from `_workshop/field-model/currency-signals.yaml` (the authoritative definitions, with the behavioural signals that show each being spent or blocked) and `.claude/rails/currency-grammar.yaml`.

There are two layers. **L2** codes describe what the end user of the product is doing. **L1** codes describe what the analyst is doing; they apply at the analyst layer and are not used for end-user jobs.

| Code | Name (as `currency-signals.yaml` defines it) | Layer | What is spent and sought (per `currency-grammar.yaml`) |
|---|---|---|---|
| `ACQ` | Transaction & Acquisition | L2 | spends money, commitment, risk; seeks goods, access, booking, completion |
| `KNW` | Information Seeking & Learning | L2 | spends attention, patience; seeks answers, certainty, comparison |
| `UTL` | Task Accomplishment & Management | L2 | spends time, effort; seeks a completed task, control over their own state |
| `ENJ` | Entertainment & Leisure | L2 | spends attention, discretionary time; seeks diversion, immersion, play |
| `BEL` | Communication & Community | L2 | spends participation, social risk; seeks connection, recognition, standing |
| `INF` | Feedback & Contribution | L2 | spends effort, goodwill; seeks reciprocity, a product that changes |
| `TRS` | Trust & Relational Continuity | L1 | the analyst spends relational capital, prior goodwill and face with the customer or stakeholder; seeks verified trustworthiness of the relationship, a recovery, or a finding's reception |
| `RSK` | Risk Containment under Reliability Threat | L1 | the analyst spends scarce attention and remaining error budget under threat of recurrence or silent drift; seeks a defensible decision to freeze, fix, or keep shipping |

`NAV` also appears in the grammar. It is not a currency: the grammar calls it a toll, overhead on the real exchange, because nobody seeks navigation for its own sake.

Each intent under a code carries a `derivation` field in `currency-signals.yaml`: `confirmed_prototype` where the intent was confirmed against a prototype, `authored_pending_prototype` where it was written and has not been confirmed. As the file stands, `KNW` has 8 confirmed intents and 5 pending, `RSK` has 4 confirmed and 3 pending, and `ACQ`, `UTL`, `ENJ`, `BEL`, `INF` and `TRS` are all pending. Treat the pending intent lists as a working model, not a measurement. Run `grep -c confirmed_prototype _workshop/field-model/currency-signals.yaml` to see the current state; the counts here describe the file at the time this README was written.

The ranking of currencies differs by industry. That ranking is what `derive.py` composes into the cells.

## Using the parts on their own

- **The skills** are plain prompts. They assume a Fullstory MCP connection and nothing else about your stack.
- **The derivation engine** reads an industry and an audience and emits composed context. It has no dependency on the skills.
- **The currency model** is a YAML file. It is useful as a taxonomy on its own.

## What this is not

This is the unconfigured, universal build. It has no org foundation, no industry set and no customer context until you run `/setup` and `/create-org-foundation`.

## Branding

The company name is written **Fullstory**.
