# docs2: ZED Sensor Fusion and Scene Perception (October 2026 milestone)

This folder is the working plan for the next 3.5 weeks. It replaces the broader plans in `2027_build/docs/` **for this milestone only**; those remain the longer-term reference.

## Goal in one sentence

By **Friday, October 30, 2026**, the rover computer runs one launch command that fuses the ZED camera and its IMU into a stable pose, turns depth into a labelled local map of **free space, walls, obstacles, and unknown**, and publishes all of it as documented ROS 2 topics that the algorithm (planning/control) team can consume live or from a recorded bag.

## Read in this order

| File | What it answers |
| --- | --- |
| [README.md](README.md) (this file) | What we are building, what we are not, and the key decisions |
| [PHASES.md](PHASES.md) | Each phase's deliverables, inputs, outputs, stand-ins, and which existing code feeds it, so Phases 1–3 can be built at the same time |
| [TIMELINE.md](TIMELINE.md) | Schedule, gates (Phases 1–3 in parallel, mapping as Phase 4), and the critical path |
| [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md) | Every task, its output, its "done when" check, and its dependencies |
| [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) | Exactly what the algorithm team receives: topics, frames, labels, failure behaviour |
| [SETUP_UBUNTU_22_04.md](SETUP_UBUNTU_22_04.md) | The software stack to install and pin, and how to check it works |

Who does which task is deliberately left open. Each task in the work breakdown is sized so it can be assigned later.

## What "semi-functional autonav" means for us

Our side of autonomous navigation is **perception and state estimation**. At the end of the month the algorithm team should be able to subscribe to:

1. **Where am I?** A smooth, IMU-fused odometry stream and a correct TF tree (`odom → base_link → camera → imu`).
2. **What is around me?** A rolling local grid around the rover: free / occupied / unknown, plus a class layer (free / wall / obstacle / unknown) with confidence.
3. **What are the nearby things?** A 2D `LaserScan` from depth (the input most planners already accept), and 3D object detections from our YOLO model.
4. **Can I trust it right now?** A health signal that says when tracking is lost, depth is poor, or data is stale.

With those four, the algorithm team can run a local costmap and a simple planner or reactive controller. Building those is their job, not ours.

## How the pieces fit

```text
ZED camera (stereo + IMU)
  │
  ▼
zed_wrapper (ZED SDK, ROS 2 Humble)      ← camera + IMU fusion happens here (visual-inertial odometry)
  ├── RGB image, depth image, camera_info
  ├── IMU (full rate)
  └── odometry + TF  odom → base_link    (map → odom from ZED area memory)
  │
  ▼
rover_perception (our new package)
  ├── ground removal using the IMU gravity direction
  ├── local grid: free / occupied / unknown
  ├── class layer: wall / obstacle / free / unknown + confidence
  ├── LaserScan from the obstacle points
  ├── 3D objects: YOLO boxes + depth
  └── health: tracking, depth quality, latency
  │
  ▼
Handoff to the algorithm team: live topics, recorded bags, OUTPUT_CONTRACT.md   (Oct 30)
  │
  ▼
rover_mapping (Phase 4, after Oct 30)
  └── persistent labelled map in `map`, saved and reloaded with the ZED area map
```

Phase mapping: wrapper configuration and TF are **Phase 1**, `rover_perception` is **Phase 2**, recording, launch and handoff are **Phase 3**, and `rover_mapping` is **Phase 4**. Phases 1–3 run at the same time; see [PHASES.md](PHASES.md).

## Key decisions (and why)

| # | Decision | Why |
| --- | --- | --- |
| D1 | **Ubuntu 22.04 + ROS 2 Humble** first. | Requested. Humble is the ROS 2 release for 22.04 and is supported by the ZED ROS 2 wrapper and by NVIDIA JetPack 6 (Jetson). Moving to 24.04 / Jazzy later is mostly a rebuild, not a redesign. |
| D2 | **The ZED SDK does the camera + IMU fusion.** We configure, verify, and measure it; we do not write our own SLAM or filter this month. | The SDK's positional tracking already fuses stereo vision with the IMU. Re-implementing it is algorithm research and would not be ready by October 30. |
| D3 | **No extra `robot_localization` filter** unless wheel odometry or a second IMU becomes available. | With one camera and its own IMU, a second filter adds a duplicate pose source and no new information. |
| D4 | **The ZED wrapper owns both `map → odom` and `odom → base_link`.** | One owner per TF edge. The local grid lives in `odom`, which never jumps. |
| D5 | **Perception works on a subsampled depth image, not the full point cloud.** | Uses roughly 50k points instead of about 900k per frame, so a Python node can keep up; it also reuses the logic of the existing depth heuristics in `slam/zed_scene_core.py`. |
| D6 | **Labels come from geometry first, YOLO second.** Walls and obstacles are classified from 3D shape. YOLO adds an object class when a detection overlaps. | Geometry works on anything, including objects YOLO was not trained on. YOLO alone can miss things. |
| D7 | **"No data" never means "free".** Cells are free only when depth actually saw the floor or saw past them. | Prevents drop-offs, glass, and dark areas from looking drivable. |
| D8 | **The legacy `main.py` stays untouched and remains the fallback recorder.** | If ROS bring-up slips, we can still record SVO files and replay them through the wrapper later. |

## Explicitly out of scope this month

- Custom visual SLAM, feature matching, loop closure, pose graphs, learned features (the old research VSLAM track).
- Costmaps, path planning, controllers, behaviour trees, goal selection, motor commands.
- GPS / outdoor global localization.
- Wheel odometry fusion (unless the hardware already exists; see D3).
- Drop-off, stair, and glass detection beyond "mark as unknown" (see D7).
- A persistent, saved map before October 30. It is **Phase 4**, which starts after the handoff (see [PHASES.md](PHASES.md)). Merging maps from several sessions into one stays out of scope.
- Moving the legacy prototype into ROS packages.
- Migrating to Ubuntu 24.04 / ROS 2 Jazzy.

## Stretch goals (only after the October 30 gate passes)

- Temporal filtering that marks moving objects (people) as dynamic instead of permanent.
- Multi-layer `grid_map` output if the algorithm team asks for it.
- Jazzy / 24.04 port.

## How this relates to the older docs

- `2027_build/docs/` targets Ubuntu 24.04 / Jazzy and includes a long research VSLAM track. For October we deliberately narrow to working sensor fusion and scene labels on 22.04 / Humble.
- `docs/SENSOR_DATA_CONTRACT.md` is still the reference for units, axes, timestamps, and the session-folder format. [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) builds on it and adds the perception outputs it lacked.
- `DOCS.md` describes the legacy prototype, whose wall, hallway, and cluster heuristics are the starting point for task P5 in the work breakdown.

Items marked **[verify]** in these docs depend on the exact ZED wrapper release or the rover hardware and must be confirmed on the real setup, not assumed.
