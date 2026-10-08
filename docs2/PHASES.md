# Phases: deliverables, inputs, outputs, and how to work in parallel

This page describes each phase as a box with fixed edges: what goes in, what comes out, and what it delivers. If the edges are fixed, Phases 1, 2 and 3 can be built **at the same time** by different people, because every input has a **stand-in** you can use until the real producer is ready.

Dates and gates are in [TIMELINE.md](TIMELINE.md). Task IDs (F3, P4, R6, M2, …) are in [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md). Topic details are in [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md).

## At a glance

| Phase | Name | Runs | Delivers (one line) |
| --- | --- | --- | --- |
| 0 | Bring-up | Oct 7–9 | The ZED camera and IMU visible in ROS 2 on Ubuntu 22.04 |
| 1 | Fusion | Oct 10 → G1 Oct 16 | A measured, trusted camera + IMU pose and TF tree |
| 2 | Perception | Oct 10 → G2 Oct 23 | Depth turned into a labelled **local** grid, a scan, 3D objects and a health signal |
| 3 | Recording and integration | Oct 10 → G3 Oct 30 | Data everyone can test on, one launch command, and the handoff to the algorithm team |
| 4 | Mapping | After G3 (from Nov 2) | A **persistent** labelled map of a whole area in the `map` frame, saved and reloadable |

```text
            Phase 0 (bring-up)
                   │
   ┌───────────────┼────────────────┐
   ▼               ▼                ▼          ← all three start Oct 10
Phase 1         Phase 2          Phase 3
Fusion          Perception       Recording + integration
   │  pose/TF      │  local grid     │  sessions, launch, handoff
   └──────┬────────┴────────┬────────┘
          ▼                 ▼
     G3 Oct 30: integrated live demo + handoff
                   │
                   ▼
            Phase 4 (mapping)
```

**Local grid vs persistent map.** Phase 2's grid is a 10 m window in `odom` that moves with the rover and forgets what falls out of it. It answers "what is around me right now". Phase 4's map covers the whole area in `map`, keeps what it saw, and is saved to disk. It answers "what does this building look like". Phase 4 is built from Phase 2's output.

## How parallel work stays safe

1. **The edges are the contract.** Topic names, message types, frames, file formats and the `core/` function signatures in this page are frozen on **Mon Oct 12 (checkpoint C0)**. After C0, changing one needs agreement from the consuming phase.
2. **Every input has a stand-in.** Build against the stand-in, switch to the real producer when it lands. Nobody waits.
3. **One owner per file.** Each phase owns its own package and launch file (table below), so merges do not collide. Phase 3 owns the top-level launch and only *includes* the others.
4. **Logic without ROS first.** Perception and mapping logic live in `core/` (plain Python + numpy) and run on frame dumps (interface I3) before any ROS node exists.

| Phase | Owns these files | Must not edit |
| --- | --- | --- |
| 1 Fusion | `rover_description/` (URDF), `rover_bringup/config/zed_overrides.yaml`, `rover_bringup/launch/fusion.launch.py`, `scripts/imu_check.py`, fusion report | perception or mapping code |
| 2 Perception | `rover_perception/` (`core/`, `nodes/`, `config/`), `rover_bringup/launch/perception.launch.py` | ZED parameters, URDF |
| 3 Recording + integration | `rover_bringup/launch/rover.launch.py`, `rover_bringup/scripts/` (record, replay, manifest, frame dump, stand-ins), `rover_bringup/rviz/`, `OUTPUT_CONTRACT.md`, handoff bags | algorithm logic inside `core/` |
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
| I4 | Reference sessions and bags | Phase 3 → 1, 2, 4 | SVO + rosbag2 MCAP + manifest (`docs/SENSOR_DATA_CONTRACT.md` §4) | Legacy `main.py --save-svo` SVO files from Phase 0 | G1 Oct 16 (ROS bags) |
| I5 | Fusion facts | Phase 1 → 2, 3 | Fusion report: latency, failure table (F6), area-memory decision (F7) | Thresholds in contract §4 (0.5 s stale, 0.3 m jump) | G1 Oct 16 |
| I6 | Perception topics | Phase 2 → 3, 4, algorithm team | `/rover/perception/*`, `/rover/status/ok`, `/diagnostics` (contract §1, §3) | `fake_perception` node (R6) that publishes a fixed synthetic grid, class grid and scan | G2 Oct 23 |
| I7 | Launch includes | Phases 1, 2, 4 → Phase 3 | Each phase ships one `*.launch.py` that starts its nodes and takes `use_sim_time` | Empty launch files from S5 | each phase's gate |
| I8 | Persistent map | Phase 4 → algorithm team | `/rover/map/*` topics + saved map folder (contract §9) | none needed: nobody depends on it before G3 | Phase 4 gate G4 |

### I3 frame-dump format (Phase 3 writes, Phase 2 and 4 read)

Made by `rover_bringup/scripts/svo_to_frames.py` (R5) from any SVO, without ROS. Units and axes follow `docs/SENSOR_DATA_CONTRACT.md` §1.

```text
frames/<session_id>/
  intrinsics.json   # {"fx", "fy", "cx", "cy", "width", "height"} of the rectified left image = depth image
  frames.csv        # frame_idx, t_ns, tracking_state, tx, ty, tz, qx, qy, qz, qw
                    #   pose of the LEFT CAMERA in the ZED world frame (Z up, X forward), IMU fusion on.
                    #   Pose columns empty when tracking_state != OK.
  depth/000000.npy  # float32 H×W metres; NaN / +inf / -inf kept exactly as the SDK gives them
  rgb/000000.png    # optional, left image (BGR), only when --rgb is passed
```

Default stride: every 3rd frame (about 10 Hz from a 30 fps SVO). Sessions are stored outside Git, like SVOs.

### `core/` function signatures (Phase 2 internal, frozen at C0 so its tasks can be split)

These let P2, P3, P4 and P5 be written by different people at the same time, each against synthetic arrays.

```python
# rover_perception/core/points.py   (P2)
depth_to_points(depth: np.ndarray, K: Intrinsics, T_odom_cam: np.ndarray, stride: int = 4,
                min_m: float = 0.3, max_m: float = 8.0) -> np.ndarray      # (N, 3) float32 in odom

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

---

## Phase 0: Bring-up (Oct 7–9)

**Goal.** A pinned Ubuntu 22.04 / ROS 2 Humble / ZED stack where the camera and IMU are visible in RViz.

| | |
| --- | --- |
| **Inputs** | Rover computer, ZED camera, [SETUP_UBUNTU_22_04.md](SETUP_UBUNTU_22_04.md) |
| **Existing code used** | `main.py --save-svo` to record the first reference sessions (a)–(e) as SVO, so nobody waits for ROS |
| **Tasks** | S1–S5 (S6 finishes in Phase 1) |
| **Outputs** | Working wrapper launch; empty packages that build (S5); SVO sessions (a) and (b) at minimum |
| **Deliverables** | G0: camera + IMU in RViz, steady `ros2 topic hz`, SVO files exist |

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

**Deliverables (G1, Oct 16):** connected TF tree; IMU checks pass; fusion on vs off report with numbers that meet the targets; failure behaviour documented; area-memory decision recorded. After G1, Phase 1 people move to P8 (health), P10 (performance) and H5 (soak test).

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

**Tasks:** P1–P8 and P10, plus H4 (unit tests) alongside. Order inside the phase: P2 → P3 → P4 → P5 on frame dumps first; P1, P6, P7 can start on day one in parallel.

**Deliverables (G2, Oct 23, on recorded sessions):** all perception topics at target rates from bag replay; hallway and cluttered-room labels correct; lens-cover replay flips health; unit tests pass.

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
| Session format | `docs/SENSOR_DATA_CONTRACT.md` §4, `docs/contract/session_manifest.example.json` | — |

### Existing code that feeds this phase

| Code | Use |
| --- | --- |
| `main.py --save-svo` / `--svo` | Early recordings and SVO replay (R4 early option) |
| `main.py` `_build_init_params` (`set_from_svo_file`, `svo_real_time_mode = False`) | How to open an SVO without ROS in `svo_to_frames.py` (R5) |
| `main.py` TUM export | Trajectory that `fake_pose` replays (R6) |
| `docs/SENSOR_DATA_CONTRACT.md` §4 + example manifest | Manifest writer (R2) |

### Outputs

| Output | Location | Consumer |
| --- | --- | --- |
| Frame dumps (I3) | `frames/<session_id>/`, outside Git | Phase 2, Phase 4 |
| `fake_pose`, `fake_perception` stand-ins (R6) | `rover_bringup/scripts/` | Phase 2, Phase 3 itself, algorithm team (early) |
| Reference sessions (a)–(e) as SVO + bag + manifest (I4) | shared index of paths and checksums | Phases 1, 2, 4 |
| `record_session.sh`, replay instructions | `rover_bringup/scripts/` | everyone |
| `rover.launch.py` (live / SVO / bag; YOLO on/off) | `rover_bringup/launch/` | demo, algorithm team |
| RViz config | `rover_bringup/rviz/rover.rviz` | everyone |
| Contract v1.0, handoff bags, `HANDOFF_README` | `docs2/`, shared storage | algorithm team |

**Tasks:** R1–R6 first (data and stand-ins), then P9, H1, H2, H3, H5, H6. H4 is shared with Phase 2.

**Checkpoints:** C0 Oct 12: frame dumps of (a) and (b) and both stand-ins exist. G1 Oct 16: ROS bags of (a)–(e) recorded and replayable. G2 Oct 23: `rover.launch.py` runs Phases 1 + 2 from a bag.

**Deliverables (G3, Oct 30):** one launch command, under 60 s cold start; 10-minute soak passes; contract v1.0 frozen; the algorithm team replays the handoff bags on their own machine; live demo.

---

## Phase 4: Mapping (after G3, from Nov 2; end date to be set)

**Goal.** Build a **persistent** labelled map of a whole area (free / wall / obstacle / unknown) in the `map` frame, save it, and reload it in a later session so the same building lines up.

Phase 4 starts after G3 so that it does not take people away from the Oct 30 deliverable. All of its inputs exist at G3, and its `core/` can be developed on frame dumps and handoff bags without the rover.

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
| A (default) | Our `rover_mapping` node merges each `class_grid` snapshot into a fixed `map`-frame grid using `map → odom`; ZED area memory keeps `map` consistent between sessions | Yes |
| B | `slam_toolbox` builds the map from `/rover/perception/scan` | No: `slam_toolbox` would publish `map → odom`, so the ZED map TF must be turned off and D4 revised |
| C | ZED SDK spatial mapping (fused 3D mesh / cloud), projected to 2D | Yes, but labels must be recomputed from the 3D map |

### Outputs (I8, draft; final in contract §9)

| Output | Type / location | Meaning |
| --- | --- | --- |
| `/rover/map/grid` | `OccupancyGrid`, `map`, latched (transient local) | Persistent free / occupied / unknown |
| `/rover/map/class_grid` | `OccupancyGrid`, `map`, latched | Same label codes as contract §3 |
| `maps/<map_id>/` | `map.yaml` + `map.pgm` (Nav2 `map_server` format), `class.pgm`, `area_map.area`, `map_manifest.json` | Saved map, reloadable with `rover.launch.py map:=<map_id>`; stored outside Git |

**Tasks:** M1–M6 in [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md).

**Deliverables (G4):** a map of the hallway + cluttered-room route saved, reloaded in a new session, and lining up with the live local grid within a stated tolerance; walls and obstacles keep their labels; relocalization jumps do not smear the map.
