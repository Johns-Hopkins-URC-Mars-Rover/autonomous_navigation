# Autonomous Navigation: Start Here

The repository today is a **camera prototype**: a ZED camera estimates where it has moved, measures depth, identifies some objects, and saves recordings ([`DOCS.md`](../DOCS.md) describes that code). We are turning it into a ROS 2 system whose outputs a planning/control team can use.

**October 2026 goal.** By **Friday, October 30, 2026**, the rover computer runs one launch command that fuses the ZED camera and its IMU into a stable pose, turns depth into a labelled local map of **free space, walls, obstacles, and unknown**, and publishes all of it as documented ROS 2 topics that the algorithm (planning/control) team can consume live or from a recorded bag.

## Documents

| File | What it answers |
| --- | --- |
| This README | What we are building, the key decisions, and the background you need |
| [PLAN.md](PLAN.md) | Phases, gates and dates; inputs, outputs and stand-ins for each phase; risks and bottlenecks |
| [TASKS.md](TASKS.md) | Every task, its output, its "done when" check, its dependencies, and the acceptance targets |
| [CONTRACT.md](CONTRACT.md) | What we publish and record: units, frames, topics, labels, failure behaviour, session format |
| [SETUP.md](SETUP.md) | The Ubuntu 22.04 / ROS 2 Humble / ZED stack to install and pin, and how to check it |
| [TEAM.md](TEAM.md) | The subteam boundary, who owns what, sync meetings, what waits on whom, and agent prompts |
| [people/WOBBLES.md](people/WOBBLES.md) | Data synthesis and sensor evidence (Wobbles) |
| [people/HEDGIE.md](people/HEDGIE.md) | VSLAM and map research (Hedgie) |
| [people/BEDRAWN.md](people/BEDRAWN.md) | Integration and handoff (Bedrawn) |
| [`../DOCS.md`](../DOCS.md) | Detailed reference for the legacy Python prototype |

Shared data files are in [`contract/`](contract/) (example session manifest, placeholder rover geometry). Diagrams and their generator scripts are in [`diagrams/`](diagrams/).

New to the project? Read this file, then [TEAM.md](TEAM.md), then your own plan in `people/`. Read [PLAN.md](PLAN.md) and [CONTRACT.md](CONTRACT.md) before writing code that crosses a phase boundary.

Items marked **[verify]** depend on the exact ZED wrapper release or the rover hardware and must be confirmed on the real setup, not assumed.

---

## What exists today

It is important not to confuse "the camera can estimate its pose" with "the rover can autonomously navigate." The first is already partly implemented; the second needs ROS messages, a correct TF tree, obstacle representations, maps, planning, control, and validation.

| Existing feature | Plain meaning | Useful result | What it does **not** prove or provide |
| --- | --- | --- | --- |
| ZED positional tracking | The camera estimates its own 3D position and orientation by matching visual structure over time. | A local motion estimate and a camera path. | Guaranteed accuracy, a Nav2 map, or robot-base localization. Tracking can drift or be lost with poor texture, blur, darkness, or repetitive scenes. |
| IMU fusion | The camera combines image motion with accelerometer/gyroscope data. The IMU helps during short, fast motions and constrains roll/pitch using gravity. | Usually steadier visual-inertial odometry (VIO) than images alone. | A calibrated rover-state estimator, wheel odometry, absolute heading, or GPS-quality global position. |
| SVO recording | A ZED recording that the ZED SDK can replay later. | Repeatable debugging and offline experiments without the camera. | A ROS 2 bag or a session manifest; those are recorded separately. |
| TUM trajectory | A text file of timestamped positions and orientations, a standard format for trajectory tools. | A baseline trajectory to plot, compare, and feed to offline tools. | Ground truth. |
| ZED area map | Visual landmarks the ZED tracker uses to recognize an area it has seen before and reduce drift. | Re-entering a known site in a consistent ZED world frame. | A Nav2 `OccupancyGrid`, a 2D map for a planner, or an obstacle costmap. |
| YOLO + depth heuristics | YOLO labels image regions; depth gives an approximate distance. Separate depth rules flag walls, hallways, and clusters. | Perception overlays and candidate observations. | A safe obstacle policy. Detections can be wrong and depth can be missing. Nothing is published to ROS. |

### Odometry, localization, mapping, navigation

1. **Odometry: "How did I move since a moment ago?"** Camera tracking/VIO estimates incremental motion. It is smooth and high-rate, but small errors accumulate as drift.
2. **Localization: "Where am I in a known world?"** Loop closure, a saved ZED area map, AMCL, or GPS corrects drift and places the rover in a shared frame.
3. **Mapping: "What is around me?"** A map describes free/occupied/unknown space, commonly a 2D occupancy grid.
4. **Navigation: "How do I safely reach that goal?"** A planner and controller combine a map, the pose, the robot footprint, and live obstacles. **That is the algorithm team's job, not ours.**

## What we deliver in October

Our side of autonomous navigation is **perception and state estimation**. At the end of the month the algorithm team can subscribe to:

1. **Where am I?** A smooth, IMU-fused odometry stream and a correct TF tree.
2. **What is around me?** A rolling local grid around the rover: free / occupied / unknown, plus a class layer (free / wall / obstacle / unknown) with confidence.
3. **What are the nearby things?** A 2D `LaserScan` from depth (the input most planners already accept), and 3D object detections from our YOLO model.
4. **Can I trust it right now?** A health signal that says when tracking is lost, depth is poor, or data is stale.

With those four, the algorithm team can run a local costmap and a simple planner or reactive controller.

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
Handoff to the algorithm team: live topics, recorded bags, CONTRACT.md   (Oct 30)
  │
  ▼
rover_mapping (Phase 4, after Oct 30)
  └── persistent labelled map in `map`, saved and reloaded with the ZED area map
```

Wrapper configuration and TF are **Phase 1**, `rover_perception` is **Phase 2**, recording, launch and handoff are **Phase 3**, and `rover_mapping` is **Phase 4**. Phases 1–3 run at the same time; see [PLAN.md](PLAN.md).

### The TF chain everyone must understand

```text
map → odom → base_link → camera → imu
```

- `base_link`: the physical rover body, at floor level under its turning centre.
- camera / IMU frames: fixed physical locations of the sensors on that body.
- `odom`: smooth, short-term motion frame. Never jumps, drifts slowly. Local control and the local grid live here.
- `map`: drift-corrected frame for a saved map or global localization. Can jump on relocalization.

**Only one component may publish a given arrow.** Two publishers for `map → odom` make the rover appear to jump and break navigation. Exact frame names and owners are in [CONTRACT.md](CONTRACT.md) §2.

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

### Out of scope this month

- Custom visual SLAM, feature matching, loop closure, pose graphs, learned features (Hedgie's research track; see [people/HEDGIE.md](people/HEDGIE.md)).
- Costmaps, path planning, controllers, behaviour trees, goal selection, motor commands.
- GPS / outdoor global localization.
- Wheel odometry fusion (unless the hardware already exists; see D3).
- Drop-off, stair, and glass detection beyond "mark as unknown" (see D7).
- A persistent, saved map before October 30. It is **Phase 4**, which starts after the handoff. Merging maps from several sessions into one stays out of scope.
- Moving the legacy prototype into ROS packages.
- Migrating to Ubuntu 24.04 / ROS 2 Jazzy.

**Stretch goals** (only after the October 30 gate passes): temporal filtering that marks moving objects (people) as dynamic; multi-layer `grid_map` output if the algorithm team asks for it; the Jazzy / 24.04 port.

### After October 30: the long-term plan

The long-term target is Ubuntu 24.04 / ROS 2 Jazzy, with dates set at the Oct 30 review: Phase 4 mapping, Hedgie's research VSLAM, conversion of the proven pieces into final ROS 2 packages, and GPS last. The per-person plans mark this work **not this month**.

## Where code goes

```text
autonomous_navigation/
├── main.py, slam/, object_detection.py   # legacy standalone ZED prototype (read-only, D8)
├── docs/                                 # these documents
└── 2027_build/                           # ROS 2 workspace
    ├── src/
    │   ├── rover_description/            # URDF/xacro: rover body + ZED mount        (Phase 1)
    │   ├── rover_bringup/                # launch, ZED overrides, record/replay, stand-ins, RViz
    │   ├── rover_perception/             # core/ (plain Python + numpy) and nodes/   (Phase 2)
    │   └── rover_mapping/                # persistent map                            (Phase 4)
    ├── config/                           # checked-in YAML/URDF/RViz settings
    └── evaluation/                       # scripts and small fixtures
```

The per-person plans also name research packages for later work (`rover_camera_ai`, `rover_localization`, `rover_navigation_inputs`). `2027_build` is a folder name, not a ROS package name. The generated `build/`, `install/` and `log/` folders, rosbag2 recordings, SVOs, maps and large experiment outputs stay out of Git.

## Safety and evidence rule

An SVO replay, a plot, a successful import, or a YOLO box is evidence that one component ran. It is not evidence that autonomous navigation is safe. Every result (fusion report, perception check, map) records the session id, the software versions, and the parameters it used, so anyone can reproduce it from the session folder alone.

---

## Background: how each stage works

### Stereo depth

The ZED has two cameras a fixed distance apart (the baseline *B*). A point appears shifted between the left and right images by a *disparity* *d*. With focal length *f* in pixels, depth is **Z = f·B / d**. Depth error grows roughly with **Z²**: a one-pixel disparity error matters far more at 8 m than at 1 m. That is why we limit to 0.3–8 m (P2). Textureless, dark, or reflective surfaces give no reliable match, so those pixels come back as `NaN`/`±inf`. That is the reason for decision D7.

### Visual-inertial odometry

The ZED SDK's internals are proprietary, but VIO generally works like this. Visual features are tracked across frames to estimate camera motion. IMU readings (≥ 100 Hz) are integrated between frames. The two are fused in a filter or optimiser. The two sensors fail in complementary ways:

- **Camera:** accurate over time, but fails with fast motion, blur, blank walls and darkness.
- **IMU:** high rate and works in the dark, but drifts quickly because integrating noisy acceleration twice compounds error.
- **Fused:** the IMU bridges short visual dropouts and fast turns, and gives the gravity direction (roll/pitch). The camera corrects the IMU's drift and bias.

Our tasks check that the inputs to this fusion are sound: gravity magnitude, gyro bias and axis signs (F3), one shared clock (F4), and fusion on vs off (F5). Evaluation uses `evo`: **ATE** (absolute trajectory error) for overall drift and closed-loop end error, **RPE** (relative pose error) for local smoothness.

### `odom` vs `map` (REP 105)

`odom` is continuous but drifts slowly. `map` is drift-corrected but can jump. The ZED's **area memory** stores visual landmarks and, when it recognises a place, corrects `map → odom`. That is the loop-closure part of SLAM, provided by the SDK.

### Depth → 3D points (P2)

The pinhole camera model in reverse. A pixel (u, v) with depth Z becomes **X = (u − cx)·Z / fx, Y = (v − cy)·Z / fy**, then is transformed into `odom` with the pose from TF. Subsampling every 4th pixel cuts ~900k points to ~50k (D5) while keeping enough density for 5 cm cells.

### Ground removal (P3)

**RANSAC** repeatedly picks 3 random points, fits a plane, and counts how many other points lie close to it. The plane with the most inliers wins, so outliers (boxes, walls) cannot drag the fit. The IMU's gravity vector constrains the search to planes within ~10° of horizontal, so a large wall is never mistaken for the floor. Points in a height band above the plane become obstacles.

### Occupancy grid (P4)

Each cell holds a probability of being occupied, stored as **log-odds** *l = log(p / (1 − p))*, so Bayesian updates become addition. For each depth return, a ray is traced from the camera to the hit. Cells along the ray get a "free" increment and the hit cell an "occupied" increment. Slow decay lets the grid forget objects that moved. Cells never crossed by a ray stay **unknown**, which enforces D7 in the data structure. The grid is *rolling*: it recentres on the rover and discards what falls off the edge.

### Wall vs obstacle (P5)

Occupied cells are grouped into straight segments (RANSAC line fitting, Hough transform, or split-and-merge; the method is open). A segment ≥ 1.0 m long whose points span ≥ 0.5 m in height is a wall; everything else occupied is an obstacle. Confidence rises with observations and falls with age.

### LaserScan (P6) and objects (P7)

Obstacle points are binned by bearing around `base_link`, keeping the nearest range per bin. **YOLO** is a single-pass neural network that predicts boxes and class scores for the whole image at once. Each box gets the **median** depth of its central region, which resists stray background pixels; back-projecting the centre gives a 3D position.

### Health (P8)

A rule-based watchdog, not an estimator. `status/ok` is true only if tracking is OK, enough depth is valid, and inputs are fresh (< 0.5 s). It lets downstream code tell "nothing is there" from "we cannot currently see".

### Persistent mapping (Phase 4)

The hard problem in every option (see [PLAN.md](PLAN.md) Phase 4) is **M3**: when relocalization corrects the pose, cells fused under the old pose are in the wrong place. Keeping snapshots tied to their poses, so they can be re-placed, avoids doubled walls.

## Reference docs

- [ZED SDK positional tracking](https://www.stereolabs.com/docs/positional-tracking/): camera pose, tracking loss, area maps, loop closure, and local odometry vs corrected pose.
- [ZED SDK spatial mapping](https://www.stereolabs.com/docs/spatial-mapping/): ZED fused 3D maps, and why they differ from a 2D occupancy map.
- [ZED ROS 2 overview](https://docs.stereolabs.com/docs/integrations/ros-2): the supported Ubuntu/ROS path, wrapper packages, SVO replay, and the RGB/depth/point-cloud/IMU/VIO outputs.
- [Nav2 first-time robot setup](https://docs.nav2.org/rolling/configuration_and_development/first_time_robot_setup_guide/): the transforms, odometry, sensors and footprint the algorithm team will expect from us.
- [Nav2 mapping and localization](https://docs.nav2.org/rolling/configuration_and_development/first_time_robot_setup_guide/sensors/mapping_localization/): how `slam_toolbox`, occupancy maps, obstacle layers and inflation relate.
- [Nav2 GPS localization](https://docs.nav2.org/rolling/tutorials/general_tutorials/navigation2_with_gps/navigation2_with_gps/): only for the later GPS stage.
