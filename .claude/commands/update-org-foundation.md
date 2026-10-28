---
name: update-org-foundation
description: >
  Keep the org foundation current: re-check due rows, add what an analysis found, and carry an old semantic layer
  across. Use when an object returns nothing, when the org changed, or when a foundation row is more than 30 days old.
  Reads from Fullstory; writes local files.
---

# Update Org Foundation

Keeps an org foundation current. It re-checks the rows that are due, adds what the latest analysis found, and, if the org still has an old semantic layer, carries that layer's IDs across and offers to retire it.

## Principles

- **The foundation is not a semantic layer.** It records what an analysis found, built and checked, and it can be wrong, so every row carries a status and a date. It cannot answer "what funnels exist?" from a file. It does not map the whole org up front; it discovers per question and writes down what it learned.
- **Never invent an ID.** An ID is written only after an MCP tool returned it in this run. A name with no ID found is recorded as `missing`.
- **No text matching to decide what something is.** Names are recorded exactly as the customer defined them. Never infer the meaning of an element, page or event from the words in its name.
- **Never ask the user for anything that lives in their browser.** This command needs no browser credential of any kind. Everything comes through the Fullstory MCP.
- **Say what is unconfirmed.** A row you did not check this run keeps its old status and date. Gaps are stated in the summary, never hidden.
- **Reading needs no consent; saving does.** See "Before saving anything".

---

## What gets read and written

The org folder holds three files:

| File | What it is |
|---|---|
| `org-foundation.md` | The one file you read. Sections: Rolling summary (under 400 words), Industry (one line, naming the rail from `.claude/rails`), Platforms, Instrumentation, Business context, Known objects, Dropped, Gaps, Run log. Every row in Known objects, Instrumentation and Business context carries a status (`confirmed`, `unconfirmed`, `changed` or `missing`) and the date it was last checked. `templates/org-foundation.md` is the empty skeleton. |
| `org.yaml` | Minimal: `org_id` and `region`. The harness gate reads it to know which org ID belongs to this client. |
| `org-foundation-index.md` | Bare name and ID rows for everything in Known objects. Read it only when a name misses in the foundation. |

Find the org folder with your own file search tools: look for an `org.yaml` whose `org_id` is this org. The folder holding it is the org folder. In the kit workspace it is `clients/[Account (umbrella-id)]/[Org Name (org-id)]/`; in the open-source harness it is `clients/[org-id]/`; in a customer harness it is `org-foundation/[org-id]/`. If more than one match, list them and ask which. Never pick one yourself. Never write a copy or backup of a foundation file inside `clients/` or `org-foundation/`, because a second `org.yaml` would match the search.

---

## Capability check

Confirm the Fullstory analytics MCP is connected: call `discover_org_context` with a short `queries` list (it returns pages, elements, events and the revenue event). Only a connection-level failure (the tool is not available, an auth error, a transport error) means it is not connected; a validation message about the arguments means retry with arguments. If it is not connected, stop and tell the user: "I need the Fullstory analytics MCP connected to re-check your org. Connect it, then run /update-org-foundation again."

## Step 1 — Find the foundation

State which org the MCP is connected to and let the user correct you. Find its foundation as described above. If there is none and no old semantic layer, send the user to `/create-org-foundation` and stop.

## Step 2 — Re-check what is due

Re-check a row when it is more than 30 days old, or when the analysis in hand depends on it. For each row where a by-ID tool exists (`get_funnel`, `get_segment`, `get_metric`, `get_journey`, and `get_pages` if it is offered, or the pages in the `discover_org_context` results; elements and events have none. `discover_org_context` returns pages only when a query matches them, so on that route list what the queries found and do not claim a complete list of pages), call it. A row with no such tool stays as it is and is re-checked by the analysis that uses it. Set the status:

- `confirmed` if it returns what the row says; update the checked date.
- `changed` if it returns something different; record the new value and keep the old one in the Run log.
- `missing` if the tool no longer returns it; keep the row.

Rows you did not re-check keep their status and date. Add new objects the analysis found, with `confirmed` and today's date, its ID and its description. Apply the same rules as `/create-org-foundation`: if the same name appears twice in what a tool returns (compared case-insensitively after trimming: "Home Page", "HOME" and "home" are one name), flag both rows as `DUPLICATE NAME` and never merge them; record `total_matched` from every capped lookup and write the unread remainder to Gaps; mark a custom event not seen for 90+ days as `stale`, never `confirmed`; and for a page with an empty name, record its `url_pattern` as the identifier, keep the numeric `page_id` in the ID column, start the Note with `unnamed page`, never guess a name, and never rely on `is_user_defined` (it is absent on some pages); escape a pipe in any name as `\|`, and cut a display name longer than 80 characters to 80 with the full name in `org-foundation-index.md`. Flag Business context figures more than 6 months old and ask the user whether they still hold.

Re-checking only reads. If a row has no by-ID tool, leave it and say so.

## Step 3 — Carry an old semantic layer across (only if one exists)

An old layer is a directory holding `semantic-index.yaml` next to an `org.yaml`. Read-only; this step never touches the layer until the user says so.

1. Carry every ID in the layer's files across **without re-reading it**. Elements and events have no by-ID lookup in the MCP, and a layer can hold hundreds of IDs, so re-checking them all is neither possible nor lazy. Write the bulk as bare name and ID rows in `org-foundation-index.md`, each marked `unconfirmed`, with the note "from layer, not re-checked" and the layer's own last-generated date. Only objects the user or the analysis named go in Known objects. Put an ID in Dropped only when the layer itself marked it unusable or a duplicate, with that reason. Re-check by ID only where a getter exists (funnels, segments, metrics, journeys, pages) and the user asks; otherwise the normal 30-day re-check confirms a row when an analysis depends on it.
2. Copy `org_id` from the layer's `org.yaml` into the foundation's `org.yaml` if it is absent.
3. **Verified** means all three hold: every ID in the layer appears as a row (in Known objects or the index file) or in Dropped with a reason; the foundation parses; and the foundation's `org.yaml` carries the layer's `org_id`. Say what verified, and name any ID that is not accounted for.
4. If it is not verified, stop and say so. Leave the layer exactly as it is.
5. If it is verified, ask whether to remove the old layer. Removal needs an explicit yes that names the layer directory; "ok" or "go ahead" is not enough. Without it, change nothing.
6. Never delete `customer.yaml`, `org.yaml`, or anything the foundation owns; remove the layer's own files only.

The old `/refresh-semantic-layer` keeps working for harnesses that carry it. Do not call it from here.

## Staying current

A `confirmed` row is re-checked when it is more than 30 days old, or when an analysis is about to depend on it, whichever comes first. Business figures are flagged once they are more than 6 months old. The 30 days is a default with no data behind it: nobody has measured how fast these objects change. If it proves wrong for an org, change the number in this command in one place.

## Step 4 — Seed from traffic again (optional)

Reading and ranking need no consent: this step only reads. What it does is observed behaviour, not a guarantee. `build_metric`'s own tool description says it saves a metric. On two orgs and two accounts (not tested on others), a `top_n` build with no name came back as an unsaved definition (a `metrics/create/` form with a hash id, no entry in the owned-metrics list), and `compute_metric` by that id returned the ranking. A saved metric would be a write, so the check at the end of this step is not optional.

1. Call `build_metric` with `output_type: top_n`, `time_range: last_30_days` and the query `count of clicks grouped by CSS selector of the clicked element, on <host>` (use the org's own site host, taken from `discover_org_context` or `get_pages`; never guess it. If the results give a wildcard host (for example `*.example.com`) or several hosts, list the hosts found, use the one with the most pages, and say which you chose in the Run log. Never invent a host). The words "grouped by CSS selector" matter: "grouped by element" returned an ungrouped click count. Pass NO `metric_name` and NO `metric_description`: nothing you create is labelled, and nothing is saved on purpose. Never call `update_metric`, and never use a segment tool in this step.
2. Capture the id it returns. Call `compute_metric` with that id. Record the new id in the Run log and keep the old one so `get_metric` can re-read it later.
3. Each row is either a 12-character element ID (a named element) or a full CSS selector path (an unnamed one). Replace the traffic-ranked element rows in Known objects (rows noted `traffic rank`) with the new top 20, as elements with status `unconfirmed` and the note `traffic rank, 30 days, N clicks` (the click count). Resolve an ID row to a name only through an MCP lookup (`discover_org_context` or `get_pages`) and never guess a name. A row that is a bare selector path stays a selector, and its Note says `unnamed`.
4. Do the same for custom events: `build_metric` with `output_type: top_n`, `time_range: last_30_days`, and the query `count of custom events grouped by custom event name`, again with no name and no description, then `compute_metric` by id and the top 20 to Instrumentation as `unconfirmed`.
5. Record the metric's `total` and how many rows you read; the unread rest goes to Gaps.
6. **Check that nothing was saved.** Call `get_metric` with `owned: true` and `limit: 3`. If anything new appears, tell the user what it is and stop. Do not delete it and do not carry on.

## Before saving anything

Everything above only reads. Before saving anything in the customer's org, ask once, before the first step that saves: `build_segment`, `build_funnel`, any `update_*` call, or a metric the user asks to keep. It puts a definition in the account; it holds no session data and the user can delete it.

> **May I save things in your Fullstory account?** I will not otherwise. **Allow it:** I build what an analysis needs and tell you each time. **Read-only:** I only read; if an analysis needs something that does not exist, I say so.

Offer read-only as its own choice, record the answer in the Run log, and do not go on until the user picks one. If saving is refused, the analysis says what it lacks.

---

## Report

Tell the user which rows were re-checked, what changed, what is now `missing`, what was carried across or dropped, and what is under Gaps.
