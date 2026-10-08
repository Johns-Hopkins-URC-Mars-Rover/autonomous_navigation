#!/usr/bin/env python3
"""Generate the detailed workstream pipeline diagram at ../pipeline.svg.

Run from the repository root:
    python3 2027_build/docs/scripts/generate_pipeline_svg.py

This uses only the Python standard library so the planning artifact can be
regenerated without installing the ROS workspace or graphical tools.

Layout model (read this before editing):
  * Every box is a "card": a title plus labelled sections (IN, OUT, DOES, ...).
  * Text is wrapped by an estimated character width, and each card's height is
    computed from its wrapped content, so adding a bullet never overflows a box.
  * Rows of the lane grid take the height of their tallest card.
  * Content lives in the data tables below; the drawing code is generic.
"""

import textwrap
from pathlib import Path
from xml.sax.saxutils import escape


OUTPUT = Path(__file__).resolve().parents[1] / "pipeline.svg"

# ---------------------------------------------------------------- palette ---
INK = "#102a43"
BODY = "#243b53"
MUTED = "#486581"
LINE = "#475569"
PAGE = "#f8fafc"
RULE = "#e2e8f0"
PURPLE = "#7a5cc0"
BLUE = "#2b6cb0"

LANE = {
    "hedgie": {"stroke": PURPLE, "fill": "#f4f0ff", "text": "#5b3c9b"},
    "wobbles": {"stroke": "#1f8a7e", "fill": "#e6fffa", "text": "#167567"},
    "bedrawn": {"stroke": "#c27a00", "fill": "#fff5e6", "text": "#a65d00"},
}

PHASE = {
    0: {"stroke": "#38a169", "fill": "#e6fcf5"},
    1: {"stroke": "#3182ce", "fill": "#ebf8ff"},
    2: {"stroke": "#dd6b20", "fill": "#fffaf0"},
    3: {"stroke": "#805ad5", "fill": "#faf5ff"},
    4: {"stroke": "#2c7a7b", "fill": "#e6fffa"},
}

# Section label chips: kind -> (text, colour).
SECTION = {
    "IN": ("IN", BLUE),
    "OUT": ("OUT", "#2f855a"),
    "DOES": ("DOES", "#4a5568"),
    "NEEDS": ("NEEDS", "#c05621"),
    "DONE": ("DONE", "#6b46c1"),
    "NOT": ("NOT", "#c53030"),
    "CODE": ("CODE", "#2c7a7b"),
}

# Inline tags in front of a bullet: key -> (text, colour).
TAG = {
    # where an INPUT comes from
    "live": ("LIVE", "#c53030"),
    "file": ("FILE", "#2f855a"),
    "synth": ("SYNTHETIC", "#718096"),
    "hand": ("HAND", "#92400e"),
    # what a DEPENDENCY is
    "hedgie": ("VSLAM", LANE["hedgie"]["stroke"]),
    "wobbles": ("DATA SYNTHESIS", LANE["wobbles"]["stroke"]),
    "bedrawn": ("INTEGRATION", LANE["bedrawn"]["stroke"]),
    "tool": ("TOOL", "#4a5568"),
    "before": ("EARLIER", "#38a169"),
    "gate": ("GATE", "#dd6b20"),
    "ext": ("NEXT TEAM", BLUE),
}

# ------------------------------------------------------- text/geometry kit ---
FONT = 13
LINE_H = 17.5
CHAR_W = 0.53  # average glyph width as a fraction of font size (conservative)
PAD = 16
LABEL_W = 58  # width reserved for the IN/OUT/DOES chip column


def wrap(value, width_px, size=FONT):
    chars = max(12, int(width_px / (size * CHAR_W)))
    return textwrap.wrap(value, chars, break_long_words=False) or [""]


def text(x, y, value, cls, anchor=None, fill=None):
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    fill_attr = f' style="fill:{fill}"' if fill else ""  # style beats the stylesheet's text rule
    return f'<text x="{x:g}" y="{y:g}" class="{cls}"{anchor_attr}{fill_attr}>{escape(value)}</text>'


def rect(x, y, w, h, fill, stroke, stroke_width=2, radius=10, dash=None):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr}/>'
    )


def chip(x, y, label, color, width, cls="chip", height=16):
    return [
        rect(x, y, width, height, color, color, 0, 4),
        text(x + width / 2, y + height - 4.5, label, cls, "middle"),
    ]


def path(points, color=LINE, width=2, dashed=False, marker="arrow"):
    d = "M" + " L".join(f"{px:g} {py:g}" for px, py in points)
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    end = f' marker-end="url(#{marker})"' if marker else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{end}/>'


def label_box(cx, cy, lines, width, color=RULE, title=None, fill="#ffffff"):
    """A small white callout, centred on (cx, cy), used to label arrows."""
    rows = ([("title", title)] if title else []) + [("small", line) for line in lines]
    height = 14 + 16 * len(rows)
    x, y = cx - width / 2, cy - height / 2
    parts = [rect(x, y, width, height, fill, color, 1.5, 8)]
    for i, (cls, value) in enumerate(rows):
        parts.append(text(x + 10, y + 19 + i * 16, value, "smallBold" if cls == "title" else "small"))
    return "\n  ".join(parts)


# --------------------------------------------------------------- the card ---
def layout_card(spec, width):
    """Wrap a card's content. Returns (ops, height); render_card() draws them."""
    ops = []
    y = PAD + 4
    ops.append(("title", y, spec["title"]))
    if spec.get("subtitle"):
        for line in wrap(spec["subtitle"], width - 2 * PAD, 12):
            y += 16
            ops.append(("subtitle", y, line))
    for kind, items in spec.get("sections", []):
        y += 11
        ops.append(("rule", y - 5))
        tag_w = max((len(TAG[i[0]][0]) * 7.0 + 14 for i in items if isinstance(i, tuple)), default=0)
        indent = LABEL_W + (tag_w + 6 if tag_w else 12)
        ops.append(("chip", y + LINE_H - 12, kind))
        for item in items:
            tag, value = item if isinstance(item, tuple) else (None, item)
            for i, line in enumerate(wrap(value, width - 2 * PAD - indent)):
                y += LINE_H
                ops.append(("line", y, line, tag if i == 0 else None, i == 0 and not tag, tag_w, indent))
            y += 3
    return ops, y + PAD - 4


def render_card(ops, x, y, w, h, stroke, stroke_width=2, badge=None, fill="#ffffff"):
    parts = [rect(x, y, w, h, fill, stroke, stroke_width)]
    for op in ops:
        kind = op[0]
        if kind == "title":
            parts.append(text(x + PAD, y + op[1], op[2], "cardTitle"))
        elif kind == "subtitle":
            parts.append(text(x + PAD, y + op[1], op[2], "cardSub"))
        elif kind == "rule":
            parts.append(f'<line x1="{x + PAD:g}" y1="{y + op[1]:g}" x2="{x + w - PAD:g}" y2="{y + op[1]:g}" stroke="{RULE}" stroke-width="1"/>')
        elif kind == "chip":
            label, color = SECTION[op[2]]
            parts += chip(x + PAD, y + op[1], label, color, 50)
        elif kind == "line":
            _, ly, line, item_tag, bullet, tag_w, indent = op
            tx = x + PAD + indent
            if item_tag:
                label, color = TAG[item_tag]
                parts += chip(x + PAD + LABEL_W, y + ly - 11, label, color, tag_w, "tag", 14)
            elif bullet:
                parts.append(text(tx - 10, y + ly, "•", "body"))
            parts.append(text(tx, y + ly, line, "body"))
    if badge:
        label, color = badge
        bw = len(label) * 6.4 + 16
        parts += chip(x + w - PAD - bw, y + 11, label, color, bw, "tag", 15)
    return "\n  ".join(parts)


class Card:
    def __init__(self, spec, width, stroke, badge=None, stroke_width=2):
        self.width, self.stroke, self.badge, self.stroke_width = width, stroke, badge, stroke_width
        self.ops, self.height = layout_card(spec, width)

    def draw(self, x, y, height=None):
        return render_card(self.ops, x, y, self.width, height or self.height, self.stroke,
                           self.stroke_width, self.badge)


# ================================================================ CONTENT ===
BASELINE = {
    "title": "Starting point: the standalone ZED prototype (main.py, slam/, object_detection.py)",
    "subtitle": "Stays runnable as the replayable baseline. The ROS 2 workspace grows beside it; nothing is rewritten for folder neatness.",
    "sections": [
        ("IN", [("live", "ZED stereo camera with IMU (RGB, depth, inertial data)"),
                ("file", "Optional SVO replay instead of the live camera"),
                ("file", "models/best.pt YOLO weights")]),
        ("OUT", ["SVO recording, TUM trajectory text file, persisted ZED area map, YOLO overlays, depth-heuristic flags (walls, hallways, central obstacles, clusters)"]),
        ("DOES", ["ZED positional tracking with IMU fusion, depth retrieval, YOLO detection plus depth heuristics, plots of trajectory and displacement"]),
        ("NOT", ["No ROS 2 messages, no Nav2 map or costmap, no GPS, no motor commands. A ZED area map is not an OccupancyGrid.",
                 "A replay, plot or YOLO box proves a component ran, not that navigation is safe."]),
    ],
}

LEGEND = {
    "title": "How to read this diagram",
    "sections": [
        ("IN", ["Where the work starts. The coloured chip says where the input comes from: LIVE = real hardware, FILE = recorded files or replay, SYNTHETIC = generated fixture, HAND = measured by hand."]),
        ("OUT", ["What the box produces and hands onward: files, ROS topics, reports, contracts."]),
        ("DOES", ["The main functionality, in the order it is built."]),
        ("NEEDS", ["Dependencies. The chip names the source responsibility: DATA SYNTHESIS, VSLAM or INTEGRATION; TOOL = software or docs; EARLIER = previous phase; GATE = bundle gate; NEXT TEAM = the downstream subteam."]),
        ("DONE", ["Acceptance check: the claim may be made only when this is shown."]),
        ("NOT", ["Deliberately out of scope for the box, to stop scope creep."]),
        ("CODE", ["Where the code lives and what it may touch."]),
    ],
}

# ---- Phase 0: shared preflight (one card per lane) ---------------------------
PREFLIGHT = {
    "hedgie": {
        "title": "Fixture and session layout",
        "sections": [
            ("IN", [("file", "One recorded ZED session (SVO) or extracted RGB-D folder from Wobbles, once it exists"),
                    ("synth", "Public RGB-D dataset or synthetic sequence, labelled as a fixture, until then")]),
            ("OUT", ["Small checked-in example manifest.json",
                     "Loader skeleton for session/: manifest.json, recording.svo or rgb/ + depth/, intrinsics.yaml, zed_baseline.tum, tracking_status.csv, optional imu.csv and gps.csv",
                     "Confirmed TUM timestamp units and quaternion order"]),
            ("DOES", ["Fixes the folder contract so analysis runs from files, not a live camera"]),
            ("NEEDS", [("tool", "ZED SVO docs, evo TUM-format docs"),
                       ("wobbles", "Real manifest and recording later; a hand-authored manifest works until then")]),
            ("NOT", ["Wait for live ROS, an IMU result or the costmap work"]),
        ],
    },
    "wobbles": {
        "title": "Measurement preflight",
        "subtitle": "Small and required. Not a camera-only feature phase.",
        "sections": [
            ("IN", [("live", "ZED camera stream and IMU on the rover"),
                    ("file", "Or an existing SVO"),
                    ("hand", "Measured base_link to camera_link to imu_link mounting geometry")]),
            ("OUT", ["Documented clock and timestamp convention, frame ids",
                     "Static frame geometry for base_link, camera_link, imu_link",
                     "One replayable recording: SVO plus rosbag2",
                     "Minimal session manifest; camera-only baseline trajectory kept for later comparison"]),
            ("DOES", ["Supplies the evidence needed to interpret IMU data: when did it happen, in which frame, and can it be replayed"]),
            ("NEEDS", [("tool", "Ubuntu 24.04, ROS 2 Jazzy, ZED SDK, NVIDIA driver and CUDA, ZED ROS 2 wrapper: verified together"),
                       ("tool", "main.py baseline for the camera-only trajectory")]),
            ("DONE", ["Recording replays the relevant topic set without hardware"]),
        ],
    },
    "bedrawn": {
        "title": "Names and synthetic source",
        "sections": [
            ("IN", [("synth", "Generated ranges and points for a fake obstacle scene"),
                    ("hand", "Start measuring rover footprint and sensor offsets")]),
            ("OUT", ["Draft list of frame and topic names",
                     "Synthetic LaserScan or PointCloud2 publisher that needs no hardware"]),
            ("DOES", ["Agrees names with Wobbles so later swaps are painless",
                      "Gives integration something to test against from day one"]),
            ("NEEDS", [("tool", "sensor_msgs definitions"),
                       ("wobbles", "Draft frame names; placeholders are fine until the contract freezes")]),
            ("NOT", ["Wait for hardware or for the IMU result"]),
        ],
    },
}

# ---- Phase 1: parallel subteam responsibilities ------------------------------
PARALLEL = {
    "hedgie": {
        "title": "Visual-only SLAM and semantic-map benchmark",
        "subtitle": "Branch hedgie-slam-research. Question: can recorded RGB-D beat the raw ZED trajectory and map?",
        "sections": [
            ("IN", [("file", "Session folder: manifest.json, SVO or rgb/ + depth/, intrinsics.yaml, zed_baseline.tum, tracking_status.csv"),
                    ("file", "Detector utilities factored out of object_detection.py, with tests proving behaviour is unchanged")]),
            ("OUT", ["outputs/<session_id>/<experiment_id>/: trajectory.tum, trajectory_quality.json, loop_closures.json, pose_graph.g2o, dense_map.ply, bev_occupancy.*, metrics.json, report.md",
                     "Every output records input session id, calibration id, code revision, model or checkpoint id and parameters",
                     "Route metrics: tracked-frame fraction, discontinuities, repeatability, relocalization events, runtime, map coverage",
                     "Optional later export of PointCloud2 or OccupancyGrid for the handoff bundle"]),
            ("DOES", ["1. Validate manifest; report on the ZED baseline trajectory",
                      "2. Select RGB-D frames; back-project depth to 3D with the camera intrinsics",
                      "3. ORB feature matching with geometric verification; learned features (SuperPoint, LightGlue) only if hardware allows",
                      "4. Place-recognition loop-closure candidates, geometric verification, pose-graph optimization",
                      "5. Dense colored point cloud or surfel map from optimized poses",
                      "6. Reuse YOLO detections or masks to drop dynamic objects from landmarks; build BEV grid with free, occupied, unknown and confidence"]),
            ("NEEDS", [("tool", "OpenCV (geometry), evo (trajectory metrics), Open3D (optional viewing)"),
                       ("tool", "Camera intrinsics checked against resolution; never copied constants"),
                       ("wobbles", "A real session folder; until then a labelled fixture"),
                       ("wobbles", "IMU-qualified session, only for the later visual vs visual-inertial comparison")]),
            ("DONE", ["Same session and config reproduce the same result, or nondeterminism is documented",
                      "Every loop closure keeps its visual and geometric evidence",
                      "Judged against the ZED baseline with numbers, not screenshots",
                      "Dynamic masking reports its false-removal cases; outputs work without ROS 2"]),
            ("CODE", ["2027_build/src/rover_camera_ai/: session_io, slam, mapping, evaluation, tests. main.py is not changed to run research live."]),
            ("NOT", ["Live camera setup, ROS 2 plumbing, TF debugging or GPS hardware"]),
        ],
        "badge": ("INDEPENDENT", PURPLE),
    },
    "wobbles": {
        "title": "IMU integration and validation (first substantive milestone)",
        "subtitle": "Branch wobbles-sensor-localization. Question: can we trust, replay and correctly frame the camera and IMU data?",
        "sections": [
            ("IN", [("live", "ZED camera IMU stream; stationary runs and moving runs on the same route"),
                    ("file", "Or an SVO replay of those runs"),
                    ("hand", "Measured mount geometry, used for the rover URDF/xacro")]),
            ("OUT", ["Published and recorded IMU topic with its frame and timing documented",
                     "Characterization: stationary bias and noise, vibration, axis orientation, data rate",
                     "Matched camera-only vs IMU-fused trajectory comparison on the same route",
                     "Sensor-health report from /diagnostics plus tracking-status summaries",
                     "Complete session manifest; TF diagram and view_frames artifact",
                     "Launch and config files: live ZED, SVO replay, IMU and GPS logging, RViz validation"]),
            ("DOES", ["1. Publish and record the ZED IMU; document frame and timing",
                      "2. Characterize noise, bias, vibration and axes",
                      "3. Compare camera-only against IMU-fused tracking on matched runs",
                      "4. Add a robot_localization filter only after documenting real extra sensors (wheel odometry, external IMU)",
                      "5. Draft the session manifest and sensor-topic/TF contract that Hedgie and Bedrawn will consume"]),
            ("NEEDS", [("before", "Measurement preflight complete before any IMU result is interpreted"),
                       ("tool", "ZED ROS 2 wrapper with parameter overlays; upstream wrapper files are never edited"),
                       ("tool", "rosbag2 for ROS-message evidence beside the SVO"),
                       ("tool", "Rover URDF/xacro defining base, camera and IMU frames (GPS frame later)")]),
            ("DONE", ["No TF edge has more than one publisher",
                      "Every sensor message has the expected frame and a monotonic timestamp",
                      "SVO or bag replay reproduces the topic set without hardware",
                      "IMU benefit is shown on matched runs, never assumed"]),
            ("CODE", ["2027_build/src/rover_localization/ and rover_bringup/. main.py may gain narrow exports only: timestamped IMU CSV, tracking status and confidence, calibration JSON, tracking-gap records."]),
            ("NOT", ["A prolonged camera-only phase; GPS in this phase"]),
        ],
        "badge": ("FIRST SUBSTANTIVE", "#1f8a7e"),
        "stroke_width": 3,
    },
    "bedrawn": {
        "title": "Handoff bundle fixture: costmap-ready navigation inputs",
        "subtitle": "Branch bedrawn-nav-integration. Question: can the next subteam consume our obstacle and localization inputs without rediscovering frames, timing or limits?",
        "sections": [
            ("IN", [("synth", "Synthetic LaserScan or PointCloud2; swapped for Wobbles topics at the gate"),
                    ("hand", "Measured rover footprint dimensions and sensor mounting offsets"),
                    ("file", "Optional Hedgie OccupancyGrid map export, as map context")]),
            ("OUT", ["Replayable LaserScan and/or PointCloud2 obstacle source, plus optional OccupancyGrid context",
                     "Handoff contract per message: type, topic, frame id, timestamp convention, rate, QoS, range and confidence limits, marking and clearing semantics",
                     "Transform ownership map -> odom -> base_link -> sensor and a local pose validity contract",
                     "Footprint, sensor offsets and stated safety assumptions",
                     "Manifest, replay command, small fixture or bag, known failure cases: invalid depth, tracking loss, relocalization"]),
            ("DOES", ["1. Depth to LaserScan adapter, or a constrained depth slice, with synthetic-message tests",
                      "2. Define what an observation may mark or clear, and how invalid data behaves",
                      "3. Validation and replay harness for the bundle",
                      "4. At the gate: swap in Wobbles topics without changing the downstream contract"]),
            ("NEEDS", [("tool", "sensor_msgs LaserScan and PointCloud2 specs, rosbag2"),
                       ("wobbles", "Sensor-topic and TF contract (the bundle's real inputs)"),
                       ("hedgie", "Offline map export, optional"),
                       ("tool", "ZED depth-sensing docs: frame, range and confidence behavior")]),
            ("DONE", ["Replay delivers the documented messages and TF chain without hardware",
                      "Each message has a source frame, monotonic timestamp and documented range and confidence behavior",
                      "Footprint is measured; no point-robot guess",
                      "A consumer can use the bundle without reading the legacy prototype"]),
            ("CODE", ["2027_build/src/rover_navigation_inputs/ and handoff config in 2027_build/config/. ZED acquisition in main.py is not modified."]),
            ("NOT", ["Costmaps, slam_toolbox, planners, controllers, behavior trees or motor commands. The next subteam owns those."]),
        ],
        "badge": ("INDEPENDENT", "#c27a00"),
    },
}

# ---- Phase 4: GPS (one card per lane) ----------------------------------------
GPS = {
    "hedgie": {
        "title": "GPS as a sparse global constraint",
        "sections": [
            ("IN", [("file", "gps.csv from a session"), ("file", "Cross-session recordings of the same place")]),
            ("OUT", ["Pose graph with GPS constraints; cross-session relocalization results"]),
            ("DOES", ["Treats GPS as a slow global anchor in the offline pose graph, never as high-rate local motion"]),
            ("NEEDS", [("wobbles", "GPS stream with covariance and fix quality"),
                       ("before", "A stable local pipeline and its replay evidence")]),
        ],
    },
    "wobbles": {
        "title": "GPS integration and global localization",
        "sections": [
            ("IN", [("live", "GPS driver output: NavSatFix"), ("hand", "Measured antenna frame offset")]),
            ("OUT", ["Recorded NavSatFix with covariance, timestamp, fix quality",
                     "Absolute-heading plan",
                     "Comparison: ZED GNSS fusion vs robot_localization + navsat_transform",
                     "One chosen owner of global localization"]),
            ("DOES", ["Validates outdoor repeat routes, global-frame jumps and recovery after poor GNSS visibility"]),
            ("NEEDS", [("gate", "Passed integration gate and agreed map -> odom owner"),
                       ("tool", "ZED Geo Tracking docs, Nav2 GPS tutorial")]),
            ("DONE", ["Not called navigation-ready without covariance, fix quality and heading evidence"]),
        ],
    },
    "bedrawn": {
        "title": "Global-localization pass-through",
        "sections": [
            ("IN", [("wobbles", "The single approved global-localization source")]),
            ("OUT", ["Bundle update documenting global-frame jumps and localization validity"]),
            ("DOES", ["Passes the approved source through only after its quality and heading contract is accepted"]),
            ("NOT", ["Configure the next subteam's costmap or waypoint behavior"]),
        ],
    },
}

INTEGRATION = {
    "title": "Prove the handoffs",
    "subtitle": "Data synthesis, VSLAM and integration converge on one replayable Navigation Data & VSLAM Handoff Bundle.",
    "sections": [
        ("IN", [("wobbles", "IMU-qualified replayable session, manifest draft, sensor-topic and TF contract"),
                ("hedgie", "Visual-only benchmark outputs and the optional map export"),
                ("bedrawn", "Synthetic-source bundle, handoff contract draft, footprint")]),
        ("DOES", ["1. Wobbles: freeze the manifest schema",
                  "2. Integration: verify topic names, message types, QoS and TF against a live or replayed run",
                  "3. Replay one complete bundle through every consumer",
                  "4. VSLAM: compare visual-only against visual-inertial trajectories (fast motion, texture-poor areas, turns)",
                  "5. Integration: swap synthetic sources for measured topics; the downstream contract must not change",
                  "6. Choose exactly one owner for map -> odom"]),
        ("OUT", ["Frozen session manifest schema",
                 "Verified topic, QoS and TF contract",
                 "One session replayed end to end",
                 "Visual vs visual-inertial comparison",
                 "Handoff bundle running on real topics",
                 "Documented single map -> odom owner"]),
        ("DONE", ["Frames and time agree across sensors",
                  "Playback is repeatable",
                  "No duplicate TF owner",
                  "The input bundle replays cleanly",
                  "The next subteam can consume it with no extra explanation"]),
        ("NEEDS", [("before", "Data-synthesis IMU evidence, VSLAM benchmark and integration fixture all finished"),
                   ("ext", "Next subteam to confirm the handoff reads correctly")]),
        ("NOT", ["GPS. It follows only after this gate."]),
    ],
}

CONVERSION = {
    "title": "Convert only what is proven",
    "subtitle": "Move demonstrated vertical slices into final ROS 2 packages.",
    "sections": [
        ("IN", [("gate", "A slice that passed the integration gate, with its acceptance check"),
                ("before", "Parallel-phase code on the person's branch")]),
        ("OUT", ["rover_camera_ai (Hedgie: offline SLAM, mapping, evaluation)",
                 "rover_localization and rover_bringup (Wobbles: sensors, TF, launch, logging)",
                 "rover_navigation_inputs (Bedrawn: adapters, validation, handoff)",
                 "Stable inputs passed downstream to the next subteam"]),
        ("DOES", ["One demonstrated vertical slice per conversion pull request",
                  "One new package or config concern per pull request",
                  "Small common 2027_build skeleton changes are reviewed from main, then rebased by the three branches"]),
        ("NEEDS", [("gate", "Integration gate passed"),
                   ("tool", "colcon workspace under 2027_build/, valid ROS 2 package names")]),
        ("DONE", ["Each merge carries a documented acceptance check",
                  "Legacy prototype still runs"]),
        ("NOT", ["Migrate legacy code just for folder uniformity",
                 "Merge empty package skeletons to claim progress",
                 "Commit build/, install/, log/, SVOs, bags, maps or models (Git LFS or an artifact store only if approved)"]),
    ],
}

# ---- Handoff contracts table -------------------------------------------------
CONTRACTS = [
    ("Session manifest", "Data synthesis → VSLAM, integration",
     "Camera model, serial or anonymized id, resolution, FPS, intrinsics; coordinate convention and base_link → camera_link transform; SVO and rosbag2 paths and checksums; start and end timestamps, software versions, calibration version; tracking, IMU and GPS availability; route, environment, known failures",
     "Draft in preflight; frozen at gate step 1"),
    ("Sensor topics and TF", "Data synthesis → Integration, next subteam",
     "Standard message type, topic name, frame id, rate, QoS; one publisher per TF edge",
     "Draft in parallel phase; verified at gate step 2"),
    ("Offline map export", "VSLAM → Integration, next subteam (optional)",
     "Frame, resolution, occupancy and confidence, provenance",
     "Only when Hedgie has a map worth exporting"),
    ("Navigation Data & VSLAM Handoff Bundle", "Integration → next subteam",
     "Obstacle source, TF and localization context, measured footprint, replay evidence, known failure cases",
     "Synthetic first; real topics at gate step 5"),
]

TF_CHAIN = [
    ("map", "Globally corrected frame",
     "Exactly ONE owner, chosen at the integration gate. Candidates: ZED tracking, SLAM Toolbox, AMCL, a GPS filter. Never two."),
    ("odom", "Smooth short-term motion",
     "Local odometry: ZED camera+IMU tracking, or an external filter only if real extra sensors exist. Wobbles documents the owner."),
    ("base_link", "The rover body",
     "Anchor frame. Footprint is measured relative to it by Bedrawn."),
    ("camera_link", "Camera mount",
     "Static transform from the rover URDF/xacro (Wobbles), from measured geometry."),
    ("imu_link", "IMU mount",
     "Static transform from the same URDF/xacro. GPS antenna frame is added at the GPS stage."),
]

RULES = [
    ("Scope and safety", [
        "No motors are commanded and no live motor command is an acceptance criterion; prove everything through RViz, replay or simulation first.",
        "This subteam hands inputs and evidence to the next subteam; that team builds costmaps and picks routes.",
        "GPS is last: a slow, noisy global correction, not a replacement for local camera motion.",
    ]),
    ("Dependency asymmetry", [
        "VSLAM and integration can start without the IMU result.",
        "All responsibilities need the final data-synthesis sensor, frame and manifest contracts for end-to-end validation.",
        "The visual baseline and integration fixture are independent of the IMU result.",
    ]),
    ("Evidence and hygiene", [
        "Every claim keeps its inputs, parameters, outputs and acceptance check so it can be reproduced.",
        "Do not edit another person's package without agreement. Use standard ROS 2 message types at package boundaries.",
        "Generated SVO, rosbag2, maps, models and experiment outputs stay out of Git unless explicitly managed.",
    ]),
]


# ============================================================== ASSEMBLY ===
W = 2480
MARGIN = 24
LANE_W = 176
GAP = 26
COLS = {0: 340, 1: 680, 2: 400, 3: 340, 4: 360}

PHASE_HEAD = {
    0: ("0 · Shared preflight", "Small, required: clock, frames, one replayable session"),
    1: ("1 · Parallel subteam work", "Data synthesis, VSLAM, integration fixture"),
    2: ("2 · Assemble + validate bundle", "One contract, one replayable delivery, one map owner"),
    3: ("3 · Package conversion", "Validated vertical slices only"),
    4: ("4 · GPS (later)", "Only after the local stack and replay evidence are stable"),
}

LANE_INFO = {
    "hedgie": ("VSLAM", "VSLAM and map research",
               "Asks: what can recorded RGB-D data teach us to make the trajectory and map better?",
               "Initial branch: hedgie-slam-research. Starts from files or fixtures."),
    "wobbles": ("DATA SYNTHESIS", "Data synthesis and sensor evidence",
                "Asks: can we trust, replay and correctly frame the camera, IMU and GPS data?",
                "Initial branch: wobbles-sensor-localization. Data-contract owner."),
    "bedrawn": ("INTEGRATION", "Integration and next-subteam handoff",
                "Asks: can the next subteam consume our validated bundle without rediscovering data limits?",
                "Initial branch: bedrawn-nav-integration. Synthetic source first."),
}


def column_x():
    xs, x = {}, MARGIN + LANE_W + GAP
    for phase in range(5):
        xs[phase] = x
        x += COLS[phase] + GAP
    return xs


def build_svg():
    parts = []
    xs = column_x()
    lanes = ["hedgie", "wobbles", "bedrawn"]

    # ---- header ----------------------------------------------------------
    parts += [
        rect(MARGIN, 16, W - 2 * MARGIN, 82, "#ffffff", "#d9e2ec", 1.5, 12),
        text(MARGIN + 26, 53, "2027 Autonomous Navigation · data synthesis, VSLAM, and integration · detailed pipeline", "title"),
        text(MARGIN + 26, 80, "Short measurement preflight → data synthesis and VSLAM proceed in parallel → assemble one validated handoff bundle → package proven producers → GPS later.", "subtitle"),
    ]

    # ---- baseline + legend ----------------------------------------------
    base_w = 1180
    base = Card(BASELINE, base_w, "#64748b")
    legend = Card(LEGEND, W - 2 * MARGIN - base_w - GAP, "#64748b")
    top_h = max(base.height, legend.height)
    top_y = 118
    parts += [base.draw(MARGIN, top_y, top_h), legend.draw(MARGIN + base_w + GAP, top_y, top_h)]

    # ---- phase header chips ---------------------------------------------
    head_y = top_y + top_h + 44
    parts.append(path([(MARGIN + base_w / 2, top_y + top_h), (MARGIN + base_w / 2, head_y - 6)]))
    parts.append(text(MARGIN + base_w / 2 + 14, top_y + top_h + 28, "feeds the preflight and every later phase as the reference baseline", "small"))
    for phase in range(5):
        title, sub = PHASE_HEAD[phase]
        x, w = xs[phase], COLS[phase]
        parts += [
            rect(x, head_y, w, 66, PHASE[phase]["fill"], PHASE[phase]["stroke"]),
            text(x + w / 2, head_y + 27, title, "phase", "middle"),
            text(x + w / 2, head_y + 49, sub, "phaseSub", "middle"),
        ]
        if phase < 4:
            parts.append(path([(x + w + 3, head_y + 33), (x + w + GAP - 3, head_y + 33)], width=3))

    # ---- build cards -----------------------------------------------------
    def make(spec, width, lane):
        return Card(spec, width, LANE[lane]["stroke"], spec.get("badge"), spec.get("stroke_width", 2))

    grid = {
        lane: {0: make(PREFLIGHT[lane], COLS[0], lane), 1: make(PARALLEL[lane], COLS[1], lane),
               4: make(GPS[lane], COLS[4], lane)}
        for lane in lanes
    }
    integration = Card(INTEGRATION, COLS[2], PHASE[2]["stroke"])
    conversion = Card(CONVERSION, COLS[3], PHASE[3]["stroke"])

    row_h = {lane: max(max(c.height for c in grid[lane].values()), 230) for lane in lanes}
    tall_need = max(integration.height, conversion.height)
    total = sum(row_h.values()) + 2 * GAP
    if tall_need > total:
        for lane in lanes:
            row_h[lane] += (tall_need - total) / 3
        total = tall_need

    y = head_y + 66 + GAP
    lanes_top = y
    for lane in lanes:
        h = row_h[lane]
        name, role, asks, blocked = LANE_INFO[lane]
        c = LANE[lane]
        parts.append(rect(MARGIN, y, LANE_W, h, c["fill"], c["stroke"], 2, 12))
        parts.append(text(MARGIN + LANE_W / 2, y + 36, name, "lane", "middle", c["text"]))
        ly = y + 62
        for block, cls in ((role, "laneRole"), (asks, "note"), (blocked, "noteBold")):
            for line in wrap(block, LANE_W - 28, 12):
                parts.append(text(MARGIN + LANE_W / 2, ly, line, cls, "middle"))
                ly += 16
            ly += 10
        for phase in (0, 1, 4):
            parts.append(grid[lane][phase].draw(xs[phase], y, h))
        ay = y + 40
        parts.append(path([(xs[0] + COLS[0] + 2, ay), (xs[1] - 3, ay)]))
        parts.append(path([(xs[1] + COLS[1] + 2, ay), (xs[2] - 3, ay)]))
        parts.append(path([(xs[3] + COLS[3] + 2, ay), (xs[4] - 3, ay)], dashed=True))
        y += h + GAP

    parts.append(integration.draw(xs[2], lanes_top, total))
    parts.append(conversion.draw(xs[3], lanes_top, total))
    parts.append(path([(xs[2] + COLS[2] + 2, lanes_top + 40), (xs[3] - 3, lanes_top + 40)]))
    lanes_bottom = lanes_top + total

    # ---- handoff diagram (left) + contracts table (right) -----------------
    sec_y = lanes_bottom + 48
    parts.append(text(MARGIN, sec_y, "How responsibilities assemble the handoff bundle", "section"))
    parts.append(text(MARGIN, sec_y + 20, "Solid arrows are required handoffs; dashed purple is optional. Everyone is unblocked from day one by files, fixtures or synthetic messages.", "small"))
    dy = sec_y + 44
    dh = 560
    dw = 1190
    parts.append(rect(MARGIN, dy, dw, dh, "#ffffff", "#d9e2ec", 1.5, 12))

    def node(x, y0, w, h, lane, lines):
        c = LANE[lane]
        out = [rect(x, y0, w, h, c["fill"], c["stroke"], 2.5, 12),
               text(x + w / 2, y0 + 28, lines[0], "lane", "middle", c["text"])]
        for i, line in enumerate(lines[1:]):
            out.append(text(x + w / 2, y0 + 50 + i * 16, line, "note", "middle"))
        return "\n  ".join(out)

    hx, hy, nw, nh = 560, dy + 30, 260, 92
    wx, wy = 70, dy + 230
    bx, by = 560, dy + 430
    ex, ey, ew = 930, dy + 430, 240
    parts.append(node(hx, hy, nw, nh, "hedgie", ["VSLAM", "trajectories, maps, BEV grid", "reads files or fixtures"]))
    parts.append(node(wx, wy, nw, nh, "wobbles", ["DATA SYNTHESIS", "sensor and session evidence", "owns the data contract"]))
    parts.append(node(bx, by, nw, nh, "bedrawn", ["INTEGRATION", "assembles the handoff bundle", "owns handoff evidence"]))
    parts += [
        rect(ex, ey, ew, nh, "#ebf8ff", BLUE, 2.5, 12),
        text(ex + ew / 2, ey + 28, "NEXT SUBTEAM", "lane", "middle", BLUE),
        text(ex + ew / 2, ey + 50, "costmaps, planning, motors", "note", "middle"),
        text(ex + ew / 2, ey + 66, "outside this subteam's scope", "note", "middle"),
    ]
    parts.append(path([(wx + nw, wy + 30), (hx - 3, hy + 46)], color="#2f855a", width=2.5))
    parts.append(label_box(375, hy + 40, ["manifest.json, SVO or rgb/ + depth/", "intrinsics.yaml, zed_baseline.tum", "tracking_status.csv, imu.csv"],
                           258, "#2f855a", "Session folder (FILE)"))
    parts.append(path([(wx + nw, wy + 62), (bx - 3, by + 46)], color="#2f855a", width=2.5))
    parts.append(label_box(375, by + 5, ["standard messages, frame ids, rate, QoS", "TF chain, rosbag2 replay"],
                           258, "#2f855a", "Topics, TF and bag"))
    parts.append(path([(hx + nw / 2, hy + nh), (bx + nw / 2, by - 3)], color=PURPLE, width=2.5, dashed=True, marker="arrowPurple"))
    parts.append(label_box(hx + nw / 2, (hy + nh + by) / 2, ["frame, resolution,", "occupancy and confidence,", "provenance"],
                           190, PURPLE, "Optional map export"))
    parts.append(path([(hx + nw, hy + nh / 2), (ex + ew / 2, hy + nh / 2), (ex + ew / 2, ey - 3)], color=PURPLE, width=2.5, dashed=True, marker="arrowPurple"))
    parts.append(label_box(ex + ew / 2, hy + nh / 2 + 70, ["same export, offered", "directly as map context"], 200, PURPLE))
    parts.append(path([(bx + nw, by + nh / 2), (ex - 3, ey + nh / 2)], color=BLUE, width=3))
    parts.append(label_box((bx + nw + ex) / 2, by - 42, ["input bundle + footprint", "+ replay evidence"],
                           190, BLUE, "Handoff bundle"))
    parts.append(text(ex + ew / 2, ey + nh + 26, "Confirms the bundle reads correctly at the gate", "small", "middle"))
    parts.append(text(wx + nw / 2, wy + nh + 26, "Topics and TF also reach the next subteam directly", "small", "middle"))

    # Contracts table
    tx = MARGIN + dw + GAP
    tw = W - MARGIN - tx
    parts.append(text(tx, sec_y, "Interface contracts to stabilize first", "section"))
    parts.append(text(tx, sec_y + 20, "Each handoff is a contract: who produces it, who consumes it, what fields it must carry, and when it is frozen.", "small"))
    cols = [("Contract", 150), ("Producer → consumer", 190), ("Minimum fields", tw - 150 - 190 - 190 - 2 * 16), ("Stable when", 190)]
    hdr_h = 30
    parts.append(rect(tx, dy, tw, hdr_h, "#edf2f7", "#bcccdc", 1, 8))
    cx = tx + 12
    col_x = []
    for name, cw in cols:
        col_x.append((cx, cw))
        parts.append(text(cx, dy + 20, name, "smallBold"))
        cx += cw + 16
    ry = dy + hdr_h + 6
    for row in CONTRACTS:
        wrapped = [wrap(cell, cw - 22, 12.5) for cell, (_, cw) in zip(row, col_x)]
        rh = max(len(w) for w in wrapped) * 16 + 20
        parts.append(rect(tx, ry, tw, rh, "#ffffff", "#d9e2ec", 1, 8))
        for i, (lines, (cxx, _)) in enumerate(zip(wrapped, col_x)):
            for j, line in enumerate(lines):
                parts.append(text(cxx, ry + 22 + j * 16, line, "smallBold" if i == 0 else "tableText"))
        ry += rh + 6

    # ---- TF ownership strip ----------------------------------------------
    tf_y = dy + dh + 48
    parts.append(text(MARGIN, tf_y, "The one TF picture everyone must respect: map → odom → base_link → camera_link → imu_link", "section"))
    parts.append(text(MARGIN, tf_y + 20, "Only one component may publish each arrow. Two publishers for map → odom make the rover appear to jump and break navigation.", "small"))
    bw = (W - 2 * MARGIN - 4 * 60) / 5
    by0 = tf_y + 44
    bh = 74 + max(len(wrap(t[2], bw - 28, 12.5)) * 16 for t in TF_CHAIN)
    for i, (frame, meaning, owner) in enumerate(TF_CHAIN):
        x = MARGIN + i * (bw + 60)
        hot = frame == "map"
        parts += [
            rect(x, by0, bw, bh, "#fff5f5" if hot else "#ffffff", "#c53030" if hot else "#64748b", 2.5 if hot else 2, 12),
            text(x + 16, by0 + 28, frame, "frame"),
            text(x + 16, by0 + 48, meaning, "note"),
        ]
        for j, line in enumerate(wrap(owner, bw - 28, 12.5)):
            parts.append(text(x + 16, by0 + 72 + j * 16, line, "tableText"))
        if i < 4:
            parts.append(path([(x + bw + 4, by0 + bh / 2), (x + bw + 56, by0 + bh / 2)], width=3))

    # ---- rules -----------------------------------------------------------
    rules_y = by0 + bh + 48
    parts.append(text(MARGIN, rules_y, "Rules that hold across the whole timeline", "section"))
    rw = (W - 2 * MARGIN - 2 * GAP) / 3
    rule_cards = [Card({"title": t, "sections": [("DOES", items)]}, rw, "#94a3b8") for t, items in RULES]
    rh = max(c.height for c in rule_cards)
    for i, card in enumerate(rule_cards):
        parts.append(card.draw(MARGIN + i * (rw + GAP), rules_y + 16, rh))
    height = int(rules_y + 16 + rh + 36)

    body = "\n  ".join(parts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" role="img" aria-labelledby="t d">
  <title id="t">2027 Autonomous Navigation: data synthesis, VSLAM, and integration pipeline</title>
  <desc id="d">Swimlane diagram of data synthesis, VSLAM, and integration across five phases (shared preflight, parallel subteam work, bundle validation, package conversion, GPS), listing each responsibility's inputs, outputs, functionality, dependencies, acceptance checks and exclusions, followed by the handoff bundle, contracts, and TF ownership chain.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="{LINE}"/></marker>
    <marker id="arrowPurple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="{PURPLE}"/></marker>
    <style>
      text {{ fill: {BODY}; }}
      .title {{ font-size: 28px; font-weight: 700; fill: {INK}; }} .subtitle {{ font-size: 15px; fill: {MUTED}; }}
      .section {{ font-size: 20px; font-weight: 700; fill: {INK}; }}
      .phase {{ font-size: 17px; font-weight: 700; fill: {INK}; }} .phaseSub {{ font-size: 12.5px; fill: {MUTED}; }}
      .lane {{ font-size: 20px; font-weight: 700; }} .laneRole {{ font-size: 13px; font-weight: 700; fill: {INK}; }}
      .cardTitle {{ font-size: 16px; font-weight: 700; fill: {INK}; }} .cardSub {{ font-size: 12px; font-style: italic; fill: {MUTED}; }}
      .body {{ font-size: {FONT}px; fill: {BODY}; }}
      .note {{ font-size: 12px; fill: #334e68; }} .noteBold {{ font-size: 12px; font-weight: 700; fill: #334e68; }}
      .small {{ font-size: 12px; fill: {MUTED}; }} .smallBold {{ font-size: 12.5px; font-weight: 700; fill: {INK}; }}
      .tableText {{ font-size: 12.5px; fill: {BODY}; }} .frame {{ font-size: 20px; font-weight: 700; font-family: Menlo,Consolas,monospace; fill: {INK}; }}
      .chip {{ font-size: 11px; font-weight: 700; fill: #ffffff; letter-spacing: 0.3px; }}
      .tag {{ font-size: 11px; font-weight: 700; fill: #ffffff; letter-spacing: 0.2px; }}
    </style>
  </defs>
  <rect width="{W}" height="{height}" fill="{PAGE}"/>
  {body}
</svg>
'''


if __name__ == "__main__":
    OUTPUT.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
