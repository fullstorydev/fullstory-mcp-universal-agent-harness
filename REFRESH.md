# Refreshing Your Semantic Layer

This harness includes a semantic layer — a map of the analytics objects your
Fullstory team has built: segments, metrics, funnels, elements, and journeys.
Claude uses this map to ground every analysis in your org's real data model
rather than guessing.

## When to refresh

Refresh the semantic layer when you notice:

- Analyses returning zero results for metrics or segments that used to work
- Messages like "Segment 'X' returned no data — it may have drifted"
- You've created significant new analytics objects in Fullstory and want
  Claude to know about them

## How to refresh

1. Open a Claude session from inside this harness directory
2. Ask it to refresh the semantic layer. The instructions are in `.claude/commands/refresh-semantic-layer.md`. If your
   tool turns that file into a command, use it (`/refresh-semantic-layer` in Claude Code). Otherwise ask it to read
   the file and follow it
3. Claude reads your org through the Fullstory connection. If no objects are
   stored yet, it asks for the names of the objects that matter most to your
   team, or for Fullstory page URLs to read them from
4. Claude updates your saved files automatically. It changes only what the
   Fullstory connection can return and keeps everything else as it was
5. You do not need to re-declare your objects unless they have changed —
   your previous selections are stored in the folder that holds your org's
   `org.yaml`

## What gets updated

Refreshing the semantic layer (`.claude/commands/refresh-semantic-layer.md`) updates, inside the folder that holds your
org's `org.yaml`:
- `semantic-index.yaml` — the master index of all objects
- `segments.yaml`, `funnels.yaml`, `metrics.yaml`, `journeys.yaml`,
  `elements.yaml`, `pages.yaml`, `events.yaml`

Your `org.yaml` provenance record is preserved. Details that come from
Fullstory dashboards cannot be refreshed through the connection, so they are
kept as of the date this harness was built.

## If problems persist after refresh

If elements still return zero results after a refresh, those objects may have
been renamed or removed from your Fullstory org. Ask Claude:

> "The segment 'X' is returning zero results even after refresh. Can you
> help me figure out if it was renamed or deleted?"

Claude will check the semantic layer and guide you through updating it.
