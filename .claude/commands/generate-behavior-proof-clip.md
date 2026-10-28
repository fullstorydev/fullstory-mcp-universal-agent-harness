# Generate Behavior Proof Clip

A kit skill. Not an MCP tool. Call it when an insight is **behavior-oriented** and the lowest sufficient proof is a short animated clip of the session — not a metric, not a still, not the full replay.

Pronounced **jif** (like the peanut butter).

---

## What this is

Humans accept proof on a ladder:

1. **Metric** — the claim (count, rate, drop).
2. **Screenshot** — the state at a moment (layout, copy, empty results).
3. **GIF** — the behavior across time (dead click, spinner that never resolves, rage burst).
4. **Session replay** — the full record.

Pick the **lowest rung that carries the claim**. Do not ship every rung every time.

| Insight nature | Lowest sufficient proof |
|---|---|
| Funnel / rate / count already proves it | Metric + session URL (optional check) |
| Layout, copy, empty state, visual placement | Screenshot + session URL |
| Motion, non-response, burst, hesitation | GIF + session URL |
| Analyst asks to watch the whole thing | Session URL only |

This skill runs only when the insight is behavior-oriented **or** the analyst asks for a clip.

It does **not** replace `/generate-dx-hotspot-snapshot`. Hotspot Phase 6b **selects** GIF-worthy sessions. This skill **renders** the clip (or degrades). Hotspot 6b should call this skill after it has a session URL + anchor event.

---

## Hard rules

- Session URL is mandatory on every outcome. No clip without a link to the session the frames came from.
- Frames-only fallback: the session URL **stands in for the GIF**. Do not pretend a `.gif` exists.
- Silent errors (hotspot Phase 3a-S) cannot be resurrected as GIF candidates because they burst.
- Cap: **15 frames**. Rate: **4 frames per second**. Window is padded around the **event timestamp(s)**, not a free-floating clock range.
- Customer-facing HTML does **not** get the GIF unless the analyst explicitly asks. Default placement: field guide Session Evidence / Highlight Clips, or the internal readout.
- Do not invent timestamps. Only use times returned by MCP session tools.
- Log which render rung fired: `ffmpeg` | `pillow` | `frames-only`.

---

## Inputs required before Phase 1

- `session_url` (or session id the kit can resolve to a URL)
- Why this session is the proof (one sentence)
- Anchor: event type + timestamp from `get_session_events` (dead click, rage click, error, etc.)
- If two events fall within ~2 seconds, treat them as **one window** spanning both

If any of those are missing, stop and ask. Do not scan the org for a "good GIF."

---

## Phase 1 — Confirm the rung

If the insight is already proven by a metric or a still, **do not run this skill**. Point at the metric or take one screenshot.

If behavior is the proof, continue.

---

## Phase 2 — Pull frames (event-anchored)

1. `session_open` on the session.
2. `get_session_events` (or equivalent transcript) around the anchor.
3. Build a pad window:
   - Center on the anchor timestamp (or the span between two close events).
   - Target ~3.75 seconds total at 4 fps = **15 frames max**.
   - Split pad before and after the anchor (approach + aftermath).
   - If the struggle is 10 seconds long, do **not** pull 40 frames. Cut to the moment.
4. `session_screenshot` at each frame timestamp. Name files `frame_01.png` … sequentially.
5. `session_close` when the pull is done.

Do not time-walk a session hoping something looks dramatic. The event is the anchor; screenshots pad the event.

---

## Phase 3 — Render (degradation ladder)

Check tools **before** claiming a GIF exists.

### Rung 1 — ffmpeg

```bash
ffmpeg -y -framerate 4 -i frame_%02d.png -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" clip.gif
```

Even dimensions are required for GIF encode. If this command exits 0 and `clip.gif` exists, stop here. Log `ffmpeg`.

### Rung 2 — Pillow

If ffmpeg is missing or fails:

```python
from pathlib import Path
from PIL import Image
frames = [Image.open(p) for p in sorted(Path(".").glob("frame_*.png"))]
frames[0].save("clip.gif", save_all=True, append_images=frames[1:], duration=250, loop=0)
```

`duration=250` is 4 fps (250 ms per frame). If `clip.gif` exists, stop. Log `pillow`.

### Rung 3 — frames-only

If neither renderer works:

- Keep the PNG sequence on disk.
- **Do not** write a fake `.gif`.
- Tell the analyst, in one block:

> I could not render the GIF on this machine. Fifteen frames are saved at `[path]`. Session: `[session_url]`. That link is the stand-in for the clip. To render locally: `ffmpeg -framerate 4 -i frame_%02d.png -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" clip.gif`

Log `frames-only`.

The frames are the deliverable. The GIF is packaging.

---

## Phase 4 — Place in the artifact

Always include, on the same evidence row:

| Field | Required |
|---|---|
| One-line description of the behavior | Yes |
| Session URL | **Always** |
| `clip.gif` | Only if rung 1 or 2 succeeded |
| Frame directory | If rung 3 |
| Render rung logged | Yes |

Default: field guide Session Evidence → Highlight Clips. Not `index.html` unless asked.

---

## Output block (copy this shape)

```
Proof clip
- Insight: [one sentence]
- Anchor event + timestamp: [from MCP]
- Session: [full session URL]
- Render: ffmpeg | pillow | frames-only
- File: clip.gif | frames at [path]
```

---

## What this skill does not do

- Does not add MCP tools.
- Does not change currency grammar or Job Gate.
- Does not generate clips for silent errors.
- Does not pull 4 fps across an entire 10-second struggle.
- Does not ship GIFs to customers by default.
