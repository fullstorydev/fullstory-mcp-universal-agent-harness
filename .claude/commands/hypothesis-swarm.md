# Hypothesis Swarm (Analytics Agent Rotation)

A multi-agent investigation skill for deeply scrutinizing analytical discrepancies, data anomalies, or conflicting metrics. Prevents hallucination cascade and tunnel vision by deploying a swarm of agents that independently investigate distinct hypotheses, rotate assignments, peer-review prior findings, and collaborate on a final synthesis.

## When to invoke

Activate when the user:
- Explicitly asks for an "agent rotation," "hypothesis swarm," or "multi-agent investigation"
- Surfaces a discrepancy between two Fullstory measurement objects (e.g., "this segment doesn't match the funnel")
- Asks "why doesn't X match Y?" where X and Y are quantitative claims from different tools
- Needs rigorous, multi-perspective validation before a finding goes into a customer deck

---

## Orchestrator Role

You are the Orchestrator. You do not run the analysis yourself. Your job is to:
1. Define $N$ testable hypotheses from context (default: 3)
2. Assign each a dedicated markdown file in the client's analysis folder
3. Write and execute the Workflow script below, filling in hypotheses and file paths
4. Provide live phase updates to the user
5. Synthesize final verdicts into an executive summary once all phases complete

---

## Pre-Flight — Before Writing the Workflow

### Step 1: Determine the output directory
Find the most recent analysis folder for the active customer:
```
./clients/[customer-slug]/[org-slug]/[report-slug]/
```
Swarm output files go directly in that folder alongside `index.html`.

### Step 2: Define hypotheses
Analyze the discrepancy in context. Each hypothesis must be:
- **Distinct** — no two hypotheses should have the same root cause
- **Testable** — the agent must be able to confirm or refute it with available data tools
- **Named** — use a short kebab-case slug (e.g., `denominator-growth`, `event-mismatch`, `pathway-migration`)

Write the three hypotheses to share with the user before launching:
```
H1 [slug]: [one-sentence description]
H2 [slug]: [one-sentence description]
H3 [slug]: [one-sentence description]
```

### Step 3: Confirm context bundle
Before writing the workflow, collect:
- Org ID and region (EU vs NA)
- All relevant object IDs: segment IDs, funnel IDs, metric IDs, named element IDs, journey IDs
- The specific discrepancy being investigated (quote the two conflicting data points)

---

## Workflow Script Template

Copy this template, fill in `CONTEXT`, `H1_DESC`, `H2_DESC`, `H3_DESC`, and `BASE_PATH`, then execute via the Workflow tool.

```javascript
export const meta = {
  name: 'hypothesis-swarm',
  description: 'Rotating multi-agent hypothesis investigation',
  phases: [
    { title: 'Phase 1 — Initial Investigation', detail: 'A1→H1, A2→H2, A3→H3' },
    { title: 'Phase 2 — First Rotation',        detail: 'A1→H2, A2→H3, A3→H1' },
    { title: 'Phase 3 — Final Synthesis',        detail: 'A1→H3, A2→H1, A3→H2' },
  ],
}

// ── FILL THESE IN ────────────────────────────────────────────────────────────

const BASE_PATH = './clients/[customer-slug]/[org-slug]/[report-slug]'

const CONTEXT = `
[Full context block: org ID, region, API base, replay base, the discrepancy being investigated,
all relevant object IDs with names and roles, prior analysis summary]
`

const H1_DESC = `
## Hypothesis 1: [Name]
[One paragraph description of the hypothesis]

### What to investigate
[Numbered list of specific MCP queries to run — be explicit about tool names and parameters]

### Output file
${BASE_PATH}/h1-[slug].md
`

const H2_DESC = `
## Hypothesis 2: [Name]
[One paragraph description of the hypothesis]

### What to investigate
[Numbered list of specific MCP queries to run]

### Output file
${BASE_PATH}/h2-[slug].md
`

const H3_DESC = `
## Hypothesis 3: [Name]
[One paragraph description of the hypothesis]

### What to investigate
[Numbered list of specific MCP queries to run]

### Output file
${BASE_PATH}/h3-[slug].md
`

// ── PHASE PROMPT BUILDERS — do not modify ────────────────────────────────────

const makePhase1Prompt = (agentNum, hypDesc) => `
You are Analyst Agent ${agentNum} investigating a Fullstory data discrepancy.

${CONTEXT}

Your assigned hypothesis:
${hypDesc}

This is Phase 1. The output file does not yet exist.

Instructions:
1. Use the Fullstory MCP tools to investigate your hypothesis. Run real queries — build metrics,
   compute funnels, get sessions, use discover_org_context, etc.
2. Be specific and data-driven. Quote actual numbers from tool results.
3. State clearly whether findings SUPPORT, REFUTE, or are INCONCLUSIVE for the hypothesis.
4. Use the Write tool to CREATE the output file with this structure:

# Hypothesis [N]: [Hypothesis Name]

## Agent ${agentNum} — Phase 1 — Initial Investigation

### Tools Run
[Every MCP tool called, key parameters used, and key numbers returned]

### Detailed Findings
[Full analysis with quoted data]

### Initial Verdict
[SUPPORTS / REFUTES / INCONCLUSIVE] — one paragraph explaining why

---

Your final text response to the orchestrator: one paragraph summarizing your verdict.
`

const makePhase2Prompt = (agentNum, hypDesc) => `
You are Analyst Agent ${agentNum} in a rotating multi-agent investigation.

${CONTEXT}

Your hypothesis assignment has rotated. You are now reviewing a hypothesis previously investigated
by another agent. Your job is to challenge or corroborate their work.

${hypDesc}

This is Phase 2. The file already exists with Phase 1 findings.

Instructions:
1. READ the output file first (Read tool). Understand what Phase 1 Agent found.
2. Approach with fresh eyes — look for what they missed, what challenges their conclusion,
   or additional evidence that strengthens or weakens it.
3. Run your own MCP tool queries. Do not simply repeat what Agent 1 did.
4. Read the current file content, then Write the full updated file (existing content + your new section).

Append this section:
## Agent ${agentNum} — Phase 2 — First Rotation

### Prior Findings Summary
[One sentence: what did Phase 1 Agent conclude?]

### New Tools Run
[Tools you ran that Agent 1 did not — with results]

### Counter-Analysis or Corroboration
[Where do you agree? Where do you disagree? What did Agent 1 miss?]

### Updated Verdict
[SUPPORTS / REFUTES / INCONCLUSIVE / MODIFIED] — updated assessment with reasoning

---

Your final text response to the orchestrator: one paragraph summarizing your updated verdict.
`

const makePhase3Prompt = (agentNum, hypDesc) => `
You are Analyst Agent ${agentNum} in the final phase of a rotating multi-agent investigation.

${CONTEXT}

${hypDesc}

This is Phase 3 — Final Synthesis. The file contains both Phase 1 and Phase 2 findings.

Instructions:
1. READ the output file first (Read tool). Review BOTH prior agents' findings and verdicts.
2. You are the synthesis agent. Reconcile disagreements, identify the strongest evidence,
   run any tie-breaker queries needed to resolve open questions.
3. Read the current file, then Write the full updated file (existing content + your new section).

Append this section:
## Agent ${agentNum} — Phase 3 — Final Synthesis

### Prior Verdicts
Agent 1 (Phase 1): [their verdict in one sentence]
Agent 2 (Phase 2): [their verdict in one sentence]

### Unresolved Questions
[Any open questions or disagreements between Phase 1 and Phase 2 agents]

### Final Tie-Breaker Investigation
[Any new MCP queries run to resolve those questions — with results]

### Definitive Final Verdict
[CONFIRMED / REFUTED / PARTIALLY SUPPORTED] — full reasoning

### Recommendation for the Deck
[One or two sentences: should this hypothesis shape how the finding is framed in the
customer-facing deliverable?]

---

Your final text response to the orchestrator: the Definitive Final Verdict paragraph.
`

// ── ORCHESTRATION ─────────────────────────────────────────────────────────────

phase('Phase 1 — Initial Investigation')
log('A1→H1, A2→H2, A3→H3 — launching in parallel')

const p1 = await parallel([
  () => agent(makePhase1Prompt(1, H1_DESC), { label: 'A1→H1', phase: 'Phase 1 — Initial Investigation' }),
  () => agent(makePhase1Prompt(2, H2_DESC), { label: 'A2→H2', phase: 'Phase 1 — Initial Investigation' }),
  () => agent(makePhase1Prompt(3, H3_DESC), { label: 'A3→H3', phase: 'Phase 1 — Initial Investigation' }),
])

log(`Phase 1 verdicts received. Rotating.`)

phase('Phase 2 — First Rotation')
log('A1→H2, A2→H3, A3→H1 — launching in parallel')

const p2 = await parallel([
  () => agent(makePhase2Prompt(1, H2_DESC), { label: 'A1→H2', phase: 'Phase 2 — First Rotation' }),
  () => agent(makePhase2Prompt(2, H3_DESC), { label: 'A2→H3', phase: 'Phase 2 — First Rotation' }),
  () => agent(makePhase2Prompt(3, H1_DESC), { label: 'A3→H1', phase: 'Phase 2 — First Rotation' }),
])

log(`Phase 2 verdicts received. Final rotation.`)

phase('Phase 3 — Final Synthesis')
log('A1→H3, A2→H1, A3→H2 — launching in parallel')

const p3 = await parallel([
  () => agent(makePhase3Prompt(1, H3_DESC), { label: 'A1→H3 (Synthesis)', phase: 'Phase 3 — Final Synthesis' }),
  () => agent(makePhase3Prompt(2, H1_DESC), { label: 'A2→H1 (Synthesis)', phase: 'Phase 3 — Final Synthesis' }),
  () => agent(makePhase3Prompt(3, H2_DESC), { label: 'A3→H2 (Synthesis)', phase: 'Phase 3 — Final Synthesis' }),
])

return {
  h1_final: p3[1],
  h2_final: p3[2],
  h3_final: p3[0],
  files: [
    `${BASE_PATH}/h1-[slug].md`,
    `${BASE_PATH}/h2-[slug].md`,
    `${BASE_PATH}/h3-[slug].md`,
  ]
}
```

---

## Orchestrator Output — After Completion

Once the workflow returns, read all three markdown files and produce:

```markdown
## Hypothesis Swarm — Executive Summary

**H1 [Name]:** [CONFIRMED / REFUTED / PARTIALLY SUPPORTED]
[Two sentences: the definitive finding and its implication]

**H2 [Name]:** [CONFIRMED / REFUTED / PARTIALLY SUPPORTED]
[Two sentences]

**H3 [Name]:** [CONFIRMED / REFUTED / PARTIALLY SUPPORTED]
[Two sentences]

**Net Recommendation for the Deck:**
[One paragraph: given all three verdicts, how should the discrepancy be characterized
and framed in the customer-facing deliverable?]
```

---

## Scaling to N > 3 Hypotheses

If more than 3 hypotheses are needed:
- Add additional `H[N]_DESC` blocks
- Extend each `parallel()` call with the additional agent
- Rotation pattern: each phase shifts assignments by +1 (mod N)
- Add a Phase 4 if needed for N=4 to complete the full rotation

For N=4: Phase 1 [1→H1, 2→H2, 3→H3, 4→H4], Phase 2 [1→H2, 2→H3, 3→H4, 4→H1], Phase 3 [1→H3, 2→H4, 3→H1, 4→H2], Phase 4 [1→H4, 2→H1, 3→H2, 4→H3].
