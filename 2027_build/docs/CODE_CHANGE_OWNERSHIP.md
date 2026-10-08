# Subteam Responsibilities and Merge Boundaries

This subteam has one boundary: synthesize and validate navigation data, run VSLAM, and assemble a replayable handoff bundle. Costmaps, route selection, planning, control, and motors belong to the next subteam.

## Responsibilities

| Responsibility | Initial branch | Scope | Does not own |
| --- | --- | --- | --- |
| Data synthesis and sensor evidence | `wobbles-sensor-localization` | ZED/SVO and synthetic sessions, TF/URDF, manifest, IMU/GPS quality evidence, replay/recording | VSLAM research conclusions, downstream costmaps/planning |
| VSLAM and map research | `hedgie-slam-research` | visual/visual-inertial trajectories, loop closure, map/occupancy/semantic exports, quantitative evaluation | live-sensor acquisition, costmaps/planning |
| Integration and next-subteam handoff | `bedrawn-nav-integration` | synthetic/replay adapters, obstacle-input contract, footprint/offset metadata, final replayable bundle | costmap construction, planners/controllers, route choice, motors |
| Legacy standalone ZED prototype | reviewed changes via `main` | narrow exports needed for evidence or replay | ROS workspace migration or downstream navigation stack |

The branch names are merge boundaries, not exclusive personal roles. Anyone may contribute within an agreed responsibility without changing the subteam boundary.

## Big overall deliverable

The only cross-branch deliverable is the **Navigation Data & VSLAM Handoff Bundle** described in [SUBTEAM_SCOPE.md](SUBTEAM_SCOPE.md). It combines the outputs below into one replayable artifact for the next subteam.

| Contract | Producer responsibility | Consumer | Required content |
| --- | --- | --- | --- |
| Session/fixture manifest | Data synthesis | VSLAM, integration | calibration, frames, timestamps, checksums, route/environment metadata, known failures |
| Sensor evidence | Data synthesis | VSLAM, integration | RGB-D, IMU, pose/odometry, diagnostics, tracking status, replay instructions |
| VSLAM/map evidence | VSLAM | Integration | trajectory, map/occupancy context, frame, resolution, confidence/provenance, evaluation results |
| Navigation Data & VSLAM Handoff Bundle | Integration | Next subteam | obstacle source, TF/localization context, footprint/offsets, map context, replay evidence, failure semantics |

## Timeline and gates

1. **Shared measurement preflight:** establish camera/IMU timing, fixed frames, and one replayable session. This enables IMU evidence but does not block synthetic data or VSLAM fixtures.
2. **Parallel work:** data synthesis validates sensor quality and IMU-assisted motion; VSLAM establishes the visual baseline and evaluation; integration prepares the fixture, handoff schema, and obstacle-input validation.
3. **Bundle gate:** replay one complete bundle, verify manifest/topics/QoS/TF, compare visual and visual-inertial results where IMU is synchronized, and document the one owner of `map -> odom`.
4. **Package gate:** package only validated producers and handoff tools. Do not migrate the legacy prototype, introduce downstream navigation packages, or merge empty scaffolding merely to look complete.

## Boundary rules

1. Use standard ROS 2 message types at the subteam boundary whenever possible.
2. Keep the root-level prototype runnable; do not move it into `2027_build/` as unrelated cleanup.
3. One component owns each TF edge. Do not publish competing `map -> odom` transforms.
4. Keep generated SVO, rosbag2, maps, models, and large experiment outputs out of Git unless an approved artifact store or Git LFS is used.
5. The next subteam receives data and evidence, not a costmap, planner, controller, goal policy, or motor command.

## Edit sequencing

1. Agree on manifest and handoff fields before changing cross-workstream code.
2. Add a small tested producer/exporter or fixture at a time.
3. Run the bundle gate with replay before package conversion.
4. Consult [WOBBLES_SENSOR_LOCALIZATION.md](WOBBLES_SENSOR_LOCALIZATION.md), [HEDGIE_SLAM_RESEARCH.md](HEDGIE_SLAM_RESEARCH.md), and [BEDRAWN_NAVIGATION.md](BEDRAWN_NAVIGATION.md) for responsibility-specific detail.
