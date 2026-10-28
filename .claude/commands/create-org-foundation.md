---
name: create-org-foundation
description: >
  Create the first org foundation for a Fullstory org: a short, dated, local record of what analysis needs to know,
  written from the Fullstory MCP and the user's answers. Use when the user asks to map or set up their org, or when
  analysis needs org context that does not exist yet. Reads from Fullstory; writes local files. No browser
  credential is needed.
---

# Create Org Foundation

Builds the first org foundation for a Fullstory org: a short, local, dated record of what an analysis needs to know about this org, written from what the Fullstory MCP returns and what the user tells you. It replaces the old semantic layer. It is lazy on purpose: it starts small and grows as analyses run.

## Principles

- **The foundation is not a semantic layer.** It records what an analysis found, built and checked, and it can be wrong, so every row carries a status and a date. It cannot answer "what funnels exist?" from a file. It does not map the whole org up front; it discovers per question and writes down what it learned.
- **Never invent an ID.** An ID is written only after an MCP tool returned it in this run. A name with no ID found is recorded as `missing`.
- **No text matching to decide what something is.** Names are recorded exactly as the customer defined them. Never infer the meaning of an element, page or event from the words in its name.
- **Never ask the user for anything that lives in their browser.** This command needs no browser credential of any kind. Everything comes through the Fullstory MCP.
- **Say what is unconfirmed.** A row you did not check this run keeps its old status and date. Gaps are stated in the summary, never hidden.
- **Reading needs no consent; saving does.** See "Before saving anything".

---

## What gets written

The org folder holds three files:

| File | What it is |
|---|---|
| `org-foundation.md` | The one file you read. Sections: Rolling summary (under 400 words), Industry (one line, naming the rail from `.claude/rails`), Platforms, Instrumentation, Business context, Known objects, Dropped, Gaps, Run log. Every row in Known objects, Instrumentation and Business context carries a status (`confirmed`, `unconfirmed`, `changed` or `missing`) and the date it was last checked. `templates/org-foundation.md` is the empty skeleton. |
| `org.yaml` | Minimal: `org_id` and `region`. The harness gate reads it to know which org ID belongs to this client. |
| `org-foundation-index.md` | Bare name and ID rows for everything in Known objects. Read it only when a name misses in the foundation. |

Find the org folder with your own file search tools: look for an `org.yaml` whose `org_id` is this org. The folder holding it is the org folder. In the kit workspace it is `clients/[Account (umbrella-id)]/[Org Name (org-id)]/`; in the open-source harness it is `clients/[org-id]/`; in a customer harness it is `org-foundation/[org-id]/`. If more than one match, list them and ask which. Never pick one yourself. Never write a copy or backup of a foundation file inside `clients/` or `org-foundation/`, because a second `org.yaml` would match the search.

---

## Capability check

Confirm the Fullstory analytics MCP is connected: call `discover_org_context` with a short `queries` list (it returns pages, elements, events and the revenue event). Only a connection-level failure (the tool is not available, an auth error, a transport error) means it is not connected; a validation message about the arguments means retry with arguments. If it is not connected, stop and tell the user: "I need the Fullstory analytics MCP connected to read your org. Connect it, then run /create-org-foundation again."

## Step 1 — Which org, and is there already a foundation

1. State which org the MCP is connected to, from the first tool response, and let the user correct you. Use that org ID as `[org-id]`.
2. Look for an existing foundation. If one exists, say so and send the user to `/update-org-foundation`; do not overwrite it. If only an old semantic layer exists for this org, send the user to `/update-org-foundation` as well: it carries the layer's IDs across.

## Step 2 — Discover what the analysis needs

Read only what the first question needs, not the whole org:

- `discover_org_context` for platforms, the revenue event and the org's instrumentation.
- `get_pages` for a count of named pages and to resolve any page the user names, or the pages in the `discover_org_context` results if `get_pages` is not offered. `discover_org_context` returns pages only when a query matches them, so on that route list what the queries found and do not claim it is a complete list of the org's pages; write the gap to Gaps.
- `get_funnel`, `get_segment`, `get_metric` or `get_journey` only to resolve an object the user named or the analysis needs. Use `regex` with a narrow pattern, not `.*` over the org.

Write each object found to Known objects with its name exactly as returned, its ID, its description (the one line the tool returns, or what its definition says), status `confirmed` and today's date. A name you searched for and did not find is recorded as `missing`, never with a guessed ID.

- **Flag duplicate names.** Compare names case-insensitively after trimming spaces: "Home Page", "HOME", "Home" and "home" are one name, and "Home|Signed Out" is a different one. If the same name appears twice in what a tool returns (for example two funnels both called "Checkout Funnel", or two pages with the same name), write both rows and start each row's Note with `DUPLICATE NAME`, followed by what tells them apart. Never merge them and never pick one.
- **Pages: record the numeric `page_id`** exactly as the pages tool returns it, in the ID column. The `friendly_id` and any other ID field go in the Note only, never in the ID column.
- **Names in the tables.** The tables use `|` as the column separator, so a name that contains a pipe is written with the pipe escaped as `\|`. A display name longer than 80 characters is cut to 80 in Known objects and Instrumentation; the ID stays whole, and the full name goes in `org-foundation-index.md`.
- **A page with an empty name.** A page can come back with an empty name and only a `url_pattern`. Record the `url_pattern` as the identifier in the Name column, keep the numeric `page_id` in the ID column, and start the row's Note with `unnamed page`. Never guess or derive a name from the URL. Do not rely on `is_user_defined`: it is absent on some pages, so never decide anything from it.
- **Capped lookups: record `total_matched`** and write the unread remainder to Gaps. Every list tool returns a total and a capped page, so for each lookup record how many matched and how many you read (for example "217 funnels matched the pattern, 5 read, 212 unread"). Unread is not absent.
- **Stale events.** A custom event not seen for 90+ days is marked `stale` in Instrumentation (and in Known objects if it appears there), with the last-seen date or age. Never mark it `confirmed`.

Read `industry` (and `persona`, if present) from this client's `customer.yaml` first, and record them on the Industry line naming the rail in `.claude/rails`. Ask only for a value that is blank or missing: do not ask for anything you can find yourself. Then ask the user for the Business context (what the business sells, who the users are, what matters most this quarter). Record what they say as `unconfirmed`: you cannot check it.

## Step 3 — Seed from traffic

Reading and ranking need no consent: this step only reads. What it does is observed behaviour, not a guarantee. `build_metric`'s own tool description says it saves a metric. On two orgs and two accounts (not tested on others), a `top_n` build with no name came back as an unsaved definition (a `metrics/create/` form with a hash id, no entry in the owned-metrics list), and `compute_metric` by that id returned the ranking. A saved metric would be a write, so the check at the end of this step is not optional.

1. Call `build_metric` with `output_type: top_n`, `time_range: last_30_days` and the query `count of clicks grouped by CSS selector of the clicked element, on <host>` (use the org's own site host, taken from `discover_org_context` or `get_pages`; never guess it. If the results give a wildcard host (for example `*.example.com`) or several hosts, list the hosts found, use the one with the most pages, and say which you chose in the Run log. Never invent a host). The words "grouped by CSS selector" matter: "grouped by element" returned an ungrouped click count. Pass NO `metric_name` and NO `metric_description`: nothing you create is labelled, and nothing is saved on purpose. Never call `update_metric`, and never use a segment tool in this step.
2. Capture the id it returns. Call `compute_metric` with that id. Record the id in the Run log so `get_metric` can re-read it later.
3. Each row is either a 12-character element ID (a named element) or a full CSS selector path (an unnamed one). Write the top 20 rows to Known objects as elements with status `unconfirmed` and the note `traffic rank, 30 days, N clicks` (the click count). Resolve an ID row to a name only through an MCP lookup (`discover_org_context` or `get_pages`) and never guess a name. A row that is a bare selector path stays a selector, and its Note says `unnamed`.
4. Do the same for custom events: `build_metric` with `output_type: top_n`, `time_range: last_30_days`, and the query `count of custom events grouped by custom event name`, again with no name and no description, then `compute_metric` by id and the top 20 to Instrumentation as `unconfirmed`.
5. Record the metric's `total` and how many rows you read; the unread rest goes to Gaps.
6. **Check that nothing was saved.** Call `get_metric` with `owned: true` and `limit: 3`. If anything new appears, tell the user what it is and stop. Do not delete it and do not carry on.

## Step 4 — Write the three files

Write `org-foundation.md`, `org.yaml` (`org_id`, `region`) and `org-foundation-index.md` in the org folder. Write the Rolling summary last: under 400 words, no object IDs, only what a reader needs to start. Add a Run log row: date, what was read, what the user confirmed, which consent was chosen.

An empty foundation is a failed build. If Known objects, Platforms and Instrumentation are all empty, say the build found nothing and why, and do not report success.

## Staying current

A `confirmed` row is re-checked when it is more than 30 days old, or when an analysis is about to depend on it, whichever comes first. Business figures are flagged once they are more than 6 months old. The 30 days is a default with no data behind it: nobody has measured how fast these objects change. If it proves wrong for an org, change the number in this command in one place.

## Before saving anything

Everything above only reads. Before saving anything in the customer's org, ask once, before the first step that saves: `build_segment`, `build_funnel`, any `update_*` call, or a metric the user asks to keep. It puts a definition in the account; it holds no session data and the user can delete it.

> **May I save things in your Fullstory account?** I will not otherwise. **Allow it:** I build what an analysis needs and tell you each time. **Read-only:** I only read; if an analysis needs something that does not exist, I say so.

Offer read-only as its own choice, record the answer in the Run log, and do not go on until the user picks one. If saving is refused, the analysis says what it lacks.

---

## Report

Tell the user, in this order: which org, what was read, how many objects are `confirmed`, `unconfirmed` and `missing`, what is under Gaps, and the next command (`/update-org-foundation`). Do not claim the org is mapped.
