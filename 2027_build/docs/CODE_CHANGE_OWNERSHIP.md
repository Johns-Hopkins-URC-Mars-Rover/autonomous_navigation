# Code Change Ownership and Merge Boundaries

This plan keeps three branches productive before hardware, ROS 2, or one another's work is ready.

## Read this before changing code

The goal is independent progress without incompatible assumptions. Each person owns a different answer:

- Hedgie: “What can we learn from recorded RGB-D data to make the trajectory/map better?”
- Wobbles: “Can we trust, replay, and correctly frame the live camera/IMU/GPS data?”
- Bedrawn: “Can Nav2 consume safe map/obstacle/localization outputs in replay or simulation?”

The root-level Python files are the existing prototype. New ROS 2 Jazzy code belongs in `2027_build/`; do not move or rewrite the prototype merely to make the folders look uniform.

| Area                                                                | Owner                     | Branch                          | Merge dependency                         |
| ------------------------------------------------------------------- | ------------------------- | ------------------------------- | ---------------------------------------- |
| Offline visual SLAM, loop closure, semantic/dense maps, metrics     | Hedgie                    | `hedgie-slam-research`        | None; uses session fixture or recordings |
| ZED wrapper, TF/URDF, recording, IMU/GPS, localization logs         | Wobbles                   | `wobbles-sensor-localization` | None; live data or SVO only              |
| Depth/scan adapters, SLAM Toolbox, Nav2 costmaps, replay/simulation | Bedrawn                   | `bedrawn-nav-integration`     | None; synthetic source first             |
| Legacy standalone ZED pipeline                                      | Shared, narrow edits only | `main` via reviewed PR        | No ROS rewrite                           |

## Boundary rules

1. Do not edit another person's package without agreement.
2. Use standard ROS 2 message types at package boundaries whenever possible.
3. Keep the legacy root-level Python prototype runnable; do not move it into the 2027 workspace as part of unrelated work.
4. Add one new package/configuration concern per pull request.
5. Do not merge branch scaffolding solely because it exists. Merge a vertical slice with a documented acceptance check.
6. Keep generated SVO, rosbag2, maps, models, and experiment outputs out of Git unless intentionally managed through an approved artifact store or Git LFS.

## Interface contracts to stabilize first

Wobbles will stabilize the live/replay sensor contract. Bedrawn may develop against synthetic data until then. Hedgie reads file-based sessions and therefore remains independent.

| Contract                | Producer  | Consumers       | Minimum fields                                             |
| ----------------------- | --------- | --------------- | ---------------------------------------------------------- |
| Session manifest        | Wobbles   | Hedgie, Bedrawn | calibration, frames, timestamps, checksums, route metadata |
| Offline map export      | Hedgie    | Bedrawn         | frame, resolution, occupancy/confidence, provenance        |
| Sensor topics/TF        | Wobbles   | Bedrawn         | standard message type, topic, frame id, rate, QoS          |
| Obstacle representation | All later | Nav2            | source frame, timestamp, confidence, clearing semantics    |

## Existing-code edit sequencing

1. Wobbles adds structured standalone exports only after agreeing on the manifest schema.
2. Hedgie factors camera-independent detection helpers only when tests prove `object_detection.py` behavior is preserved.
3. Bedrawn does not couple Nav2 to the root-level Python loop; it uses ROS messages and launch/config overlays.
4. Any common `2027_build` skeleton change should be a small reviewed PR from `main`, then rebased/cherry-picked by the three branches.

## Reference docs before cross-workstream changes

- Read `FOUNDATIONS.md` before changing a frame, map, trajectory, area-map, or navigation claim; it defines the shared vocabulary and limits.
- Read `README.md` before adding a ROS package, because it states the target workspace layout, build order, and TF ownership rule.
- For a live-data change, defer to `WOBBLES_SENSOR_LOCALIZATION.md` and the official ZED ROS 2 topic/robot-integration references it links.
- For an offline SLAM/map export change, defer to `HEDGIE_SLAM_RESEARCH.md` and its calibration/trajectory-format references.
- For a Nav2 map/costmap change, defer to `BEDRAWN_NAVIGATION.md` and its Nav2 costmap/SLAM Toolbox references.
