# Subteam Scope: Data Synthesis, VSLAM, and Integration

## Our boundary

This subteam turns raw or synthetic rover observations into a **validated, replayable navigation-data bundle**. We own data synthesis, sensor/session evidence, visual SLAM, map/obstacle exports, and integration of those outputs into one documented handoff.

The next subteam owns everything after that boundary: costmap construction, route/goal choice, planner/controller configuration, recovery behavior, and motor integration.

## Our three responsibilities

| Responsibility | What this subteam produces | Initial workstream / branch |
| --- | --- | --- |
| **Data synthesis and sensor evidence** | synthetic fixtures, replayable SVO/rosbag sessions, manifest, calibrated frames, IMU timing/quality, and known-failure labels | Wobbles / `wobbles-sensor-localization` |
| **VSLAM and map research** | visual-only and visual-inertial trajectory comparisons, loop closures, map/occupancy exports, semantic/dense evidence, and metrics | Hedgie / `hedgie-slam-research` |
| **Integration and next-subteam handoff** | one replayable bundle that joins obstacle observations, map context, TF/localization context, footprint/offset metadata, and the contract/readme | Bedrawn / `bedrawn-nav-integration` |

The labels above describe responsibilities, not a requirement that only one person can help. The branch names remain the current merge boundaries.

## Big overall deliverable

Deliver one **Navigation Data & VSLAM Handoff Bundle** containing:

1. A stable session manifest plus replayable recorded and/or synthetic data.
2. Time-aligned RGB-D, IMU, pose/odometry, TF, diagnostics, and tracking-status evidence.
3. VSLAM trajectory/map outputs, with visual-only versus visual-inertial comparison when synchronized IMU data exists.
4. A documented obstacle source (`LaserScan` and/or `PointCloud2`) and optional map context (`OccupancyGrid`), including frame, timestamp, range/confidence, and marking/clearing semantics.
5. Measured rover footprint, sensor mounting offsets, route/environment metadata, replay instructions, and known failure cases.

The next subteam must be able to validate and consume this bundle without reading the legacy prototype or needing live hardware.

## Done means

- The same session/fixture replays deterministically enough to inspect the supplied topics, transforms, and outputs.
- The frame and timestamp conventions are explicit, and exactly one component owns each supplied TF edge.
- VSLAM and sensor outputs identify their provenance and quality limits rather than claiming guaranteed navigation accuracy.
- The bundle exposes inputs and evidence only; it does not contain a costmap, planner, controller, goal-selection policy, or motor command.
