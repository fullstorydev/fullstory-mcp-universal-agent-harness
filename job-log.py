#!/usr/bin/env python3
"""
Fullstory Field Kit — Job Logger
Tracks every MCP artifact and task executed during org context builds.
Purpose: replayable playbook for running the same context-building play
on any org — hand the log to a new agent, it runs the identical steps.

Usage:
  python job-log.py log-step   --client "acme-corp" --org "Acme Corp (o-XXXXXX-na1)" --play org-context-root --step 1 --tool discover_org_context --params '{"queries": ["search", "checkout"]}' --purpose "Verify MCP connection" --output-doc org-context-root.md
  python job-log.py log-artifact --client "acme-corp" --org "Acme Corp (o-XXXXXX-na1)" --play org-context-root --step 5 --tool build_metric --params '{"query": "page views by page"}' --artifact-type metric --artifact-id 123456789 --artifact-name "Page Views by Page - Top N" --purpose "Traffic distribution" --output-doc org-context-root.md
  python job-log.py summarize  --client "acme-corp" --org "Acme Corp (o-XXXXXX-na1)"
  python job-log.py export-play --client "acme-corp" --org "Acme Corp (o-XXXXXX-na1)" --play org-context-root
"""

import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent
CLIENTS_DIR = WORKSPACE / "clients"


def get_log_path(client: str, org: str) -> Path:
    path = CLIENTS_DIR / client / org / "job-log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_entry(log_path: Path, entry: dict):
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Logged step {entry.get('step', '?')} to {log_path}")


def cmd_log_step(args):
    log_path = get_log_path(args.client, args.org)
    entry = {
        "timestamp": now_iso(),
        "play": args.play,
        "step": args.step,
        "tool": args.tool,
        "params": json.loads(args.params) if args.params else {},
        "artifact": None,
        "purpose": args.purpose,
        "output_document": args.output_doc,
        "notes": args.notes or "",
    }
    append_entry(log_path, entry)


def cmd_log_artifact(args):
    log_path = get_log_path(args.client, args.org)
    entry = {
        "timestamp": now_iso(),
        "play": args.play,
        "step": args.step,
        "tool": args.tool,
        "params": json.loads(args.params) if args.params else {},
        "artifact": {
            "type": args.artifact_type,
            "id": args.artifact_id,
            "name": args.artifact_name,
        },
        "purpose": args.purpose,
        "output_document": args.output_doc,
        "notes": args.notes or "",
    }
    append_entry(log_path, entry)


def cmd_summarize(args):
    log_path = get_log_path(args.client, args.org)
    if not log_path.exists():
        print(f"No log found at {log_path}")
        return

    entries = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    plays = {}
    artifacts = []

    for e in entries:
        play = e.get("play", "unknown")
        plays.setdefault(play, []).append(e)
        if e.get("artifact"):
            artifacts.append(e)

    print(f"\n=== Job Log Summary ===")
    print(f"Client: {args.client}")
    print(f"Org:    {args.org}")
    print(f"Total steps logged: {len(entries)}")
    print(f"Plays: {', '.join(plays.keys())}")
    print(f"\nArtifacts created ({len(artifacts)}):")
    for a in artifacts:
        art = a["artifact"]
        print(f"  [{art['type']}] {art['name']} (id: {art['id']}) — {a['purpose']}")

    print(f"\nSteps by play:")
    for play, steps in plays.items():
        print(f"  {play}: {len(steps)} steps")


def cmd_export_play(args):
    """Export a single play as a standalone replayable playbook JSON."""
    log_path = get_log_path(args.client, args.org)
    if not log_path.exists():
        print(f"No log found at {log_path}")
        return

    entries = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    play_steps = [e for e in entries if e.get("play") == args.play]

    if not play_steps:
        print(f"No steps found for play '{args.play}'")
        return

    playbook = {
        "play": args.play,
        "client": args.client,
        "org": args.org,
        "exported_at": now_iso(),
        "description": f"Replayable playbook for '{args.play}'. Run these steps in order against a new org to produce the same context document.",
        "steps": play_steps,
    }

    out_path = CLIENTS_DIR / args.client / args.org / f"playbook-{args.play}.json"
    out_path.write_text(json.dumps(playbook, indent=2))
    print(f"Playbook exported to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Fullstory Field Kit — Job Logger")
    sub = parser.add_subparsers(dest="command")

    # Shared org args
    def add_org_args(p):
        p.add_argument("--client", required=True, help='e.g. "Acme (u-EXAMPLE-eu1)"')
        p.add_argument("--org", required=True, help='e.g. "Acme Corp (o-XXXXXX-na1)"')

    # log-step
    p_step = sub.add_parser("log-step", help="Log a non-artifact MCP step")
    add_org_args(p_step)
    p_step.add_argument("--play", required=True)
    p_step.add_argument("--step", required=True, type=int)
    p_step.add_argument("--tool", required=True)
    p_step.add_argument("--params", default="{}")
    p_step.add_argument("--purpose", required=True)
    p_step.add_argument("--output-doc", required=True)
    p_step.add_argument("--notes", default="")

    # log-artifact
    p_art = sub.add_parser("log-artifact", help="Log an MCP artifact (metric, segment, funnel)")
    add_org_args(p_art)
    p_art.add_argument("--play", required=True)
    p_art.add_argument("--step", required=True, type=int)
    p_art.add_argument("--tool", required=True)
    p_art.add_argument("--params", default="{}")
    p_art.add_argument("--artifact-type", required=True, choices=["metric", "segment", "funnel", "session"])
    p_art.add_argument("--artifact-id", required=True)
    p_art.add_argument("--artifact-name", required=True)
    p_art.add_argument("--purpose", required=True)
    p_art.add_argument("--output-doc", required=True)
    p_art.add_argument("--notes", default="")

    # summarize
    p_sum = sub.add_parser("summarize", help="Print a summary of the job log")
    add_org_args(p_sum)

    # export-play
    p_exp = sub.add_parser("export-play", help="Export a play as a replayable playbook JSON")
    add_org_args(p_exp)
    p_exp.add_argument("--play", required=True)

    args = parser.parse_args()

    if args.command == "log-step":
        cmd_log_step(args)
    elif args.command == "log-artifact":
        cmd_log_artifact(args)
    elif args.command == "summarize":
        cmd_summarize(args)
    elif args.command == "export-play":
        cmd_export_play(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
