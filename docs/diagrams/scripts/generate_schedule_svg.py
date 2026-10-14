#!/usr/bin/env python3
"""Generate the work divergence/convergence flowchart at ../schedule_flow.svg.

Run from the repository root:
    python3 docs/diagrams/scripts/generate_schedule_svg.py

Standard library only. Message: the three people split into parallel lanes after
each gate and meet again at the next one, where outputs are handed over and the
plan is recalibrated. Time runs top to bottom; people are columns; every gate is
one bar spanning all lanes. Dates come from docs/TEAM.md and docs/PLAN.md.
Same card-engine approach as generate_pipeline_svg.py: content tables on top,
boxes sized from their wrapped text below.
"""

import textwrap
from pathlib import Path
from xml.sax.saxutils import escape


OUTPUT = Path(__file__).resolve().parents[1] / "schedule_flow.svg"

INK, BODY, MUTED, LINE, PAGE = "#102a43", "#243b53", "#486581", "#475569", "#f8fafc"
GATE_STROKE, GATE_FILL = "#334155", "#edf2f7"

# Same lanes, colors and order as pipeline.svg.
LANES = {
    "hedgie": {"name": "HEDGIE", "role": "VSLAM and map research",
               "stroke": "#7a5cc0", "fill": "#f4f0ff", "text": "#5b3c9b"},
    "wobbles": {"name": "WOBBLES", "role": "Data synthesis and sensor evidence",
                "stroke": "#1f8a7e", "fill": "#e6fffa", "text": "#167567"},
    "bedrawn": {"name": "BEDRAWN", "role": "Integration and handoff",
                "stroke": "#c27a00", "fill": "#fff5e6", "text": "#a65d00"},
}
ORDER = ["hedgie", "wobbles", "bedrawn"]

# ------------------------------------------------------------- content ---
# The flow alternates: a gate (everyone meets) then a row of parallel cards.
# Card: (title, [bullets], needs or None).
FLOW = [
    ("gate", {
        "id": "C0", "title": "Mon Oct 12 · Shared preflight and interface freeze",
        "rows": [("Together", "check camera, clock and frames; record one session"),
                 ("Decide", "freeze the manifest schema, topic names and frames")],
    }),
    ("work", "Oct 12–16", {
        "hedgie": ("Visual baseline on stand-ins",
                   ["Session loader and validator", "ZED-baseline benchmark on frame dumps"],
                   "manifest schema from C0"),
        "wobbles": ("IMU validation and recording",
                    ["Measure rover frames (with Bedrawn)", "IMU checks; fusion on vs off",
                     "Record sessions with manifests"],
                    "the rover (priority until G1)"),
        "bedrawn": ("Contract and synthetic bundle",
                    ["Handoff contract draft", "Synthetic fixture bag",
                     "Footprint and offsets (with Wobbles)"],
                    "Wobbles' topic list"),
    }),
    ("gate", {
        "id": "G1", "title": "Fri Oct 16 · Fusion gate",
        "rows": [("Hand over", "Wobbles → Hedgie and Bedrawn: IMU-qualified recorded sessions"),
                 ("Decide", "area memory on or off; confirm the one owner of map → odom")],
    }),
    ("work", "Oct 16–23", {
        "hedgie": ("Map on real sessions",
                   ["BEV grid: free / occupied / unknown", "Map export for the bundle",
                    "Visual vs visual-inertial"],
                   "Wobbles' IMU session"),
        "wobbles": ("Health and TF checks",
                    ["Sensor-health report", "One publisher per TF edge"],
                    None),
        "bedrawn": ("Real-data obstacle input",
                    ["Depth → LaserScan on real bags", "Replay harness and validator"],
                    "Wobbles' recorded sessions"),
    }),
    ("gate", {
        "id": "G2", "title": "Fri Oct 23 · Perception gate",
        "rows": [("Hand over", "Hedgie → Bedrawn: map export.  Wobbles → Bedrawn: health report"),
                 ("Decide", "contract freeze candidate; cut scope if behind")],
    }),
    ("work", "Oct 23–30", {
        "hedgie": ("Map context", ["Fix the map export from the G2 review"], None),
        "wobbles": ("Evidence gaps", ["Fill missing session evidence", "Support the live demo"], None),
        "bedrawn": ("Assemble the bundle",
                    ["Bundle, README and failure cases", "Dry run Tue Oct 27 (proposed)"],
                    "Hedgie's map, Wobbles' health report"),
    }),
    ("gate", {
        "id": "G3", "title": "Fri Oct 30 · Handoff to the algorithm team",
        "rows": [("Hand over", "one replayable bundle and contract v1.0"),
                 ("Decide", "set dates for everything below")],
    }),
    ("later", "After Oct 30", {
        "hedgie": ("Mapping and research",
                   ["Phase 4 mapping from Mon Nov 2", "Loop closure, dense map, dynamic masking"],
                   None),
        "wobbles": ("GPS", ["GPS fusion comparison", "main.py exports, if reopened"], None),
        "bedrawn": ("Packages and GPS", ["Jazzy package conversion", "GPS pass-through"],
                    "Wobbles' GPS evidence"),
    }),
]

# ------------------------------------------------------------ geometry ---
MARGIN, GAP, ROW_GAP = 32, 28, 46
TIME_W, LANE_W = 120, 320
W = MARGIN + TIME_W + 24 + 3 * LANE_W + 2 * GAP + MARGIN
FONT, LINE_H, PAD = 14, 19, 16
CHAR_W = 0.54
X0 = MARGIN + TIME_W + 24                      # left edge of the lanes
LANE_X = [X0 + i * (LANE_W + GAP) for i in range(3)]
LANES_W = 3 * LANE_W + 2 * GAP


def wrap(value, width_px, size=FONT):
    return textwrap.wrap(value, max(12, int(width_px / (size * CHAR_W))), break_long_words=False) or [""]


def text(x, y, value, cls, anchor=None, fill=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    f = f' style="fill:{fill}"' if fill else ""  # style beats the stylesheet's text rule
    return f'<text x="{x:g}" y="{y:g}" class="{cls}"{a}{f}>{escape(value)}</text>'


def rect(x, y, w, h, fill, stroke, sw=2, r=12, dash=False):
    d = ' stroke-dasharray="7 5"' if dash else ""
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def arrow(x, y1, y2, dash=False):
    d = ' stroke-dasharray="7 5"' if dash else ""
    return (f'<path d="M{x:g} {y1:g} L{x:g} {y2:g}" fill="none" stroke="{LINE}" '
            f'stroke-width="2.5"{d} marker-end="url(#arrow)"/>')


def card_layout(spec):
    """Return (height, items) for a lane card; items are (kind, y offset, text)."""
    title, bullets, needs = spec
    y = PAD + 14
    items = [("title", y, title)]
    y += 6
    for b in bullets:
        for i, line in enumerate(wrap(b, LANE_W - 2 * PAD - 16)):
            y += LINE_H
            items.append(("bullet" if i == 0 else "cont", y, line))
    if needs:
        y += 8
        for line in wrap("Needs: " + needs, LANE_W - 2 * PAD, 13):
            y += LINE_H - 1
            items.append(("needs", y, line))
    return y + PAD, items


def draw_card(x, y, h, items, stroke, dash):
    out = [rect(x, y, LANE_W, h, "#ffffff", stroke, 2, 12, dash)]
    for kind, ly, value in items:
        if kind == "title":
            out.append(text(x + PAD, y + ly, value, "cardTitle"))
        elif kind == "needs":
            out.append(text(x + PAD, y + ly, value, "needs"))
        else:
            if kind == "bullet":
                out.append(text(x + PAD, y + ly, "•", "body"))
            out.append(text(x + PAD + 16, y + ly, value, "body"))
    return out


def gate_layout(spec):
    label_w, y = 92, 30
    items = [("title", y, spec["title"])]
    y += 8
    for label, value in spec["rows"]:
        for i, line in enumerate(wrap(value, LANES_W - 84 - label_w - PAD, 14)):
            y += LINE_H + 1
            items.append(("row", y, line, label if i == 0 else None))
    return y + PAD, items


def draw_gate(y, h, spec, items):
    out = [rect(X0, y, LANES_W, h, GATE_FILL, GATE_STROKE, 2.5),
           rect(X0 + PAD, y + 14, 46, 28, GATE_STROKE, GATE_STROKE, 0, 6),
           text(X0 + PAD + 23, y + 33, spec["id"], "gateId", "middle")]
    tx = X0 + 84
    for it in items:
        if it[0] == "title":
            out.append(text(tx, y + it[1], it[2], "gateTitle"))
        else:
            _, ly, line, label = it
            if label:
                out.append(text(tx, y + ly, label + ":", "gateLabel"))
            out.append(text(tx + 92, y + ly, line, "body"))
    return out


def build_svg():
    parts = [
        rect(MARGIN, 16, W - 2 * MARGIN, 104, "#ffffff", "#d9e2ec", 1.5),
        text(MARGIN + 24, 52, "October 2026: where the work splits and where it meets", "title"),
        text(MARGIN + 24, 80, "After each gate the three people work in parallel; at the next gate they meet, hand over outputs and recalibrate.", "subtitle"),
    ]
    # Legend: one sample of each symbol, on the line under the subtitle.
    ly = 104
    lx = MARGIN + 24
    parts += [rect(lx, ly - 13, 34, 16, GATE_FILL, GATE_STROKE, 2, 4),
              text(lx + 44, ly, "Gate: all three meet", "legend"),
              f'<path d="M{lx + 214} {ly - 5} L{lx + 252} {ly - 5}" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>',
              text(lx + 262, ly, "Work flows into the next step", "legend"),
              f'<path d="M{lx + 492} {ly - 5} L{lx + 530} {ly - 5}" stroke="{LINE}" stroke-width="2.5" stroke-dasharray="7 5" marker-end="url(#arrow)"/>',
              text(lx + 540, ly, "Deferred: dates set at G3", "legend"),
              text(lx + 750, ly, "“Needs” = waits on someone else", "legend")]

    # Lane headers.
    y = 140
    for lane, lx in zip(ORDER, LANE_X):
        info = LANES[lane]
        parts += [rect(lx, y, LANE_W, 62, info["fill"], info["stroke"]),
                  text(lx + LANE_W / 2, y + 28, info["name"], "lane", "middle", info["text"]),
                  text(lx + LANE_W / 2, y + 49, info["role"], "laneRole", "middle")]
    y += 62 + ROW_GAP
    # Header → C0: each person enters the shared preflight.
    for lx in LANE_X:
        parts.append(arrow(lx + LANE_W / 2, y - ROW_GAP + 2, y - 4))

    prev_bottom_by_lane = None
    for step in FLOW:
        kind = step[0]
        if kind == "gate":
            spec = step[1]
            h, items = gate_layout(spec)
            if prev_bottom_by_lane:  # convergence: every lane flows into the gate
                for lx, bottom in zip(LANE_X, prev_bottom_by_lane):
                    parts.append(arrow(lx + LANE_W / 2, bottom + 2, y - 4))
            parts += draw_gate(y, h, spec, items)
            gate_bottom = y + h
            y += h + ROW_GAP
            prev_bottom_by_lane = None
        else:
            period, cards = step[1], step[2]
            dash = kind == "later"
            laid = {lane: card_layout(cards[lane]) for lane in ORDER}
            row_h = max(h for h, _ in laid.values())
            # divergence: the gate fans out into every lane
            for lx in LANE_X:
                parts.append(arrow(lx + LANE_W / 2, gate_bottom + 2, y - 4, dash))
            parts.append(text(MARGIN + TIME_W, y + row_h / 2 + 6, period, "period", "end"))
            for lane, lx in zip(ORDER, LANE_X):
                h, items = laid[lane]
                parts += draw_card(lx, y, row_h, items, LANES[lane]["stroke"], dash)
            prev_bottom_by_lane = [y + row_h] * 3
            y += row_h + ROW_GAP

    # Footer: source and the one rule.
    fy = y - ROW_GAP + 30
    parts += [rect(MARGIN, fy, W - 2 * MARGIN, 62, "#edf2f7", "#bcccdc", 1, 12),
              text(MARGIN + 20, fy + 27, "Sources: docs/TEAM.md and docs/PLAN.md. The Oct 27 dry run is proposed, not yet in the plan.", "body"),
              text(MARGIN + 20, fy + 49, "Rule: if G1 slips, fusion fixes come first; Hedgie and Bedrawn keep working on recordings.", "body")]
    height = int(fy + 62 + 24)

    body = "\n  ".join(parts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" role="img" aria-labelledby="t d">
  <title id="t">October 2026: where the work splits and where it meets</title>
  <desc id="d">Flowchart with three lanes (Hedgie, Wobbles, Bedrawn) running top to bottom. The lanes meet at gates C0 (Oct 12), G1 (Oct 16), G2 (Oct 23) and G3 (Oct 30), where outputs are handed over and decisions are made, and split into parallel work between gates. Work after Oct 30 is deferred, with dates set at G3.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="{LINE}"/></marker>
    <style>
      text {{ fill: {BODY}; }}
      .title {{ font-size: 27px; font-weight: 700; fill: {INK}; }} .subtitle {{ font-size: 15px; fill: {MUTED}; }}
      .legend {{ font-size: 13px; fill: {MUTED}; }}
      .lane {{ font-size: 19px; font-weight: 700; }} .laneRole {{ font-size: 13px; font-weight: 700; fill: {INK}; }}
      .period {{ font-size: 16px; font-weight: 700; fill: {INK}; }}
      .gateId {{ font-size: 15px; font-weight: 700; fill: #ffffff; }}
      .gateTitle {{ font-size: 17px; font-weight: 700; fill: {INK}; }} .gateLabel {{ font-size: 14px; font-weight: 700; fill: {INK}; }}
      .cardTitle {{ font-size: 16px; font-weight: 700; fill: {INK}; }} .body {{ font-size: {FONT}px; }}
      .needs {{ font-size: 13px; fill: {MUTED}; }}
    </style>
  </defs>
  <rect width="{W}" height="{height}" fill="{PAGE}"/>
  {body}
</svg>
'''


if __name__ == "__main__":
    OUTPUT.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
