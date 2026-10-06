# 2027 Autonomous Navigation Build

This folder is the planning contract for the Ubuntu 24.04 / ROS 2 Jazzy build. The existing top-level Python pipeline remains a standalone ZED prototype and is not the ROS 2 navigation stack.

## Baseline

`main.py` already opens the ZED, retrieves RGB and depth, runs ZED positional tracking with IMU fusion, records SVO, writes a TUM trajectory, persists a ZED area map, and runs YOLO plus depth heuristics. It does **not** yet publish ROS 2 messages, create Nav2 maps/costmaps, or provide GPS localization.

The target runtime is Ubuntu 24.04 with ROS 2 Jazzy. Ubuntu 20.04/Foxy is not a target. Hardware compatibility, NVIDIA driver/CUDA, the ZED SDK, and the current ZED ROS 2 wrapper must be verified together before live deployment.

## Local branch baseline

All branches start from `main` after the documentation commit.

| Person  | Branch                          | Primary package area                       | May proceed independently with                    |
| ------- | ------------------------------- | ------------------------------------------ | ------------------------------------------------- |
| Hedgie  | `hedgie-slam-research`        | offline visual SLAM and semantic mapping   | recorded SVO/extracted session folders            |
| Wobbles | `wobbles-sensor-localization` | ZED/IMU/GPS and localization data contract | live camera or an SVO; no Nav2 dependency         |
| Bedrawn | `bedrawn-nav-integration`     | maps, costmaps, Nav2, simulation/replay    | synthetic ROS bags or Wobbles bags when available |

Read the person-specific plans before editing. A merge is not required for another workstream to begin.

## Shared end-state contract

```text
map -> odom -> base_link -> camera_link -> imu_link
                  |
                  +-> Nav2 local/global costmaps -> planner/controller

Recorded session -> Hedgie offline SLAM/map research
ZED / IMU / GPS -> Wobbles localization data contract
Map + obstacle representation -> Bedrawn Nav2 integration
```

Exactly one component must own each TF edge. In particular, do not let ZED positional tracking, SLAM Toolbox, AMCL, and a GPS filter simultaneously publish `map -> odom`.

## Build order

1. Camera-only: ZED RGB-D/VIO, replayable recordings, offline SLAM benchmark, depth-derived obstacle representation, Nav2 simulation/replay.
2. IMU: timestamp/axis validation, VIO comparison, local state-estimation decision.
3. GPS: GNSS quality/heading validation, a single global-localization owner, outdoor waypoint validation.

No live motor command is an acceptance criterion for this repository. First prove the stack through RViz and replay/simulation.

## 2027 workspace target

Implementation branches may add the following workspace without modifying the legacy pipeline:

```text
2027_build/
  src/
    rover_camera_ai/
    rover_localization/
    rover_navigation/
    rover_bringup/
  config/
  evaluation/
```

Package names must remain valid ROS 2 names; `2027_build` is only a directory name.

## Shared data handoff

Every recorded session should ultimately have a stable identifier and this minimum manifest:

- camera model, serial (or anonymized device id), resolution, FPS, and intrinsics;
- coordinate convention and static `base_link -> camera_link` transform;
- SVO path/checksum and matching rosbag2 path/checksum when available;
- start/end timestamps, recording software versions, and calibration version;
- pose/tracking status timeline, IMU availability, and GPS availability;
- the test route, environment, and known failure events.

The schema may be drafted independently, but Wobbles owns its final live-data implementation. Hedgie can use a synthetic or hand-authored manifest while waiting.

## References

- ZED ROS 2 wrapper: RGB/depth/point clouds, IMU, VIO, positional tracking, SVO replay, and diagnostics.
- Nav2: `slam_toolbox` is the initial 2D SLAM baseline; static, obstacle/voxel, and inflation layers are the initial costmap baseline.
- GPS is a later global-localization stage; Nav2 expects the `map -> odom -> base_link` TF chain.
