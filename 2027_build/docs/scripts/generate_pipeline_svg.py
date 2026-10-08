#!/usr/bin/env python3
"""Generate the simple pipeline diagram at ../pipeline.svg.

Run from the repository root:
    python3 2027_build/docs/scripts/generate_pipeline_svg.py

Standard library only. Design rule: one short card per person per phase, four
labelled lines per card (IN, DOES, OUT, NEEDS), one line each. If a card needs
more, the detail belongs in that person's plan document, not in this picture.

Layout: boxes are sized from their wrapped text, so editing a sentence never
causes overflow. Content lives in the tables below; the drawing code is generic.
"""

import textwrap
from pathlib import Path
from xml.sax.saxutils import escape


OUTPUT = Path(__file__).resolve().parents[1] / "pipeline.svg"

INK, BODY, MUTED, LINE, PAGE = "#102a43", "#243b53", "#486581", "#475569", "#f8fafc"

# People are the lanes; each person's broad responsibility sits under their name.
LANES = {
    "hedgie": {"name": "HEDGIE", "role": "VSLAM and map research",
               "stroke": "#7a5cc0", "fill": "#f4f0ff", "text": "#5b3c9b"},
    "wobbles": {"name": "WOBBLES", "role": "Data synthesis and sensor evidence",
                "stroke": "#1f8a7e", "fill": "#e6fffa", "text": "#167567"},
    "bedrawn": {"name": "BEDRAWN", "role": "Integration and handoff",
                "stroke": "#c27a00", "fill": "#fff5e6", "text": "#a65d00"},
}
ORDER = ["hedgie", "wobbles", "bedrawn"]

PHASES = [
    ("0 · Shared preflight", "small, required", "#38a169", "#e6fcf5"),
    ("1 · Parallel work", "everyone starts at once", "#3182ce", "#ebf8ff"),
    ("2 · Integration gate", "prove it fits together", "#dd6b20", "#fffaf0"),
    ("3 · Package conversion", "only what is proven", "#805ad5", "#faf5ff"),
]

CHIP = {"IN": "#2b6cb0", "DOES": "#4a5568", "OUT": "#2f855a", "NEEDS": "#c05621"}

# ------------------------------------------------------------- content ---
PREFLIGHT = {
    "title": "Check the basics once",
    "rows": [
        ("DOES", "Agree the camera/IMU clock, the frame names, and the mounting geometry"),
        ("OUT", "One replayable recording plus a small session manifest"),
        ("NEEDS", "ZED camera or an SVO file; ROS 2 Jazzy set up"),
    ],
    "note": "Not a camera-only phase. It only gives IMU data meaning.",
}

PARALLEL = {
    "hedgie": {
        "title": "Offline SLAM benchmark",
        "rows": [
            ("IN", "Recorded session files (or a labelled fixture)"),
            ("DOES", "Build visual-only SLAM, loop closures and a map"),
            ("OUT", "Trajectory, map and metrics compared with the ZED baseline"),
            ("NEEDS", "Nothing to start; a real session from Wobbles later"),
        ],
    },
    "wobbles": {
        "title": "IMU validation and recording",
        "rows": [
            ("IN", "ZED camera and IMU, live or from an SVO"),
            ("DOES", "Record sessions, check IMU timing and axes, compare camera-only with IMU-fused"),
            ("OUT", "Replayable session, manifest, TF and IMU quality report"),
            ("NEEDS", "The shared preflight"),
        ],
    },
    "bedrawn": {
        "title": "Handoff bundle fixture",
        "rows": [
            ("IN", "Synthetic data now; Wobbles' topics later"),
            ("DOES", "Turn depth into obstacle scans and write down the handoff contract"),
            ("OUT", "Replayable obstacle bundle with rover footprint"),
            ("NEEDS", "Wobbles' topic and TF contract at the gate; Hedgie's map is optional"),
        ],
    },
}

INTEGRATION = {
    "title": "One session, all three",
    "rows": [
        ("IN", "Each person's finished parallel work"),
        ("DOES", "Freeze the manifest, replay one session end to end, swap synthetic data for real topics, pick one owner of map → odom"),
        ("OUT", "One validated Navigation Data & VSLAM Handoff Bundle"),
    ],
    "note": "Passes only if time and frames agree, replay repeats, and there is no duplicate TF owner.",
}

CONVERSION = {
    "title": "Make it real ROS 2",
    "rows": [
        ("IN", "Slices that passed the gate"),
        ("DOES", "Move each proven slice into its ROS 2 package, one slice per pull request"),
        ("OUT", "Final packages in 2027_build/"),
    ],
    "note": "No migrating legacy code just to tidy folders.",
}

HANDOFFS = [
    ("wobbles", "hedgie", "session files: recording, manifest, calibration"),
    ("wobbles", "bedrawn", "ROS topics, TF and bag replay"),
    ("hedgie", "bedrawn", "map export (optional)"),
]

# ------------------------------------------------------------ geometry ---
W = 1500
MARGIN = 24
GAP = 22
LANE_W = 170
COL_W = [232, 440, 272, 244]
FONT, LINE_H, PAD, LABEL_W = 14, 19, 16, 62
CHAR_W = 0.53


def wrap(value, width_px, size=FONT):
    return textwrap.wrap(value, max(12, int(width_px / (size * CHAR_W))), break_long_words=False) or [""]


def text(x, y, value, cls, anchor=None, fill=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    f = f' style="fill:{fill}"' if fill else ""  # style beats the stylesheet's text rule
    return f'<text x="{x:g}" y="{y:g}" class="{cls}"{a}{f}>{escape(value)}</text>'


def rect(x, y, w, h, fill, stroke, sw=2, r=12):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def arrow(points, color=LINE, width=2.5):
    d = "M" + " L".join(f"{x:g} {y:g}" for x, y in points)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" marker-end="url(#arrow)"/>'


class Card:
    """A titled box with chip-labelled rows. Height comes from the wrapped text."""

    def __init__(self, spec, width, stroke):
        self.width, self.stroke = width, stroke
        y = PAD + 14
        self.items = [("title", y, spec["title"])]
        for kind, value in spec["rows"]:
            y += 12
            for i, line in enumerate(wrap(value, width - 2 * PAD - LABEL_W)):
                y += LINE_H
                self.items.append(("row", y, line, kind if i == 0 else None))
        if spec.get("note"):
            y += 8
            for line in wrap(spec["note"], width - 2 * PAD, 13):
                y += LINE_H - 1
                self.items.append(("note", y, line))
        self.height = y + PAD + 4

    def draw(self, x, y, h=None):
        out = [rect(x, y, self.width, h or self.height, "#ffffff", self.stroke)]
        for it in self.items:
            if it[0] == "title":
                out.append(text(x + PAD, y + it[1], it[2], "cardTitle"))
            elif it[0] == "note":
                out.append(text(x + PAD, y + it[1], it[2], "note"))
            else:
                _, ly, line, kind = it
                if kind:
                    out += [rect(x + PAD, y + ly - 12, 50, 17, CHIP[kind], CHIP[kind], 0, 4),
                            text(x + PAD + 25, y + ly, kind, "chip", "middle")]
                out.append(text(x + PAD + LABEL_W, y + ly, line, "body"))
        return "\n  ".join(out)


def build_svg():
    xs, x = [], MARGIN + LANE_W + GAP
    for w in COL_W:
        xs.append(x)
        x += w + GAP
    parts = [
        rect(MARGIN, 16, W - 2 * MARGIN, 76, "#ffffff", "#d9e2ec", 1.5),
        text(MARGIN + 24, 50, "2027 Navigation Data & VSLAM: who does what", "title"),
        text(MARGIN + 24, 77, "Three people start in parallel, then prove one replayable bundle for the next subteam.", "subtitle"),
    ]

    head_y = 112
    for (title, sub, stroke, fill), cx, w in zip(PHASES, xs, COL_W):
        parts += [rect(cx, head_y, w, 58, fill, stroke),
                  text(cx + w / 2, head_y + 25, title, "phase", "middle"),
                  text(cx + w / 2, head_y + 46, sub, "phaseSub", "middle")]

    cards = {lane: Card(PARALLEL[lane], COL_W[1], LANES[lane]["stroke"]) for lane in ORDER}
    pre = Card(PREFLIGHT, COL_W[0], PHASES[0][2])
    gate = Card(INTEGRATION, COL_W[2], PHASES[2][2])
    conv = Card(CONVERSION, COL_W[3], PHASES[3][2])
    row_h = {lane: max(cards[lane].height, 130) for lane in ORDER}
    lanes_h = sum(row_h.values()) + 2 * GAP
    total = max(lanes_h, pre.height, gate.height, conv.height)
    row_h["bedrawn"] += total - lanes_h  # absorb any slack so lanes end flush with the tall cards

    top = head_y + 58 + GAP
    y = top
    for lane in ORDER:
        info, h = LANES[lane], row_h[lane]
        parts += [rect(MARGIN, y, LANE_W, h, info["fill"], info["stroke"]),
                  text(MARGIN + LANE_W / 2, y + 38, info["name"], "lane", "middle", info["text"])]
        for i, line in enumerate(wrap(info["role"], LANE_W - 28, 13)):
            parts.append(text(MARGIN + LANE_W / 2, y + 64 + i * 18, line, "laneRole", "middle"))
        parts += [cards[lane].draw(xs[1], y, h),
                  arrow([(xs[1] + COL_W[1] + 2, y + 36), (xs[2] - 3, y + 36)])]
        y += h + GAP
    parts += [pre.draw(xs[0], top, total), gate.draw(xs[2], top, total), conv.draw(xs[3], top, total),
              arrow([(xs[0] + COL_W[0] + 2, top + 36), (xs[1] - 3, top + 36)]),
              arrow([(xs[2] + COL_W[2] + 2, top + 36), (xs[3] - 3, top + 36)])]

    # Handoff strip: the only cross-person links.
    sy = top + total + 40
    parts.append(text(MARGIN, sy, "What passes between people", "section"))
    bw = (W - 2 * MARGIN - 2 * GAP) / 3
    for i, (src, dst, what) in enumerate(HANDOFFS):
        bx = MARGIN + i * (bw + GAP)
        s, d = LANES[src], LANES[dst]
        name_w = len(s["name"]) * 11
        parts += [rect(bx, sy + 16, bw, 78, "#ffffff", "#94a3b8", 1.5),
                  text(bx + 16, sy + 44, s["name"].title(), "handoff", None, s["text"]),
                  text(bx + 22 + name_w, sy + 44, "→", "handoff", None, INK),
                  text(bx + 48 + name_w, sy + 44, d["name"].title(), "handoff", None, d["text"])]
        for j, line in enumerate(wrap(what, bw - 32)):
            parts.append(text(bx + 16, sy + 68 + j * 18, line, "body"))

    # Footer: the one boundary and the one rule that matter.
    fy = sy + 94 + 30
    parts += [rect(MARGIN, fy, W - 2 * MARGIN, 62, "#edf2f7", "#bcccdc", 1, 12),
              text(MARGIN + 20, fy + 27, "Hands off to the next subteam: costmaps, route planning and motors are theirs, not ours. GPS comes later, after this works.", "body"),
              text(MARGIN + 20, fy + 49, "Rule: exactly one component owns each TF frame link. In particular, only one may publish map → odom.", "body")]
    height = int(fy + 62 + 24)

    body = "\n  ".join(parts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" role="img" aria-labelledby="t d">
  <title id="t">2027 Navigation Data and VSLAM: who does what</title>
  <desc id="d">Three lanes (Hedgie: VSLAM and map research; Wobbles: data synthesis and sensor evidence; Bedrawn: integration and handoff) across four phases: shared preflight, parallel work, integration gate, package conversion, followed by what passes between people.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="{LINE}"/></marker>
    <style>
      text {{ fill: {BODY}; }}
      .title {{ font-size: 27px; font-weight: 700; fill: {INK}; }} .subtitle {{ font-size: 15px; fill: {MUTED}; }}
      .section {{ font-size: 18px; font-weight: 700; fill: {INK}; }}
      .phase {{ font-size: 17px; font-weight: 700; fill: {INK}; }} .phaseSub {{ font-size: 13px; fill: {MUTED}; }}
      .lane {{ font-size: 20px; font-weight: 700; }} .laneRole {{ font-size: 13px; font-weight: 700; fill: {INK}; }}
      .cardTitle {{ font-size: 16px; font-weight: 700; fill: {INK}; }} .body {{ font-size: {FONT}px; }}
      .note {{ font-size: 13px; font-style: italic; fill: {MUTED}; }} .handoff {{ font-size: 16px; font-weight: 700; }}
      .chip {{ font-size: 10.5px; font-weight: 700; fill: #ffffff; letter-spacing: 0.4px; }}
    </style>
  </defs>
  <rect width="{W}" height="{height}" fill="{PAGE}"/>
  {body}
</svg>
'''


if __name__ == "__main__":
    OUTPUT.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
