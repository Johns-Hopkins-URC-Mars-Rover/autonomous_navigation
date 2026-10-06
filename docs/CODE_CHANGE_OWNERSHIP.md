# Code Change Ownership and Merge Boundaries

This plan keeps three branches productive before hardware, ROS 2, or one another's work is ready.

| Area | Owner | Branch | Merge dependency |
|---|---|---|---|
| Offline visual SLAM, loop closure, semantic/dense maps, metrics | Hedgie | `hedgie-slam-research` | None; uses session fixture or recordings |
| ZED wrapper, TF/URDF, recording, IMU/GPS, localization logs | Wobbles | `wobbles-sensor-localization` | None; live data or SVO only |
| Depth/scan adapters, SLAM Toolbox, Nav2 costmaps, replay/simulation | Bedrawn | `bedrawn-nav-integration` | None; synthetic source first |
| Legacy standalone ZED pipeline | Shared, narrow edits only | `main` via reviewed PR | No ROS rewrite |

## Boundary rules

1. Do not edit another person's package without agreement.
2. Use standard ROS 2 message types at package boundaries whenever possible.
3. Keep the legacy root-level Python prototype runnable; do not move it into the 2027 workspace as part of unrelated work.
4. Add one new package/configuration concern per pull request.
5. Do not merge branch scaffolding solely because it exists. Merge a vertical slice with a documented acceptance check.
6. Keep generated SVO, rosbag2, maps, models, and experiment outputs out of Git unless intentionally managed through an approved artifact store or Git LFS.

## Interface contracts to stabilize first

Wobbles will stabilize the live/replay sensor contract. Bedrawn may develop against synthetic data until then. Hedgie reads file-based sessions and therefore remains independent.

| Contract | Producer | Consumers | Minimum fields |
|---|---|---|---|
| Session manifest | Wobbles | Hedgie, Bedrawn | calibration, frames, timestamps, checksums, route metadata |
| Offline map export | Hedgie | Bedrawn | frame, resolution, occupancy/confidence, provenance |
| Sensor topics/TF | Wobbles | Bedrawn | standard message type, topic, frame id, rate, QoS |
| Obstacle representation | Bedrawn initially; Hedgie optionally later | Nav2 | source frame, timestamp, confidence, clearing semantics |

## Existing-code edit sequencing

1. Wobbles adds structured standalone exports only after agreeing on the manifest schema.
2. Hedgie factors camera-independent detection helpers only when tests prove `object_detection.py` behavior is preserved.
3. Bedrawn does not couple Nav2 to the root-level Python loop; it uses ROS messages and launch/config overlays.
4. Any common `2027_build` skeleton change should be a small reviewed PR from `main`, then rebased/cherry-picked by the three branches.
