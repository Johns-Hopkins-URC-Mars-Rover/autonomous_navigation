# Bedrawn: Mapping, Costmaps, and Nav2 Handoff

Branch: `bedrawn-nav-integration`

## Mission

Create a safe, replayable navigation-facing stack from camera-derived environment information. Start with standard Nav2 components and configuration; custom plugins are a later decision, not the starting point.

## Scope

### Camera-only stage

- Build a depth-to-`LaserScan` adapter or a constrained depth-slice source for the first 2D mapping baseline.
- Configure `slam_toolbox` for a reproducible map-building/save/load workflow.
- Configure local/global Nav2 costmaps using conservative standard layers:
  - static layer for the saved map;
  - obstacle and/or voxel layer for live ZED-derived obstacles;
  - inflation layer sized from the real rover footprint.
- Build a replay-first RViz/Nav2 demo using a synthetic bag, public bag, or recorded ZED data.
- Keep motors disabled; validate goals in simulation/replay first.

### IMU stage

- Verify that costmaps remain usable with the agreed local odometry frame.
- Filter depth-derived obstacles for pitch/roll and invalid-depth artifacts.
- Test mapping/navigation behavior during tracking loss and relocalization.

### GPS stage

- Consume the single approved global-localization source from Wobbles.
- Validate outdoor global/local costmaps and GPS waypoint behavior.
- Ensure global corrections do not cause unsafe local-costmap jumps.

## Deliverables

- `slam_toolbox` configuration and map build/save/load instructions.
- Nav2 parameters and launch files for replay/simulation.
- RViz configuration displaying TF, footprint, map, scan/point cloud, global costmap, and local costmap.
- A navigation-team handoff document: required topics, frames, QoS, map formats, configuration values, and failure behavior.
- A repeatable acceptance demonstration: load/replay -> localization -> costmaps -> no-motors navigation goal.

## Code changes owned by Bedrawn

Create `2027_build/src/rover_navigation/` and add configuration under `2027_build/config/`. Expected components:

- depth/point-cloud adapter nodes with synthetic-message tests;
- `slam_toolbox` configuration;
- Nav2 parameter overlays and launch files;
- robot footprint/costmap configuration;
- replay/simulation test harness;
- map and costmap validation scripts.

Do not modify ZED camera acquisition in `main.py`. Consume standard ROS messages from Wobbles's contract. Do not implement a custom planner, controller, behavior tree, or costmap plugin unless standard layers fail against documented requirements.

## Acceptance checks

- A valid `map -> odom -> base_link` chain exists, with one publisher per edge.
- `slam_toolbox` map creation/load is reproducible from the same recording.
- The local costmap marks obstacles and clears free space conservatively.
- Inflation reflects the measured rover footprint, not a guessed point robot.
- No-motors replay/simulation tests pass before any live navigation test.
- The navigation team can start the stack from the handoff without reading the legacy prototype.

## First independent milestone

Use a synthetic `LaserScan`/`PointCloud2` source and a standard Jazzy/Nav2 setup to bring up RViz, SLAM Toolbox, and visible local/global costmaps. Replace the synthetic source with Wobbles's topics later without redesigning the stack.
