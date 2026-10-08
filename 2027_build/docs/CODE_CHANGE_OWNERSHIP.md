# Code Change Ownership and Merge Boundaries

This plan keeps three branches productive before hardware, ROS 2, or one another's work is ready. After a short shared measurement preflight, the three people work in parallel; Wobbles' first substantive work is IMU integration/validation, not a prolonged camera-only implementation phase.

## Read this before changing code

The goal is independent progress without incompatible assumptions. Each person owns a different answer:

- Hedgie: “What can we learn from recorded RGB-D data to make the trajectory/map better?”
- Wobbles: “Can we trust, replay, and correctly frame the live camera/IMU/GPS data?”
- Bedrawn: “Can another team consume safe, costmap-ready map/obstacle/localization inputs in replay or simulation?”

The root-level Python files are the existing prototype. New ROS 2 Jazzy code belongs in `2027_build/`; do not move or rewrite the prototype merely to make the folders look uniform.

| Area                                                                | Owner                     | Branch                          | Merge dependency                         |
| ------------------------------------------------------------------- | ------------------------- | ------------------------------- | ---------------------------------------- |
| Offline visual SLAM, loop closure, semantic/dense maps, metrics     | Hedgie                    | `hedgie-slam-research`        | None; uses session fixture or recordings |
| ZED wrapper, TF/URDF, recording, IMU/GPS, localization logs         | Wobbles                   | `wobbles-sensor-localization` | None; live data or SVO only              |
| Depth/scan adapters, costmap-ready handoff, replay/simulation       | Bedrawn                   | `bedrawn-nav-integration`     | None; synthetic source first             |
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
| Offline map export      | Hedgie    | Bedrawn, external team | frame, resolution, occupancy/confidence, provenance  |
| Sensor topics/TF        | Wobbles   | Bedrawn, external team | standard message type, topic, frame id, rate, QoS    |
| Costmap-ready input bundle | Bedrawn | External costmap/planning team | obstacle source, TF/localization context, footprint, replay evidence |

## Timeline and integration gates

1. **Shared preflight:** record one reproducible camera/IMU session and document clocks, frame names, and fixed mounting geometry. This enables IMU work; it does not block Hedgie's fixture or Bedrawn's synthetic work.
2. **Parallel milestone:** Wobbles completes IMU health and matched VIO comparison; Hedgie completes a visual-only offline benchmark; Bedrawn completes a synthetic/replay costmap-ready input bundle.
3. **Integration gate:** jointly test the manifest, topics/TF, map/obstacle formats, replay behavior, single `map -> odom` owner, and external-consumer handoff with one session.
4. **Conversion gate:** package only those validated vertical slices. Do not migrate the legacy prototype or merge empty package skeletons merely to claim conversion progress.

## Existing-code edit sequencing

1. Wobbles adds structured standalone exports only after agreeing on the manifest schema.
2. Hedgie factors camera-independent detection helpers only when tests prove `object_detection.py` behavior is preserved.
3. Bedrawn does not couple a downstream costmap/planning stack to the root-level Python loop; it exports standard ROS messages and handoff metadata only.
4. Any common `2027_build` skeleton change should be a small reviewed PR from `main`, then rebased/cherry-picked by the three branches. Keep it minimal until the integration gate; full package conversion follows validated handoffs.

## Reference docs before cross-workstream changes

- Read `FOUNDATIONS.md` before changing a frame, map, trajectory, area-map, or navigation claim; it defines the shared vocabulary and limits.
- Read `README.md` before adding a ROS package, because it states the target workspace layout, build order, and TF ownership rule.
- For a live-data change, defer to `WOBBLES_SENSOR_LOCALIZATION.md` and the official ZED ROS 2 topic/robot-integration references it links.
- For an offline SLAM/map export change, defer to `HEDGIE_SLAM_RESEARCH.md` and its calibration/trajectory-format references.
- For a costmap-ready input or external-handoff change, defer to `BEDRAWN_NAVIGATION.md` and its ROS message/replay references.
