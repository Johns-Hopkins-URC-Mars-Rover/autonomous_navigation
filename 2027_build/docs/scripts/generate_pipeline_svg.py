#!/usr/bin/env python3
"""Generate the IMU-first workstream diagram at ../pipeline.svg.

Run from the repository root:
    python3 2027_build/docs/scripts/generate_pipeline_svg.py

This uses only the Python standard library so the planning artifact can be
regenerated without installing the ROS workspace or graphical tools.
"""

from pathlib import Path
from xml.sax.saxutils import escape


OUTPUT = Path(__file__).resolve().parents[1] / "pipeline.svg"


def text(x, y, value, class_name, anchor=None):
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x}" y="{y}" class="{class_name}"{anchor_attr}>{escape(value)}</text>'


def rect(x, y, width, height, fill, stroke, stroke_width=2, radius=10):
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def panel(x, y, width, height, color, title, lines, footer=None, stroke_width=2):
    parts = [rect(x, y, width, height, "#ffffff", color, stroke_width)]
    parts.append(text(x + 18, y + 30, title, "boxTitle"))
    for index, line in enumerate(lines):
        parts.append(text(x + 18, y + 58 + index * 23, line, "boxText"))
    if footer:
        # Keep the footer below the final bullet in the densest four-line card.
        parts.append(text(x + 18, y + height - 15, footer, "small"))
    return "\n  ".join(parts)


def lane(y, fill, stroke, label_color, name, description, footer):
    parts = [rect(24, y, 192, 164, fill, stroke, 2, 12)]
    parts.extend(
        [
            text(120, y + 46, name, "lane", "middle").replace('class="lane"', f'class="lane" fill="{label_color}"'),
            text(120, y + 70, description[0], "note", "middle"),
            text(120, y + 89, description[1], "note", "middle"),
            text(120, y + 127, footer, "small", "middle"),
        ]
    )
    return "\n  ".join(parts)


def build_svg():
    phases = [
        (250, 220, "#e6fcf5", "#38a169", "0 · Shared preflight", "clock, frames, one replayable session"),
        (505, 400, "#ebf8ff", "#3182ce", "1 · Parallel individual milestones", "Wobbles starts substantive IMU work"),
        (940, 240, "#fffaf0", "#dd6b20", "2 · Integration gate", "one contract, one replay session"),
        (1215, 245, "#faf5ff", "#805ad5", "3 · Package conversion", "validated vertical slices only"),
    ]
    phase_parts = []
    for x, width, fill, stroke, title, subtitle in phases:
        phase_parts += [rect(x, 112, width, 74, fill, stroke), text(x + width / 2, 141, title, "phase", "middle"), text(x + width / 2, 162, subtitle, "phaseSub", "middle")]

    hedgie = panel(
        505, 220, 400, 164, "#7a5cc0", "Visual-only benchmark (independent)",
        ["• RGB-D fixture/recording → trajectory, loop closures, map", "• quantify against ZED baseline", "• prepare optional visual-inertial comparison input"],
        "Hedgie does not wait for live ROS, IMU, or the costmap team.",
    )
    wobbles = panel(
        505, 423, 400, 164, "#1f8a7e", "IMU integration and validation (Wobbles first)",
        ["• publish/record IMU; validate axes, rate, bias, vibration", "• matched camera-only vs IMU-fused routes", "• decide whether additional filtering is warranted"],
        "Demonstrate benefit; do not assume it.", 3,
    )
    bedrawn = panel(
        505, 626, 400, 164, "#c27a00", "Costmap-ready input bundle (independent)",
        ["• depth/point cloud → LaserScan obstacle input", "• replay, TF/localization context, footprint metadata"],
        "External team builds costmap and chooses routes.",
    )
    preflight = "\n  ".join([
        panel(250, 220, 220, 164, "#38a169", "Minimum evidence only", ["• camera/IMU clock convention", "• base → camera → IMU frames", "• one SVO/bag or replay path", "• minimal session manifest"], "Not a prolonged camera-only phase."),
        panel(250, 423, 220, 164, "#38a169", "Wobbles preflight", ["• timing and physical frames", "• replayable camera/IMU run", "• baseline trajectory retained"], "Enables IMU interpretation."),
        panel(250, 626, 220, 164, "#38a169", "Bedrawn preflight", ["• agree frame/topic names", "• create synthetic source"], "Does not wait for hardware."),
    ])
    integration = "\n  ".join([
        rect(940, 220, 240, 570, "#ffffff", "#dd6b20"),
        text(958, 252, "Prove the handoffs", "boxTitle"),
        *[text(958, 287 + index * 26, item, "boxText") for index, item in enumerate([
            "1. Freeze manifest schema", "2. Verify topic, QoS, TF", "3. Replay one session", "4. Hedgie: visual vs VI", "5. Bedrawn: swap input", "6. One map → odom owner",
        ])],
        '<line x1="958" y1="448" x2="1162" y2="448" stroke="#fbd38d" stroke-width="2"/>',
        text(958, 479, "Gate is passed only if", "boxTitle"),
        *[text(958, 510 + index * 25, item, "boxText") for index, item in enumerate([
            "• frames and time agree", "• playback is repeatable", "• no duplicate TF owner", "• input bundle replays cleanly",
        ])],
        text(958, 623, "GPS follows only after this gate.", "small"),
    ])
    conversion = "\n  ".join([
        rect(1215, 220, 245, 570, "#ffffff", "#805ad5"),
        text(1233, 252, "Convert what is proven", "boxTitle"),
        *[text(1233, 288 + index * 26, item, "boxText") for index, item in enumerate(["• rover_camera_ai", "• rover_localization", "• rover_navigation_inputs", "• rover_bringup"])],
        '<line x1="1233" y1="397" x2="1442" y2="397" stroke="#d6bcfa" stroke-width="2"/>',
        text(1233, 429, "Rules", "boxTitle"),
        *[text(1233, 460 + index * 24, item, "boxText") for index, item in enumerate([
            "• minimal scaffolding may", "  exist earlier", "• no legacy migration just", "  for folder uniformity", "• one demonstrated vertical", "  slice per conversion PR",
        ])],
        text(1233, 623, "Then pass stable inputs downstream.", "small"),
    ])
    connectors = "\n  ".join(
        f'<path d="M{x1} {y} H{x2}" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>'
        for y in (302, 505, 708)
        for x1, x2 in ((470, 495), (905, 930), (1180, 1205))
    )
    lanes = "\n  ".join([
        lane(220, "#f4f0ff", "#7a5cc0", "#5b3c9b", "HEDGIE", ("Offline SLAM +", "semantic maps"), "Starts from files/fixtures"),
        lane(423, "#e6fffa", "#1f8a7e", "#167567", "WOBBLES", ("Sensors, TF,", "recording, localization"), "Data-contract owner"),
        lane(626, "#fff5e6", "#c27a00", "#a65d00", "BEDRAWN", ("Costmap-ready inputs,", "replay handoff"), "External team consumes"),
    ])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 1010" width="1500" height="1010" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
  <title>2027 Autonomous Navigation: IMU-first parallel workstream timeline</title>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#475569"/></marker>
    <style>
      .title {{ font-size: 25px; font-weight: 700; fill: #102a43; }} .subtitle {{ font-size: 14px; fill: #486581; }}
      .phase {{ font-size: 15px; font-weight: 700; fill: #102a43; }} .phaseSub {{ font-size: 11px; fill: #486581; }}
      .lane {{ font-size: 18px; font-weight: 700; }} .boxTitle {{ font-size: 15px; font-weight: 700; fill: #102a43; }}
      .boxText {{ font-size: 12.5px; fill: #243b53; }} .note {{ font-size: 12px; fill: #334e68; }} .small {{ font-size: 11px; fill: #486581; }}
    </style>
  </defs>
  <rect width="1500" height="1010" fill="#f8fafc"/>
  {rect(20, 16, 1460, 72, '#ffffff', '#d9e2ec', 1.5, 12)}
  {text(46, 49, '2027 Autonomous Navigation · IMU-first, parallel delivery', 'title')}
  {text(46, 72, 'Short measurement preflight → Wobbles leads IMU validation while Hedgie and Bedrawn work independently → integrate proven handoffs → convert validated slices to ROS packages.', 'subtitle')}
  {'\n  '.join(phase_parts)}
  <path d="M470 149 H495 M905 149 H930 M1180 149 H1205" stroke="#475569" stroke-width="3" marker-end="url(#arrow)"/>
  {lanes}
  {preflight}
  {hedgie}
  {wobbles}
  {bedrawn}
  {integration}
  {conversion}
  {connectors}
  {rect(250, 835, 1210, 120, '#edf2f7', '#bcccdc', 1, 12)}
  {text(275, 867, 'Shared rule across the whole timeline', 'boxTitle')}
  {text(275, 895, "Hedgie's visual baseline and Bedrawn's costmap-ready input bundle are independent of Wobbles' IMU result. They all need the final sensor, frame, manifest, and map contracts for end-to-end integration.", 'boxText')}
  {text(275, 922, 'Bedrawn hands inputs to the external costmap/planning team; that team selects costmaps and routes. No motors are commanded.', 'boxText')}
</svg>
'''


if __name__ == "__main__":
    OUTPUT.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
