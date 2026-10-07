# Foundations: What Exists, What It Means, and What Comes Next

Read this before the person-specific plans or the detailed legacy-pipeline reference.

## The project in one sentence

The current repository is a **camera prototype**: a ZED camera looks at the world, estimates where it has moved, estimates depth, identifies some objects, and saves recordings. The 2027 build turns those useful ingredients into a ROS 2 / Nav2 system that can make and use navigation maps.

It is important not to confuse “the camera can estimate its pose” with “the rover can autonomously navigate.” The first is already partly implemented; the second requires ROS messages, a correct TF tree, obstacle representations, maps, planning, control, and validation.

## What the current pipeline does

| Existing feature | Plain meaning | Useful result | What it does **not** prove or provide |
|---|---|---|---|
| ZED positional tracking | The camera estimates its own 3D position and orientation by matching visual structure over time. | A local motion estimate and a camera path. | Guaranteed accuracy, a Nav2 map, or robot-base localization. Visual tracking can drift or be lost in poor texture, blur, darkness, or repeated-looking scenes. |
| IMU fusion | The camera combines image motion with accelerometer/gyroscope measurements. The IMU helps during short, rapid motions and constrains roll/pitch using gravity. | Usually steadier visual-inertial odometry (VIO) than images alone. | A calibrated rover-state estimator, wheel odometry, absolute heading, or GPS-quality global position. |
| SVO recording | An SVO is a ZED recording that lets the ZED SDK replay a camera session later. | Repeatable debugging and offline CV/SLAM experiments without the physical camera. | A complete ROS 2 bag or a substitute for a session manifest; metadata and ROS topics may still need recording separately. |
| TUM trajectory | A text file containing timestamped position and orientation rows. It is a standard exchange format for trajectory tools. | A baseline trajectory that can be plotted, compared, and fed to offline research tools. | Ground truth. It can measure against another trajectory only after frame/time alignment and a defensible reference are available. |
| ZED area map | ZED stores visual landmarks so its own positional tracker can recognize a previously explored area and reduce drift/relocalize. | Re-entering a known site in a consistent ZED world frame. | A Nav2 `OccupancyGrid`, a saved 2D map for a planner, an obstacle costmap, or a map other software automatically understands. |
| YOLO + depth heuristics | YOLO labels image regions; depth supplies an approximate distance. Separate depth rules flag walls, hallways, central obstacles, and clusters. | Useful perception overlays and candidate semantic/geometric observations. | A safety-certified obstacle policy. A detection can be wrong, depth can be missing/occluded, and the current code does not publish a Nav2 obstacle source. |

## The important distinction: odometry, localization, mapping, navigation

Think of the rover as answering four increasingly difficult questions:

1. **Odometry — “How did I move since a moment ago?”**
   Camera tracking/VIO estimates incremental motion. It is smooth and high-rate, but small errors accumulate as drift.
2. **Localization — “Where am I in a known world?”**
   Loop closure, a saved ZED area map, AMCL, GPS, or another global reference corrects drift and places the rover in a shared frame.
3. **Mapping — “What is around me?”**
   A map describes free/occupied/unknown space. For Nav2 this is commonly a 2D occupancy grid, while richer research maps may be 3D point clouds or semantic maps.
4. **Navigation — “How do I safely reach that goal?”**
   Nav2 combines a map, current pose, robot footprint, live obstacles, a planner, a controller, and recovery/safety behavior. It does not itself create VSLAM.

The root-level prototype reaches part of question 1 and gathers inputs for questions 2–3. The 2027 build is responsible for questions 2–4.

## Why build `2027_build/` at the repository root?

**Yes.** `2027_build/` should be a new top-level directory in this repository, beside `main.py`, `slam/`, and `docs/`.

```text
autonomous_navigation/
├── main.py, slam/, object_detection.py     # legacy standalone ZED prototype
├── docs/                                   # plans and explanations
└── 2027_build/                             # new ROS 2 Jazzy workspace
    ├── src/                                # ROS packages
    ├── config/                             # checked-in YAML/URDF/RViz settings
    └── evaluation/                         # scripts and small fixtures
```

Why this is better than rewriting the root code now:

- the current prototype keeps working as a camera/SVO baseline;
- the ROS 2 workspace can follow normal `colcon` structure;
- each branch can add its own package without colliding with legacy code;
- `build/`, `install/`, `log/`, rosbag2 recordings, generated maps, and large experiment outputs stay untracked.

`2027_build` is a folder name, not a ROS package name. Its packages use valid names such as `rover_camera_ai`.

## The one TF picture everyone must understand

```text
map -> odom -> base_link -> camera_link -> imu_link
```

- `base_link`: the physical rover body.
- `camera_link` / `imu_link`: fixed physical locations of sensors on that body.
- `odom`: smooth, short-term local motion frame, usually from VIO/wheel odometry/IMU fusion.
- `map`: globally corrected frame used for a saved map or GPS/global localization.

Only one component may publish a given arrow. Two publishers for `map -> odom` make the rover appear to jump and break navigation.

## Reading path: easy to challenging

1. This file.
2. `docs/README.md` for the shared architecture and branch plan.
3. Your named plan for concrete deliverables.
4. `DOCS.md` for the detailed behavior of the existing Python prototype.
5. The source files named by your plan.
6. ROS 2/ZED/Nav2 upstream documentation only when your workstream needs it.

## Safety and evidence rule

An SVO replay, a plot, a successful import, or a YOLO box is evidence that one component ran. It is not evidence that autonomous navigation is safe. Every workstream must retain its inputs, parameters, outputs, and acceptance checks so claims can be reproduced.
