# SLAM Pipeline Overview

A one-page view of the October 2026 milestone in [README.md](README.md): how sensor data turns into pose, a labelled local map, and (in Phase 4) a persistent map. Task IDs in parentheses are from [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md); phases and gates are from [PHASES.md](PHASES.md) and [TIMELINE.md](TIMELINE.md). Nothing here adds scope. It summarises those docs, flags likely bottlenecks, and explains the science behind each stage.

**What "SLAM" means this month.** We do not write our own SLAM (decision D2). The ZED SDK provides visual-inertial odometry (the "localization" half) and area memory (relocalization). We build the **local mapping** half on top of it (Phase 2), and a **persistent map** after Oct 30 (Phase 4).

---

## 1. The pipeline

Read top to bottom. Each stage lists its main tasks and phase.

```text
0. PLATFORM            Ubuntu 22.04 + ROS 2 Humble + ZED SDK + pinned zed-ros2-wrapper
   (S1–S6, Phase 0)    Package skeletons: rover_description, rover_bringup, rover_perception
        │
        ▼
1. SENSE               ZED stereo camera + built-in IMU
   (F2, Phase 1)       → rectified RGB, depth image (32FC1, m), camera_info, IMU ≥ 100 Hz
        │
        ├──────────────► 1b. RECORD / REPLAY  (R1–R6, Phase 3)
        │                    SVO + rosbag2 MCAP + manifest, reference sessions (a)–(e),
        │                    frame dumps (no ROS), fake_pose / fake_perception stand-ins.
        │                    Feeds every later stage so work does not need the rover.
        ▼
2. LOCALIZE            Visual-inertial odometry inside the ZED SDK (we configure, not write)
   (F1–F7, Phase 1)    → /rover/odom (odom → base_link, smooth)
                       → /rover/pose + map → odom (area memory, may jump)
                       Checks: IMU validation (F3), timing (F4), fusion on vs off (F5),
                       failure cases (F6), area-memory decision (F7). Mount + URDF (F1).
        │  pose + TF
        ▼
3. BUILD 3D POINTS     Subsample depth (every 4th px), keep 0.3–8 m, drop NaN/±inf,
   (P1, P2, Phase 2)   back-project with intrinsics, transform into odom
        ▼
4. REMOVE GROUND       RANSAC floor plane, constrained near horizontal using IMU gravity;
   (P3, Phase 2)       split points into ground vs obstacle (height band)
        │
        ├──────────────► 4b. SCAN  (P6)  obstacle points → PointCloud2 → LaserScan in base_link
        ▼
5. LOCAL GRID          Rolling 10 m × 10 m, 5 cm cells in odom; ray-cast free space,
   (P4, Phase 2)       mark hits occupied, log-odds update with slow decay; unseen = unknown
        ▼
6. CLASSIFY            Fit straight segments to occupied cells → wall vs obstacle;
   (P5, Phase 2)       per-cell confidence from observation count and age
        │
        ├──────────────► 6b. OBJECTS  (P7)  YOLO (models/best.pt) on RGB + median box depth
        │                     → Detection3DArray in base_link (labels on top of geometry, D6)
        ▼
7. HEALTH              Tracking state, valid-depth fraction, grid age, latency
   (P8, Phase 2)       → /rover/status/ok, /diagnostics
        ▼
8. INTEGRATE + HAND OFF  One launch command (H1), RViz config (P9), performance tuning (P10),
   (Phase 3, G3 Oct 30)  contract v1.0 (H2), handoff bags (H3), tests (H4), soak (H5), demo (H6)
        ▼
9. PERSISTENT MAP      Pick approach (M1), merge local grids into map frame (M2),
   (M1–M6, Phase 4,    handle relocalization jumps (M3), map node (M4), save/reload (M5),
    after Nov 2)       freeze map interface (M6)
```

Gates: **G0** Oct 9 (camera + IMU in RViz) · **C0** Oct 12 (interfaces frozen, stand-ins exist) · **G1** Oct 16 (fusion measured) · **G2** Oct 23 (labelled grid correct on recordings) · **G3** Oct 30 (live demo + handoff) · **G4** after Nov 2 (saved map reloads and lines up).

### Stage to track map

| Stage | Track | Tasks | Phase | Gate |
| --- | --- | --- | --- | --- |
| Platform | S Setup | S1–S6 | 0 | G0 |
| Sense + Localize | F Fusion | F1–F7 | 1 | G1 |
| Record / replay | R Recording | R1–R6 | 3 (first) | C0, G1 |
| Points → grid → classes → scan/objects → health | P Perception | P1–P8, P10 (P9 in Phase 3) | 2 | G2 |
| Integrate + hand off | H Handoff | H1–H6 | 3 | G3 |
| Persistent map | M Mapping | M1–M6 | 4 | G4 |

---

## 2. Where production is likely to bottleneck

Ordered roughly by how soon each one can bite. Today is Tue Oct 13, so C0 has just passed and G1 is three days out.

| # | Bottleneck | Why it bottlenecks | What it blocks | Mitigation already in the docs (or suggested) |
| --- | --- | --- | --- | --- |
| 1 | **Platform chain S1 → S3 → S4** | Strictly serial and version-sensitive (JetPack 5 vs 6, SDK / CUDA / wrapper tag mismatch). It is the start of the stated critical path. | Every live ROS task: F1–F7, P1, R1, R3, H1. | x86 22.04 fallback machine; pin versions (S6). Offline `core/` work continues regardless. |
| 2 | **C0 deliverables from Phase 3 (R5 frame dumps, R6 stand-ins)** | Phase 3 must feed everyone *before* it does its own work. If dumps or stand-ins are late or wrong, Phases 1–2 either wait or build on guesses. | P2–P5 offline development, P9, early algorithm-team work. | Confirm C0 actually passed. If not, it is the top priority this week. |
| 3 | **One rover, one camera** | F3, F5, F6, R4, P7 distance checks, H5 soak and H6 demo all need the physical hardware, and tests like lens-cover or 5-minute static runs occupy it. | G1 (F5 needs R4 sessions), G2 checks, G3 soak. | "Record once, test many times": capture sessions (a)–(e) early and in one block, then do everything possible on replay. Schedule rover time explicitly. |
| 4 | **F5 → F6 → P8 / H2 chain** | F5 needs F1–F3 *and* R4; F6 needs F5; P8 thresholds and the contract failure table need F6. Fusion problems also take priority over perception (schedule rule 2). | G1, then P8 health, then H2 contract. | Use contract §4 placeholder thresholds (0.5 s stale, 0.3 m jump) in P8 until F6 lands. |
| 5 | **Serial perception chain P2 → P3 → P4 → P5** | Each stage consumes the previous one's output. P5 (wall vs obstacle) is the most judgment-heavy step, needs reviewer sign-off, and sits last. | G2 class-grid checks, Phase 4 input. | Frozen `core/` signatures let all four start on synthetic arrays at once; integrate early on frame dumps rather than at the end. |
| 6 | **Compute budget (P10) is measured last** | Depth + tracking + YOLO + grid share one GPU/CPU. P4 ray-casting ~50k points per frame at ≥ 5 Hz in Python is a likely hotspot unless vectorised. A miss found at P10 forces late rework. | G3 "all targets met on the rover computer". | Profile on the rover computer as soon as P1–P4 run, not only at P10. Drop order: YOLO (P7) → confidence layer → area memory. |
| 7 | **Integration crunch, Oct 24–30** | H1 needs F2 + P1–P9; H2 needs F6, F7, P10; H3 needs H1 + H2; H5 needs H1; H6 needs all. Five tasks converge on one week with a one-day buffer (Oct 31). | G3. | Phase 1 people move to P8 / P10 / H5 after G1 (as planned). Draft `rover.launch.py` from a bag by G2. |
| 8 | **External review: algorithm team** | H2 is done only when the algorithm team has "no open questions"; H3 when they replay bags unaided; F7 and M1 need their agreement. Their availability is outside our control. | G3, Phase 4 start. | Share the draft contract and stand-in topics early so review is incremental, not a single meeting on Oct 30. |
| 9 | **[verify] items** | Topic, frame and parameter names depend on the pinned wrapper tag and camera model. Each unresolved one blocks freezing contract v1.0. | H2, and anything hard-coding names. | Resolve them as soon as S4 is pinned; the launch file remaps to `/rover/...` names so consumers do not change. |
| 10 | **Phase 4: area memory and relocalization (F7, M1, M3)** | If F7 turns area memory off for the demo, there is no stable `map` frame across sessions. M3 (no smeared walls after a jump) is the hardest mapping task. | G4. | M1 re-tests area memory first; options B (`slam_toolbox`) and C (ZED spatial mapping) are fallbacks. |

**Single biggest risk to Oct 30:** items 3 and 7 together. Hardware time is shared across every track, and all integration work lands in the final week.

---

## 3. The algorithms and science, briefly

### Stereo depth (Sense)
The ZED has two cameras a fixed distance apart (the baseline *B*). A point appears shifted between the left and right images by a *disparity* *d*. With focal length *f* in pixels, depth is **Z = f·B / d**. Depth error grows roughly with **Z²**: a one-pixel disparity error matters far more at 8 m than at 1 m. That is why we limit to 0.3–8 m (P2). Textureless, dark, or reflective surfaces give no reliable match, so those pixels come back as `NaN`/`±inf`. That is the reason for decision D7 ("no data never means free").

### Visual-inertial odometry (Localize, F1–F7)
The ZED SDK's internals are proprietary, but visual-inertial odometry (VIO) generally works like this. Visual features are tracked across frames to estimate camera motion. IMU readings (accelerometer + gyroscope, ≥ 100 Hz) are integrated between frames. The two are fused in a filter or optimiser. The two sensors fail in complementary ways:
- **Camera:** accurate over time, but fails with fast motion, blur, blank walls and darkness.
- **IMU:** high rate and works in the dark, but drifts quickly because integrating noisy acceleration twice compounds error.
- **Fused:** the IMU bridges short visual dropouts and fast turns, and gives the gravity direction (roll/pitch). The camera corrects the IMU's drift and bias.

Our tasks check that the inputs to this fusion are sound. F3 tests gravity magnitude ≈ 9.81 m/s², gyro bias, and axis signs per REP 103. F4 checks that timestamps share one clock, because fusing misaligned data corrupts the estimate. F5 compares fusion on vs off. Evaluation uses `evo`: **ATE** (absolute trajectory error) for overall drift and closed-loop end error, **RPE** (relative pose error) for local smoothness.

### Frames: `odom` vs `map` (REP 105)
`odom` is continuous and never jumps, but drifts slowly. `map` is drift-corrected but can jump when the system relocalizes. That is why the local grid and control live in `odom` (D4) and only the persistent map uses `map`. The ZED's **area memory** does the relocalization. It stores visual landmarks and, when it recognises a place, corrects `map → odom`. That is the loop-closure part of SLAM, provided by the SDK.

### Depth → 3D points (P2)
This is the pinhole camera model in reverse. A pixel (u, v) with depth Z becomes **X = (u − cx)·Z / fx, Y = (v − cy)·Z / fy**. The point is then transformed into `odom` with the pose from TF. Subsampling every 4th pixel cuts ~900k points to ~50k (D5) while keeping enough density for 5 cm cells.

### Ground removal (P3)
**RANSAC** (random sample consensus) repeatedly picks 3 random points, fits a plane, and counts how many other points lie close to it. The plane with the most inliers wins, so outliers (boxes, walls) cannot drag the fit. The IMU's gravity vector constrains the search to planes within ~10° of horizontal, so a large wall is never mistaken for the floor. Points in a height band above the plane (5 cm up to rover height + 10 cm) become obstacles.

### Occupancy grid (P4)
Each cell holds a probability of being occupied, stored as **log-odds** *l = log(p / (1 − p))*. Bayesian updates then become simple addition. For each depth return, a ray is traced from the camera to the hit (Bresenham-style line walk). Cells along the ray get a "free" increment and the hit cell gets an "occupied" increment. Slow decay lets the grid forget objects that moved. Cells never crossed by a ray stay **unknown**, which is the "unseen is unknown" rule enforced at the data-structure level. The grid is *rolling*: it recentres on the rover and discards what falls off the edge.

### Wall vs obstacle classification (P5)
Occupied cells are grouped into straight line segments, for example by RANSAC line fitting, Hough transform, or split-and-merge (the docs leave the method open). A segment ≥ 1.0 m long whose points span ≥ 0.5 m in height is labelled a wall; everything else occupied is an obstacle. Confidence rises with the number of observations and falls with age. Geometry-first labelling (D6) works on any object, whether or not YOLO was trained on it.

### LaserScan (P6)
Obstacle points are binned by bearing angle around `base_link`, keeping the nearest range per bin. This is the input format most 2D planners and SLAM tools already accept.

### Object detection (P7)
**YOLO** is a single-pass convolutional neural network that predicts bounding boxes and class scores for the whole image at once, which makes it fast enough for real time. Each box gets the **median** depth of its central region. The median resists stray background pixels at box edges. Back-projecting the centre gives a 3D position.

### Health monitoring (P8)
This is a rule-based watchdog, not an estimator. `status/ok` is true only if tracking is OK, enough depth is valid, and inputs are fresh (< 0.5 s). It lets downstream code distinguish "nothing is there" from "we cannot currently see".

### Persistent mapping (Phase 4)
- **Option A (default):** transform each local grid snapshot into `map` using `map → odom` at that time, then fuse with the same log-odds rules.
- **Option B:** `slam_toolbox` builds its own pose graph. It matches each laser scan against earlier ones, adds loop-closure constraints when it revisits a place, and optimises the graph, which means it takes over `map → odom`.
- **Option C:** project the ZED's fused 3D mesh to 2D.

The hard science problem in all three is **M3**. When a relocalization corrects the pose, cells fused under the old pose are in the wrong place. Keeping snapshots tied to their poses, so they can be re-placed, is what avoids doubled walls.
