# Plan: phases, gates, and schedule (October 7 – 31, 2026, then mapping)

After a short bring-up, **Phases 1, 2 and 3 run at the same time**, starting Oct 10. Each one ends at its own gate. Phase 4 (mapping) starts after the Oct 30 handoff. Parallel work is possible because every phase's inputs and outputs are fixed below and each input has a **stand-in** you can use until the real producer is ready. A gate passes only when its checks pass on the real rover computer, or on recorded sessions where stated.

Task IDs (F3, P4, R6, M2, …) are in [TASKS.md](TASKS.md). Topic details are in [CONTRACT.md](CONTRACT.md). Who does what, and the team sync meetings at each gate, are in [TEAM.md](TEAM.md).

## At a glance

| Phase | Name | Runs | Delivers | Ends at |
| --- | --- | --- | --- | --- |
| 0 | Bring-up | Wed Oct 7 – Fri Oct 9 | The ZED camera and IMU visible in ROS 2 on Ubuntu 22.04 | **G0** Oct 9 |
| 1 | Fusion | Sat Oct 10 → Fri Oct 16 | A measured, trusted camera + IMU pose and TF tree | **G1** Oct 16 |
| 2 | Perception | Sat Oct 10 → Fri Oct 23 | Depth turned into a labelled **local** grid, a scan, 3D objects and a health signal | **G2** Oct 23 |
| 3 | Recording and integration | Sat Oct 10 → Fri Oct 30 | Data everyone can test on, one launch command, and the handoff to the algorithm team | **G3** Oct 30 |
| — | Buffer | Sat Oct 31 | Fixes only, no new features | — |
| 4 | Mapping | From Mon Nov 2 (end date to be set) | A **persistent** labelled map of a whole area in `map`, saved and reloadable | **G4** |

```text
            Oct 7  8  9 |10 11 12 13 14 15 16 |17 ... 23 |24 ... 30 |31 | Nov 2 →
Phase 0     ■■■■■■■■■■■ G0
Phase 1                 ■■■■■■■■■■■■■■■■■■■■■ G1
Phase 2                 ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ G2
Phase 3                 ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ G3
                              C0 (Mon Oct 12): interfaces frozen, stand-ins exist
Phase 4                                                               buffer  ■■■■■ → G4
```

**Local grid vs persistent map.** Phase 2's grid is a 10 m window in `odom` that moves with the rover and forgets what falls out of it. It answers "what is around me right now". Phase 4's map covers the whole area in `map`, keeps what it saw, and is saved to disk. It answers "what does this building look like". Phase 4 is built from Phase 2's output.

## The pipeline, stage by stage

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
   (M1–M6, Phase 4)    handle relocalization jumps (M3), map node (M4), save/reload (M5),
                       freeze map interface (M6)
```

How each stage works is explained in [README.md](README.md#background-how-each-stage-works).

## Rules for parallel work and the schedule

1. **The edges are the contract.** Topic names, message types, frames, file formats and the `core/` function signatures on this page are frozen at **checkpoint C0 (Mon Oct 12)**. After C0, changing one needs agreement from the consuming phase. After G2, changes to topic names, frames, or label codes also need a contract version bump and a message to the algorithm team.
2. **Build against stand-ins, not against each other.** Every input has a stand-in. Build against it and switch to the real producer when it passes its gate. Nobody waits.
3. **One owner per file.** Each phase owns its own package and launch file (table below), so merges do not collide. Phase 3 owns the top-level launch and only *includes* the others.
4. **Logic without ROS first.** Perception and mapping logic live in `core/` (plain Python + numpy) and run on frame dumps (interface I3) before any ROS node exists.
5. **Fusion problems come first.** If G1 is not met, fixing it takes priority over new perception features; Phase 2 keeps going on recordings meanwhile.
6. **Record once, test many times.** Every algorithm change is checked on the reference sessions before a live test.
7. **Cut scope, not quality.** If time runs short, drop in this order: YOLO objects (P7), confidence layer (part of P5), area memory (F7 decision = off, which pushes Phase 4 later). Never drop the health signal or the "unseen is unknown" rule.
8. **No motor commands** are part of any gate. The rover is pushed or driven manually by a person.
9. **Phase 4 does not start before G3.** It must not take people away from the Oct 30 handoff.

| Phase | Owns these files | Must not edit |
| --- | --- | --- |
| 1 Fusion | `rover_description/` (URDF), `rover_bringup/config/zed_overrides.yaml`, `rover_bringup/launch/fusion.launch.py`, `scripts/imu_check.py`, fusion report | perception or mapping code |
| 2 Perception | `rover_perception/` (`core/`, `nodes/`, `config/`), `rover_bringup/launch/perception.launch.py` | ZED parameters, URDF |
| 3 Recording + integration | `rover_bringup/launch/rover.launch.py`, `rover_bringup/scripts/` (record, replay, manifest, frame dump, stand-ins), `rover_bringup/rviz/`, `CONTRACT.md`, handoff bags | algorithm logic inside `core/` |
| 4 Mapping | `rover_mapping/` (new package), `rover_bringup/launch/mapping.launch.py` | `rover_perception/core/` (asks Phase 2 instead) |
| — | Legacy `main.py`, `slam/`, `object_detection.py` | Read-only for everyone (decision D8). Copy ideas, do not edit. |

---

## Interfaces between phases

Every arrow between phases is one of these. "Stand-in" is what you use until the real producer is ready.

| ID | What travels | Producer → consumer | Format | Stand-in until real | Real by |
| --- | --- | --- | --- | --- | --- |
| I1 | Camera and IMU topics | Phase 1 → 2, 3, 4 | `/rover/camera/rgb/*`, `/rover/camera/depth/*`, `/rover/imu` (contract §1) | ZED wrapper with default settings (Phase 0), or SVO replay through the wrapper | C0 Oct 12 (names), G1 (tuned) |
| I2 | Pose and TF | Phase 1 → 2, 3, 4 | `/rover/odom`, `/rover/pose`, `/tf`, `/tf_static` (contract §1–2) | `fake_pose` node (R6) that replays a TUM trajectory as `/rover/odom` + `odom → base_link`; URDF with an identity camera mount (so the TUM camera pose stands in for `base_link`) | G1 Oct 16 |
| I3 | Frame dumps (no ROS) | Phase 3 → 2 (and 4) | Folder format below | Phase 2 writes synthetic dumps for unit tests (flat floor, wall at 2 m, box) | C0 Oct 12, sessions (a) and (b) |
| I4 | Reference sessions and bags | Phase 3 → 1, 2, 4 | SVO + rosbag2 MCAP + manifest (contract §12) | Legacy `main.py --save-svo` SVO files from Phase 0 | G1 Oct 16 (ROS bags) |
| I5 | Fusion facts | Phase 1 → 2, 3 | Fusion report: latency, failure table (F6), area-memory decision (F7) | Thresholds in contract §4 (0.5 s stale, 0.3 m jump) | G1 Oct 16 |
| I6 | Perception topics | Phase 2 → 3, 4, algorithm team | `/rover/perception/*`, `/rover/status/ok`, `/diagnostics` (contract §1, §3) | `fake_perception` node (R6) that publishes a fixed synthetic grid, class grid and scan | G2 Oct 23 |
| I7 | Launch includes | Phases 1, 2, 4 → Phase 3 | Each phase ships one `*.launch.py` that starts its nodes and takes `use_sim_time` | Empty launch files from S5 | each phase's gate |
| I8 | Persistent map | Phase 4 → algorithm team | `/rover/map/*` topics + saved map folder (contract §9) | none needed: nobody depends on it before G3 | Phase 4 gate G4 |

### I3 frame-dump format (Phase 3 writes, Phase 2 and 4 read)

Made by `rover_bringup/scripts/svo_to_frames.py` (R5) from any SVO, without ROS. Units and axes follow [CONTRACT.md](CONTRACT.md) §0.

```text
frames/<session_id>/
  intrinsics.json   # {"fx", "fy", "cx", "cy", "width", "height"} of the rectified left image = depth image
  mount.json        # T_base_cam: base_link -> left camera, 4x4, camera BODY axes (X fwd, Y left, Z up).
                    #   = manifest base_link -> zed_camera_link (placeholder for now) composed with the
                    #   SDK's zed_camera_link -> left camera offset. Has "placeholder": true/false.
  frames.csv        # frame_idx, t_ns, tracking_state, tx, ty, tz, qx, qy, qz, qw
                    #   T_world_cam: pose of the LEFT CAMERA, BODY axes, in the ZED world frame
                    #   (Z up, X forward), IMU fusion on. Pose columns empty when tracking_state != OK.
  depth/000000.npy  # float32 H×W metres; NaN / +inf / -inf kept exactly as the SDK gives them
  rgb/000000.png    # optional, left image (BGR), only when --rgb is passed
```

Default stride: every 3rd frame (about 10 Hz from a 30 fps SVO). Sessions are stored outside Git, like SVOs.

**Frames, so the code works for any camera mount.** Offline, `odom` is defined as `base_link` at the first frame with a valid pose (frame 0), matching the live wrapper. Each frame's camera pose in `odom` and the conversion from pixels to `odom` points are:

```text
T_odom_cam(t) = T_base_cam · T_world_cam(0)⁻¹ · T_world_cam(t)          # 4x4, camera body axes
p_opt         = depth · K⁻¹ · [u, v, 1]ᵀ                                  # optical axes: X right, Y down, Z fwd
p_odom        = T_odom_cam(t) · R_body_opt · p_opt
R_body_opt    = [[0, 0, 1], [-1, 0, 0], [0, -1, 0]]                       # optical -> body, fixed
```

`T_base_cam` comes only from `mount.json`. No other number about the mount appears in `core/`, so a new rover changes one file.

### `core/` function signatures (Phase 2 internal, frozen at C0 so its tasks can be split)

These let P2, P3, P4 and P5 be written by different people at the same time, each against synthetic arrays.

```python
# rover_perception/core/points.py   (P2)
depth_to_points(depth: np.ndarray, K: Intrinsics, T_odom_cam: np.ndarray, stride: int = 4,
                min_m: float = 0.3, max_m: float = 8.0) -> np.ndarray      # (N, 3) float32 in odom
#   T_odom_cam: 4x4, camera BODY axes -> odom (formula above); the function applies R_body_opt itself.

# rover_perception/core/ground.py   (P3)
split_ground(points: np.ndarray, params: GroundParams) -> GroundSplit      # .ground (N,3), .obstacle (M,3), .plane (a,b,c,d)

# rover_perception/core/grid.py     (P4)
class LocalGrid:
    update(ground: np.ndarray, obstacle: np.ndarray, sensor_xyz: np.ndarray, t_ns: int) -> None
    recentre(rover_xy: np.ndarray) -> None
    clear() -> None
    snapshot() -> GridSnapshot   # .occupancy, .labels, .confidence: int8 H×W; .origin_xy, .resolution, .t_ns

# rover_perception/core/classify.py (P5)
classify(occupancy: np.ndarray, obstacle: np.ndarray, resolution: float, params: ClassifyParams) -> np.ndarray  # int8 label codes (contract §3)
```

`GridSnapshot` is also the input to Phase 4's `core/`, so mapping can be developed on Phase 2 output from frame dumps, without ROS.

## Checkpoint C0: Mon Oct 12

Not a gate, but everything parallel depends on it. C0 passes when:

- Topic names, frames, the frame-dump format and the `core/` signatures above are agreed (H2 draft).
- Frame dumps of sessions (a) and (b) exist (R5).
- `fake_pose` and `fake_perception` publish the contract topics (R6).
- `fusion.launch.py`, `perception.launch.py` and `rover.launch.py` exist and build, even if mostly empty (S5).

---

## Phase 0: Bring-up (Oct 7–9)

**Goal.** A pinned Ubuntu 22.04 / ROS 2 Humble / ZED stack where the camera and IMU are visible in RViz.

| | |
| --- | --- |
| **Inputs** | Rover computer, ZED camera, [SETUP.md](SETUP.md) |
| **Existing code used** | `main.py --save-svo` to record the first reference sessions (a)–(e) as SVO, so nobody waits for ROS |
| **Tasks** | S1–S5 (S6 finishes in Phase 1); in parallel, R4 early option |
| **Outputs** | Working wrapper launch; empty packages that build (S5); SVO sessions (a) and (b) at minimum |

**G0 passes when:**

- The rover computer reports Ubuntu 22.04 and sees the GPU.
- The ZED wrapper (pinned tag) launches and RGB, depth, and IMU appear in RViz.
- `ros2 topic hz` shows steady depth and IMU rates.
- At least sessions (a) and (b) exist as SVO files.

**If G0 slips:** the most likely cause is the OS/JetPack version (a Jetson on JetPack 5 is Ubuntu 20.04 and needs reflashing to JetPack 6). Fall back to an x86 Ubuntu 22.04 machine with an NVIDIA GPU for development and keep reflashing in parallel. Phase 2 `core/` work and Phase 3 frame dumps do not need ROS and continue regardless.

---

## Phase 1: Fusion (Oct 10 → G1 Oct 16)

**Goal.** The ZED's camera + IMU pose is correct, measured, and understood when it fails. We configure and prove the SDK's fusion; we do not write our own (decision D2).

### Inputs

| Input | From | Stand-in if not ready |
| --- | --- | --- |
| Wrapper running on the rover computer | Phase 0 (S4) | x86 Ubuntu 22.04 machine with an NVIDIA GPU |
| Measured camera mount | tape measure (F1) | identity transform |
| Recordings for fusion on/off comparison | Phase 3 (I4) | SVO files from `main.py --save-svo` |

### Existing code that feeds this phase

| Code | Use |
| --- | --- |
| `main.py` `_build_tracking_params` (IMU fusion on, area memory on) and `_build_init_params` (depth 0.2–20 m, HD720 at 30 fps) | Known-good settings to reproduce in `zed_overrides.yaml` (F2) |
| `main.py` TUM export (`zed_trajectory.txt`), with and without `--no-imu` | Quick fusion-on vs fusion-off comparison with `evo` before ROS bags exist (F5) |
| `main.py` IMU read (`get_sensors_data(..., TIME_REFERENCE.IMAGE)`) | Shows the legacy IMU is per-frame only; full rate comes from the wrapper (F3) |
| `slam/zed_vo_core.py` `DisplacementTracker.summary()` | Path length and net displacement for the closed-loop test (F5) |

### Outputs (what other phases can rely on after G1)

| Output | Type / location | Consumer |
| --- | --- | --- |
| `/rover/odom` | `nav_msgs/Odometry`, `odom` → `base_link` | Phase 2 (grid placement), Phase 4, algorithm team |
| `/rover/pose` | `geometry_msgs/PoseWithCovarianceStamped`, `map` | Phase 4 |
| `/rover/imu` | `sensor_msgs/Imu`, `zed_imu_link`, ≥ 100 Hz | Phase 2 (gravity direction), algorithm team |
| `/tf`, `/tf_static` | One connected tree, one publisher per edge | Everyone |
| `zed_overrides.yaml`, `fusion.launch.py` | `rover_bringup/` | Phase 3 (top-level launch) |
| Fusion report | numbers, plots, failure table (F5, F6) | Phase 2 health thresholds (P8), contract §4 |
| Area-memory decision (F7) | contract | Phase 3 demo, Phase 4 (needs area memory on) |

**Tasks:** S6, F1–F7.

**G1 passes when** (the "sensor fusion fully operational" gate):

- `view_frames` shows one connected TF tree with one publisher per edge (F1).
- The IMU checks pass: rate, gravity magnitude, axis signs, timestamps (F3, F4).
- Fusion-on vs fusion-off comparison is written up with numbers and meets the odometry targets (F5).
- The failure behaviour of odometry and TF is documented for the lens-cover, blank-wall, dark, and fast-spin cases (F6).
- The area-memory decision is recorded (F7).

After G1, Phase 1 people move to P8 (health), P10 (performance) and H5 (soak test).

---

## Phase 2: Perception (Oct 10 → G2 Oct 23)

**Goal.** Turn each depth frame plus the pose into a labelled **local** picture: free / wall / obstacle / unknown, a `LaserScan`, 3D objects, and a health signal.

### Inputs

| Input | From | Stand-in if not ready |
| --- | --- | --- |
| Depth + intrinsics + pose, offline | Phase 3 frame dumps (I3) | synthetic arrays in unit tests |
| Depth + `camera_info` topics | Phase 1 (I1) | wrapper with defaults, or SVO replay |
| `odom → base_link → camera` TF | Phase 1 (I2) | `fake_pose` (R6) + identity mount |
| Tracking state, failure thresholds | Phase 1 (I5) | contract §4 thresholds |
| `models/best.pt` | repository | — |

### Existing code that feeds this phase

| Code | Use |
| --- | --- |
| `slam/zed_scene_core.py` `Config` (0.3–8.0 m range) and `preprocess_depth` | Depth range and invalid-depth handling in `points.py` (P2) |
| `slam/zed_scene_core.py` `detect_walls`, `detect_hallway` | Ideas for the wall test in `classify.py` (P5). The legacy code works in image space; the new code works in the grid. |
| `slam/zed_scene_core.py` `find_forward_clusters` | Reference behaviour for obstacle checks on session (c) |
| `object_detection.py` `ObjectDetector.run` and `_sample_depth` | YOLO + depth per box, wrapped into a ROS node for `/rover/perception/objects` (P7) |
| `models/best.pt` | YOLO weights; class names from `model.names` |

### Outputs (I6, after G2)

| Output | Type / frame | Consumer |
| --- | --- | --- |
| `/rover/perception/grid` | `OccupancyGrid`, `odom` | Phase 3, algorithm team |
| `/rover/perception/class_grid`, `/confidence` | `OccupancyGrid`, `odom`, label codes in contract §3 | Phase 4 (main input), algorithm team |
| `/rover/perception/obstacle_points` | `PointCloud2`, `odom` | Phase 4 (optional), algorithm team |
| `/rover/perception/scan` | `LaserScan`, `base_link` | algorithm team |
| `/rover/perception/objects` | `vision_msgs/Detection3DArray`, `base_link` | algorithm team |
| `/rover/status/ok`, `/diagnostics` | `Bool`, `DiagnosticArray` | Phase 3 (soak test), Phase 4 (skip bad frames), algorithm team |
| `perception.launch.py`, `core/` + unit tests | `rover_perception/` | Phase 3 |

**Tasks:** P1–P8 and P10, plus H4 (unit tests) alongside. Order inside the phase: P2 → P3 → P4 → P5 on frame dumps first; P1, P6, P7 can start on day one in parallel. Until G1 and the ROS bags exist, P2–P5 run on frame dumps and P1, P6, P7 run on the wrapper's default output or `fake_pose`.

**G2 passes when** (on recorded sessions):

- Grid, class grid, scan, and objects publish at target rates from bag replay (P4–P7).
- On the hallway session, walls are labelled wall, the floor is free, and areas behind walls are unknown (P4, P5).
- On the cluttered-room session, boxes and chairs are labelled obstacle; YOLO objects are within 10% of measured distance (P5, P7).
- Lens-cover replay flips the health signal (P8).
- Unit tests pass (H4).

---

## Phase 3: Recording and integration (Oct 10 → G3 Oct 30)

**Goal.** Give Phases 1 and 2 data and stand-ins from day one, then join everything into one launch command and hand it to the algorithm team.

### Inputs

| Input | From | Stand-in if not ready |
| --- | --- | --- |
| SVO sessions | Phase 0 (`main.py --save-svo`) | — |
| Wrapper topics | Phase 1 (I1, I2) | SVO replay through the wrapper |
| `fusion.launch.py`, `perception.launch.py` | Phases 1, 2 (I7) | empty launch files from S5 |
| Perception topics | Phase 2 (I6) | `fake_perception` (R6) |
| Session format | contract §12, [`contract/session_manifest.example.json`](contract/session_manifest.example.json) | — |

### Existing code that feeds this phase

| Code | Use |
| --- | --- |
| `main.py --save-svo` / `--svo` | Early recordings and SVO replay (R4 early option) |
| `main.py` `_build_init_params` (`set_from_svo_file`, `svo_real_time_mode = False`) | How to open an SVO without ROS in `svo_to_frames.py` (R5) |
| `main.py` TUM export | Trajectory that `fake_pose` replays (R6) |
| Contract §12 + example manifest | Manifest writer (R2) |

### Outputs

| Output | Location | Consumer |
| --- | --- | --- |
| Frame dumps (I3) | `frames/<session_id>/`, outside Git | Phase 2, Phase 4 |
| `fake_pose`, `fake_perception` stand-ins (R6) | `rover_bringup/scripts/` | Phase 2, Phase 3 itself, algorithm team (early) |
| Reference sessions (a)–(e) as SVO + bag + manifest (I4) | shared index of paths and checksums | Phases 1, 2, 4 |
| `record_session.sh`, replay instructions | `rover_bringup/scripts/` | everyone |
| `rover.launch.py` (live / SVO / bag; YOLO on/off) | `rover_bringup/launch/` | demo, algorithm team |
| RViz config | `rover_bringup/rviz/rover.rviz` | everyone |
| Contract v1.0, handoff bags, `HANDOFF_README` | `docs/CONTRACT.md`, shared storage | algorithm team |

**Tasks:** R1–R6 first (data and stand-ins), then P9, H1, H2, H3, H5, H6. H4 is shared with Phase 2.

**Checkpoints on the way:**

- C0 Oct 12: frame dumps and stand-ins exist (R5, R6).
- G1 Oct 16: ROS bags of sessions (a)–(e) recorded and replayable, with manifests (R1–R4).
- G2 Oct 23: `rover.launch.py` runs Phases 1 + 2 from a bag, and RViz shows every output (H1 draft, P9).

**G3 passes when:**

- One launch command brings everything up on the rover in under 60 s (H1).
- All rate and latency targets are met with everything running on the rover computer (P10).
- The 10-minute live soak test passes (H5).
- [CONTRACT.md](CONTRACT.md) v1.0 is frozen with no **[verify]** items left (H2).
- The algorithm team replays the handoff bags on their own machine and sees every output (H3).
- Live demo: the rover is pushed or driven manually through a hallway and a cluttered area while RViz shows pose, labelled grid, scan, objects, and health (H6).

---

## Phase 4: Mapping (after G3, from Nov 2; end date to be set)

**Goal.** Build a **persistent** labelled map of a whole area (free / wall / obstacle / unknown) in the `map` frame, save it, and reload it in a later session so the same building lines up.

Phase 4 starts after G3 so that it does not take people away from the Oct 30 deliverable. All of its inputs exist at G3, and its `core/` can be developed on frame dumps and handoff bags without the rover. Exact dates are set at the G3 demo, together with the algorithm team's November requests.

### Inputs

| Input | From | Notes |
| --- | --- | --- |
| `/rover/perception/class_grid`, `/confidence` (or `GridSnapshot` from frame dumps) | Phase 2 (I6) | The main thing a persistent map is made of |
| `/rover/pose`, `map → odom` TF | Phase 1 (I2) | Places each local grid in `map` |
| `/rover/status/ok` | Phase 2 | Do not add grids while tracking is lost |
| Area-memory behaviour (F7) and relocalization jump sizes (F6) | Phase 1 (I5) | Phase 4 needs area memory **on** so `map` is the same frame across sessions |
| Handoff bags (b) and (c) | Phase 3 (I4) | Test data |

### Existing code that feeds this phase

| Code | Use |
| --- | --- |
| `main.py` `--area-map` and `disable_positional_tracking(<file>)` | How the ZED saves and reloads its area map; the wrapper equivalent is configured in Phase 1's overrides |
| `rover_perception/core/grid.py` `GridSnapshot`, label codes | Reused as is; the map uses the same codes |

**Approach (decision M1, first task of the phase).** Pick one and record why:

| Option | How | Keeps D4 (ZED owns `map → odom`)? |
| --- | --- | --- |
| A (default) | Our `rover_mapping` node merges each `class_grid` snapshot into a fixed `map`-frame grid using `map → odom`, with the same log-odds rules; ZED area memory keeps `map` consistent between sessions | Yes |
| B | `slam_toolbox` builds the map from `/rover/perception/scan`: it matches each scan against earlier ones, adds loop closures, and optimises a pose graph | No: `slam_toolbox` would publish `map → odom`, so the ZED map TF must be turned off and D4 revised |
| C | ZED SDK spatial mapping (fused 3D mesh / cloud), projected to 2D | Yes, but labels must be recomputed from the 3D map |

### Outputs (I8, draft; final in contract §9)

| Output | Type / location | Meaning |
| --- | --- | --- |
| `/rover/map/grid` | `OccupancyGrid`, `map`, latched (transient local) | Persistent free / occupied / unknown |
| `/rover/map/class_grid` | `OccupancyGrid`, `map`, latched | Same label codes as contract §3 |
| `maps/<map_id>/` | `map.yaml` + `map.pgm` (Nav2 `map_server` format), `class.pgm`, `area_map.area`, `map_manifest.json` | Saved map, reloadable with `rover.launch.py map:=<map_id>`; stored outside Git |

**Tasks:** M1–M6 in [TASKS.md](TASKS.md).

**G4 passes when:**

- A map of the hallway + cluttered-room route is saved, then reloaded in a new session, and lines up with the live local grid within a stated tolerance (M4, M5).
- Walls and obstacles keep their labels in the saved map (M2).
- A relocalization jump does not smear or duplicate walls (M3).
- The map topics and saved-map format are frozen in [CONTRACT.md](CONTRACT.md) §9 (M6).

---

## Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Rover computer is not on Ubuntu 22.04 (for example JetPack 5) | Phase 0 slips by days | Develop on an x86 22.04 machine; reflash in parallel |
| SDK, CUDA, and wrapper versions do not match | Wrapper fails to build or crashes | Pin the wrapper tag to the SDK major version; record versions (S6) |
| Interfaces change after C0 | Parallel work has to be redone | Freeze at C0; stand-ins publish exactly the contract names; changes go through the consuming phase |
| Not enough compute for depth + tracking + YOLO + grid | Rates miss targets | Lower resolution or frame rate, lighter depth mode, YOLO at a lower rate or off (P10) |
| Indoor scenes with blank walls or poor light | Tracking loss | IMU fusion, failure documentation (F6), health signal (P8) |
| Reflective or dark floors give bad depth | False obstacles or holes | Confidence threshold, "unseen is unknown" rule, test in the real environment early |
| Area memory turned off for the demo (F7) | No consistent `map` frame for Phase 4 | Phase 4 starts with M1 re-testing area memory; option B or C as fallback |

## Where the schedule is likely to bottleneck

Ordered roughly by how soon each one can bite (written Tue Oct 13, just after C0).

| # | Bottleneck | Why it bottlenecks | What it blocks | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | **Platform chain S1 → S3 → S4** | Strictly serial and version-sensitive. It is the start of the critical path. | Every live ROS task: F1–F7, P1, R1, R3, H1. | x86 22.04 fallback machine; pin versions (S6). Offline `core/` work continues regardless. |
| 2 | **C0 deliverables from Phase 3 (R5 frame dumps, R6 stand-ins)** | Phase 3 must feed everyone *before* it does its own work. If dumps or stand-ins are late or wrong, Phases 1–2 either wait or build on guesses. | P2–P5 offline development, P9, early algorithm-team work. | Confirm C0 actually passed. If not, it is the top priority. |
| 3 | **One rover, one camera** | F3, F5, F6, R4, P7 distance checks, H5 soak and H6 demo all need the hardware, and tests like lens-cover or 5-minute static runs occupy it. | G1 (F5 needs R4 sessions), G2 checks, G3 soak. | Capture sessions (a)–(e) early and in one block, then do everything possible on replay. Schedule rover time explicitly. |
| 4 | **F5 → F6 → P8 / H2 chain** | F5 needs F1–F3 *and* R4; F6 needs F5; P8 thresholds and the contract failure table need F6. Fusion problems also take priority (rule 5). | G1, then P8 health, then H2 contract. | Use the contract §4 placeholder thresholds (0.5 s stale, 0.3 m jump) in P8 until F6 lands. |
| 5 | **Serial perception chain P2 → P3 → P4 → P5** | Each stage consumes the previous one's output. P5 is the most judgment-heavy step, needs reviewer sign-off, and sits last. | G2 class-grid checks, Phase 4 input. | Frozen `core/` signatures let all four start on synthetic arrays at once; integrate early on frame dumps. |
| 6 | **Compute budget (P10) is measured last** | Depth + tracking + YOLO + grid share one GPU/CPU. P4 ray-casting ~50k points per frame at ≥ 5 Hz in Python is a likely hotspot unless vectorised. | G3 "all targets met on the rover computer". | Profile on the rover computer as soon as P1–P4 run, not only at P10. |
| 7 | **Integration crunch, Oct 24–30** | H1 needs F2 + P1–P9; H2 needs F6, F7, P10; H3 needs H1 + H2; H5 needs H1; H6 needs all. Five tasks converge on one week with a one-day buffer. | G3. | Phase 1 people move to P8 / P10 / H5 after G1. Draft `rover.launch.py` from a bag by G2. |
| 8 | **External review: algorithm team** | H2 is done only when the algorithm team has "no open questions"; H3 when they replay bags unaided; F7 and M1 need their agreement. | G3, Phase 4 start. | Share the draft contract and stand-in topics early so review is incremental. |
| 9 | **[verify] items** | Topic, frame and parameter names depend on the pinned wrapper tag and camera model. Each unresolved one blocks contract v1.0. | H2, and anything hard-coding names. | Resolve them as soon as S4 is pinned; the launch file remaps to `/rover/...` names so consumers do not change. |
| 10 | **Phase 4: area memory and relocalization (F7, M1, M3)** | If F7 turns area memory off, there is no stable `map` frame across sessions. M3 is the hardest mapping task. | G4. | M1 re-tests area memory first; options B and C are fallbacks. |

**Single biggest risk to Oct 30:** items 3 and 7 together. Hardware time is shared across every track, and all integration work lands in the final week.
