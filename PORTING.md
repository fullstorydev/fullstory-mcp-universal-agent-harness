# Porting this harness to another agent runtime

This file is written for an AI agent, and for the person asking it to set this harness up. If your runtime does not
turn `.claude/commands/` files into commands, or you are not sure whether it does, start here.

## What this harness is

It analyzes a company's Fullstory data. You tell it your role and industry once; it then helps you ask questions of your
org's data and produces findings and reports. It runs on top of the Fullstory analytics MCP server, so an agent without
that connection can read this harness but cannot analyze anything.

It is a set of instruction files plus data, not a program. The instruction files are in `.claude/commands/`. Each one
describes one job. `harness-manifest.json` lists every job, the file that holds its instructions, and what that job
needs from a runtime. If the manifest and a file disagree, the file is right.

## How to start

Your first task is workspace setup. The instructions are in `.claude/commands/setup.md`. Read that file and follow it. If
your runtime binds that file to a command, you may use the command; the file is the same either way.

Setup asks the user two things (their role, and their industry), copies the matching pre-built cells from `cells/` into
a `rails/` folder, and writes `workspace-config.yaml`. After that, the user asks a question and you pick the job from
`harness-manifest.json` whose description fits it, then read that job's file and follow it.

## What a runtime has to provide

The manifest names five capabilities. For each, find what your runtime calls it, from what it does:

| Capability | What it does | How to recognize your equivalent |
|---|---|---|
| `structured_picker` | Asks the user to choose from a short list | A question with 1 to 4 questions of 2 to 4 options each, plus an automatic free-text "Other". Use it for every selection so the user types as little as possible. |
| `file_read` | Reads a file in the harness folder | Any way to open a file by path |
| `file_write` | Creates or overwrites a file in the harness folder | Any way to write a file by path |
| `shell` | Runs a command or short script | Used by a few jobs only; the manifest says which |
| `mcp:fullstory` | Calls the Fullstory analytics MCP server | A connected MCP server exposing Fullstory tools |

Two rules govern how you use them:

1. **Use the structured picker whenever you ask the user to choose.** Only if your runtime has no such tool, ask in
   plain text and tell the user that you are doing so.
2. **If your runtime has a shell tool, use it to run shell commands.** If it has none, say which job needs one and
   stop that job rather than guessing a substitute.

Do not assume the names in the manifest apply to you. The manifest records a tool name for a runtime only where
something established it. A value of `unknown` means the runtime may well have the capability and nobody has recorded
its name; find it yourself. A value of `null` would mean it is absent, and nothing in this manifest says that today.

## What must stay true when you re-express it

- **Do not change what the analysis concludes.** Re-express how a job is invoked, not what it finds.
- **The setup questions come first.** Do not analyze before setup has written `workspace-config.yaml`.
- **Review sessions before you present a finding.** `.claude/commands/session-validation.md` requires at least five
  representative sessions to be fully inspected before you present a conclusion, or every available session if fewer
  than five exist. Do not skip it.
- **Say what you are.** If you could not use the picker, or a job needed a tool you did not have, tell the user.
- **Never write a Fullstory org ID, customer name or credential into any file you create for sharing.**
- **Do not name this folder's internal files to the user.** Describe the work in the user's words.

## What is and is not known about your runtime

Every runtime in `harness-manifest.json` is labelled `untested`. That means no one has recorded a run of this harness
there. A runtime marked `tested` has a transcript of a complete setup in the wave record. Treat the manifest as a
starting point and your own detection as the authority.

The derivation engine, `derive.py`, is not used during setup: setup copies cells that were already produced. You need
Python and the PyYAML package only to run `derive.py` yourself. `README.md` explains how.

The cloud agent is a non-target: it may load these documents, but this harness is not checked against it and no run
there has been recorded. If you are running there, treat every job that needs a capability the manifest does not
establish for your runtime as unsupported, and say so.

## If you are asked to adapt this to a new runtime

Read `harness-manifest.json`, then each `.claude/commands/*.md` file named in it. For each job, decide which capability
it needs and whether your runtime has it. Write down any job you cannot run and why. Do not edit the instruction files
to hide a gap; a harness that says plainly what it cannot do is more useful than one that claims it can do more.
