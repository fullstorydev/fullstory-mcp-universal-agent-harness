---
name: harness-feedback
description: >
  Guides a harness user through sharing structured feedback about their analysis
  experience. Activates when the user says analysis felt generic, a signal didn't
  match their role, or the framing didn't fit their industry context. Produces a
  structured YAML block to share with the Fullstory analyst. Does not write to
  any kit file directly. Invoke as /harness-feedback.
---

# /harness-feedback — Analysis Quality Feedback

This skill captures feedback about *how well the analysis was calibrated* to your
role and industry — not MCP tool errors (use `/fullstory-mcp-feedback` for those).

## When to invoke

- Surfaced signals that didn't feel relevant to your role
- Framing assumed a different audience than you are
- Recommended starting points felt generic rather than specific to your context
- You want to share what would have been more useful

## What I'll ask

1. **What felt off?** (1-3 sentences, your words)
2. **Your role/audience** (e.g., data analyst, marketing manager, engineering lead)
3. **Your industry** (e.g., retail, fintech, SaaS, travel, gaming)
4. **What would have been more useful** (optional but helpful for the Fullstory team)

## Output

I'll produce a YAML block. Copy it and share with your Fullstory contact:

```yaml
harness_feedback:
  date: "YYYY-MM-DD"
  audience: "{your role/audience slug}"
  industry: "{your industry}"
  observation: >
    {what felt off, in your words}
  suggested_correction: >
    {what would have been more useful — optional}
  routing: "derive-corrections or rail-observations"
```

Share via your usual channel (Slack, email, support ticket). Your Fullstory analyst
will route it into the kit's correction log.

## Privacy note

Do not include end-user PII, customer account identifiers, or session replay IDs.
Your feedback is about kit calibration, not specific user behavior. Signal names
like `rage_click` or `error_click` are fine.
