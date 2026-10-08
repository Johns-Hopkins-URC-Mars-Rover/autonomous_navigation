# Work Breakdown

Every task the October 30 milestone needs, grouped into five tracks. Owners are not assigned yet. Each task lists what it produces, how we know it is done, and what it waits on. Dates are in [TIMELINE.md](TIMELINE.md).

| Track | Purpose |
| --- | --- |
| **S** Setup | A pinned, working Ubuntu 22.04 / ROS 2 Humble / ZED stack on the rover computer |
| **F** Fusion | Camera + IMU pose that is correct, measured, and understood when it fails |
| **R** Recording | Repeatable sessions that every other track can test against without hardware |
| **P** Perception | Depth + IMU → free / wall / obstacle / unknown, scan, and 3D objects |
| **H** Handoff | One launch command, a frozen contract, test coverage, and the demo |

Code lives in the ROS 2 workspace at `2027_build/` (as in the older plan), in three new packages:

```text
2027_build/src/
  rover_description/   # URDF/xacro: rover body + ZED mount
  rover_bringup/       # launch files, ZED parameter overrides, record/replay scripts, RViz config
  rover_perception/    # core/ (plain Python + numpy, no ROS) and nodes/ (thin ROS wrappers)
```

Keep perception logic in `core/` with no ROS imports so it can be unit-tested on saved depth arrays and run on legacy SVO files before ROS is ready.

---

## S: Setup

| ID | Task | Output | Done when | Needs |
| --- | --- | --- | --- | --- |
| S1 | Pick and prepare the rover computer: Jetson on JetPack 6 (Ubuntu 22.04) or an x86 Ubuntu 22.04 machine with an NVIDIA GPU. A second 22.04 laptop for RViz is useful. | Hardware/OS record in [SETUP_UBUNTU_22_04.md](SETUP_UBUNTU_22_04.md) | `lsb_release -a` says 22.04; GPU visible (`nvidia-smi` or `tegrastats`) | — |
| S2 | Install ROS 2 Humble. | Working `ros2` CLI | Demo talker/listener works; `ros2 doctor` has no errors | S1 |
| S3 | Install the ZED SDK that matches the CUDA / JetPack version, plus its Python API. | SDK installed | ZED Diagnostic passes with the camera; legacy `main.py --no-display` runs on this machine | S1 |
| S4 | Build `zed-ros2-wrapper` at a **pinned release tag** that matches the SDK major version. | Wrapper built in the workspace | `ros2 launch zed_wrapper zed_camera.launch.py camera_model:=<model>` shows RGB, depth, and IMU in RViz | S2, S3 |
| S5 | Create the three packages above with build files, empty launch, and a passing `colcon build` / `colcon test`. | Package skeletons | Clean build and test run on the rover computer | S2 |
| S6 | Record every pinned version (OS, JetPack/CUDA, SDK, wrapper tag, Python, YOLO/torch). | Version table filled in | A second person reproduces the setup from the table alone | S1–S4 |

## F: Fusion (camera + IMU pose)

The ZED SDK performs the visual-inertial fusion (README decision D2). Our job is to configure it, prove it works, and document its limits.

| ID | Task | Output | Done when | Needs |
| --- | --- | --- | --- | --- |
| F1 | Measure the camera mount: position (m) and angle of the ZED relative to the rover body. Define `base_link` at floor level under the rover's turning centre. | `rover_description` URDF that includes the ZED xacro; measured values copied into the manifest | `ros2 run tf2_tools view_frames` shows one connected tree `map → odom → base_link → zed_camera_link → … → zed_imu_link`, with no duplicate publishers | S4, S5 |
| F2 | Write the ZED parameter override file: positional tracking on, IMU fusion on, `base_frame: base_link`, TF and map TF published by the wrapper, depth mode, resolution, frame rate, sensor publish rate. **[verify]** exact parameter names on the pinned wrapper. | `rover_bringup/config/zed_overrides.yaml` | `ros2 param dump` on the running node matches the file | S4 |
| F3 | Validate the IMU: rate and jitter, monotonic timestamps, frame id, 5-minute static test (gravity magnitude, gyro bias), axis test (tilt nose-down, roll left, yaw left and check signs against REP 103). | `scripts/imu_check.py` and an IMU report | All checks in the acceptance table below pass | F2, R1 |
| F4 | Check timing: IMU and image stamps use the same clock; measure capture-to-publish latency for depth and odometry. | Timing section of the fusion report | Latency measured and within target; no stamp goes backwards in a 10-minute run | F2 |
| F5 | Measure odometry quality with IMU fusion **on vs off** on the same recordings (replay one SVO twice). Tests: static drift, closed loop back to a floor mark, fast turns and shaking. | Fusion report with numbers and trajectory plots (`evo` on TUM exports) | Fusion-on meets the targets below and is no worse than fusion-off on every test | F1–F3, R4 |
| F6 | Characterise failures: cover the lens for 2 s, blank wall, dark room, fast spin. Record what `/odom`, TF, and tracking status do during loss and after recovery (freeze, IMU-only, or jump). | Failure table in [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) | Each failure case has observed behaviour and a recovery-jump size | F5 |
| F7 | Decide area-memory use for the demo (on or off) and document how `map → odom` behaves when the ZED relocalizes. | Decision recorded in the contract | Algorithm team acknowledges: control uses `odom`, not `map` | F5 |

## R: Recording and replay

| ID | Task | Output | Done when | Needs |
| --- | --- | --- | --- | --- |
| R1 | Recording script: rosbag2 in MCAP format with a fixed topic list, plus an SVO recording of the same run. | `rover_bringup/scripts/record_session.sh` | One command records both; the bag info shows every listed topic | S4 |
| R2 | Session manifest writer following `docs/SENSOR_DATA_CONTRACT.md` §4, with the bag folder added. | `scripts/write_manifest.py` | Manifest validates against the example; checksums match | R1 |
| R3 | Replay path: `ros2 bag play --clock` with `use_sim_time:=true`, and SVO replay through the wrapper. | Replay instructions and a launch argument | Perception produces the same output topics from replay as live | R1, P1 |
| R4 | Reference sessions (about 2–5 minutes each): (a) static, (b) hallway loop back to a floor mark, (c) cluttered room with boxes and chairs, (d) fast turns and shaking, (e) deliberate lens cover. | Sessions stored outside Git; paths and checksums listed in a shared index | Every F and P test can run from these without the rover | R1, R2 |

Early option: before ROS is ready, record sessions (a)–(e) as SVO files with the legacy `main.py --save-svo`. Perception `core/` work can start on those immediately.

## P: Perception (depth + IMU → labelled scene)

| ID | Task | Output | Done when | Needs |
| --- | --- | --- | --- | --- |
| P1 | Node skeleton: subscribe to depth, depth `camera_info`, and TF; parameters in YAML; launch file. | `rover_perception` node running | Receives synchronised frames at the camera rate in live and replay | S5, S4 |
| P2 | Depth → 3D points: subsample (start with every 4th pixel), keep 0.3–8 m (legacy `SceneConfig` range), drop `NaN`/`±inf` per the contract, transform into `odom`. | `core/points.py` + tests | Synthetic depth of a flat floor lands on z ≈ floor height within 2 cm | P1, F1 |
| P3 | Ground removal using the gravity direction: in `odom` (z up, levelled by the IMU), fit the floor plane with RANSAC, constrained to within about 10° of horizontal. Split points into ground and obstacle (height band from 5 cm above floor to rover height + 10 cm, both parameters). | `core/ground.py` + tests | Floor points < 2% labelled obstacle on session (a); a 10 cm box is labelled obstacle | P2 |
| P4 | Rolling local grid in `odom`: start with 10 m × 10 m, 5 cm cells, centred on the rover. Cells start unknown; ray-cast free space from the camera to each ground or obstacle hit; mark obstacle hits occupied; log-odds update with slow decay. | `core/grid.py`; topic `/rover/perception/grid` | Unit tests pass; on session (b) the corridor shows free floor, occupied walls, unknown behind walls | P3 |
| P5 | Wall vs obstacle classification: fit straight segments to occupied cells; a segment at least 1.0 m long whose points span at least 0.5 m in height is a **wall**, everything else occupied is an **obstacle** (both thresholds are parameters). Start from the ideas in `slam/zed_scene_core.py` (`detect_walls`, `detect_hallway`). Add a per-cell confidence from observation count and age. | `core/classify.py`; topics `/rover/perception/class_grid`, `/rover/perception/confidence` | Unit tests pass; on sessions (b) and (c) a reviewer agrees with wall vs obstacle labels on sampled frames | P4 |
| P6 | Obstacle points and LaserScan: publish obstacle points as `PointCloud2`; convert to `LaserScan` in `base_link` with `pointcloud_to_laserscan`. | `/rover/perception/obstacle_points`, `/rover/perception/scan` | Scan matches grid obstacles in RViz; no floor hits on session (a) | P3 |
| P7 | 3D objects: run `models/best.pt` on RGB; for each box take the median depth of its central region, convert to a 3D centre and size in `base_link`. Class names come from the model (`model.names`). | `/rover/perception/objects` (`vision_msgs/Detection3DArray`) | Object positions within 10% of tape-measured distance at 1–4 m on session (c) | P1 |
| P8 | Health signal: tracking state, fraction of valid depth, grid age, per-stage latency. | `/diagnostics` entries + `/rover/status/ok` (`std_msgs/Bool`) | Lens-cover test flips `ok` to false within 0.5 s and back after recovery | P4, F6 |
| P9 | RViz configuration showing camera, TF, grid, class grid, scan, objects, and health. | `rover_bringup/rviz/rover.rviz` | A newcomer can see every output with one launch | P4–P8 |
| P10 | Performance tuning on the rover computer: measure CPU/GPU and output rates; adjust resolution, depth mode, subsampling, YOLO rate. | Performance table in the contract | Rate and latency targets below are met with everything running | P1–P8 |

## H: Handoff and hardening

| ID | Task | Output | Done when | Needs |
| --- | --- | --- | --- | --- |
| H1 | One launch command with arguments for live / SVO / bag replay and for turning YOLO on or off. | `ros2 launch rover_bringup rover.launch.py` | Cold start to all outputs in under 60 s | F2, P1–P9 |
| H2 | Freeze [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) at v1.0: resolve all **[verify]** items, list YOLO classes, fill the failure and performance tables. | Contract v1.0 | Algorithm team reviews it and has no open questions | F6, F7, P10 |
| H3 | Handoff bag set: reference sessions (b), (c), (e) re-recorded with all output topics, plus replay instructions. | Bags + `HANDOFF_README` | The algorithm team replays them on their own machine without help | H1, H2 |
| H4 | Tests: unit tests for `core/` on synthetic depth (flat floor → free; wall at 2 m → wall line; box → obstacle; NaN patch → unknown), plus a regression run on one recorded session. | `colcon test` suite | Tests pass in a clean checkout | P2–P5 |
| H5 | Live soak test on the rover, pushed or driven manually: 10 minutes indoors. | Soak-test log and bag | No crash, no stalled topic, health signal accurate | H1 |
| H6 | Demo and walkthrough with the algorithm team; collect their requests for November. | Demo notes | Gate G3 in the timeline passes | H1–H5 |

---

## Acceptance targets

These are **proposed starting targets**. Replace them with measured values after F5 and P10 if they turn out to be unrealistic, and record why.

| Area | Check | Proposed target |
| --- | --- | --- |
| IMU | Publish rate | ≥ 100 Hz, stable (**[verify]** the camera model's maximum) |
| IMU | Static gravity magnitude | 9.81 ± 0.1 m/s² |
| IMU | Axis signs | Match REP 103 (X forward, Y left, Z up) on all three tilt tests |
| Timing | Timestamps | Never go backwards in a 10-minute run |
| Timing | Capture → `/odom` latency | < 100 ms |
| Odometry | Static drift, 5 minutes | < 5 cm position, < 1° yaw |
| Odometry | Closed loop of 30–50 m, no area map | End error < 2% of path length |
| Odometry | Fast turns and shaking | Tracking stays OK with fusion on; fusion-on no worse than fusion-off |
| Odometry | Lens covered 2 s | Reported as lost within 0.5 s; recovers; jump size recorded |
| Grid | Update rate | ≥ 5 Hz |
| Grid | Capture → grid latency | < 250 ms |
| Grid | Floor mislabelled as obstacle (session a) | < 2% of floor cells |
| Grid | Unseen areas | Always unknown, never free |
| Objects | Detection rate | ≥ 5 Hz |
| Objects | Distance error at 1–4 m | < 10% |
| System | Cold start | < 60 s to all outputs |
| System | Soak test | 10 minutes, no crash or stalled topic |

## Dependency picture

```text
S1 → S2 ─┬→ S4 → F2 → F3/F4 → F5 → F6/F7 ───────────────┐
S1 → S3 ─┘     ↘ S5 → F1 ──────↗                         │
                 R1 → R2 → R4 (feeds F5, P2–P7 testing)  ├→ H1 → H2 → H3 → H6
       P2 → P3 → P4 → P5 → P8 → P9 → P10 ───────────────┤
                      ↘ P6        P7 ───────────────────┘
                                  H4 runs alongside P2–P5; H5 after H1
```

Critical path: **S1 → S3 → S4 → F2 → F5**. Everything in P can be developed in `core/` on legacy SVO recordings while the critical path runs, and joined to ROS once P1 exists.
