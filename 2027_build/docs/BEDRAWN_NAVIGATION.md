# Bedrawn: Mapping, Costmaps, and Nav2 Handoff

Branch: `bedrawn-nav-integration`

## Start here: the simple version

Bedrawn turns sensor observations into the representations Nav2 needs to make a safe plan. The first question is: **“Which nearby places are free, blocked, or unknown, and where is the rover on that representation?”**

Begin with simulation or replay and ordinary Nav2 components. Do not begin by writing a planner/plugin or commanding motors. Read `FOUNDATIONS.md`, especially the distinction between mapping and navigation, before reading the technical scope below.

### Vocabulary before implementation

- **Occupancy grid/map:** a top-down grid in which each cell represents free, occupied, or unknown space.
- **Costmap:** Nav2's local or global map of how undesirable each cell is. Obstacles are expensive/lethal; inflation adds a safety buffer around them.
- **Local costmap:** a moving, short-range safety view around the rover.
- **Global costmap:** the larger planning view, usually tied to a saved map.
- **`LaserScan` / `PointCloud2`:** standard ROS messages carrying 2D ranges / 3D points. Bedrawn may develop against synthetic examples first.
- **SLAM Toolbox:** a ROS 2 component that can create a 2D occupancy map and provide the map-to-odometry correction for a compatible laser-scan input.

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

## Reference docs: what to use and when

- [Nav2 first-time robot setup](https://docs.nav2.org/rolling/configuration_and_development/first_time_robot_setup_guide/): read in its stated order before writing Nav2 parameters: transforms, URDF, odometry, sensors, mapping/localization, footprint, then plugins.
- [Nav2 mapping and localization](https://docs.nav2.org/rolling/configuration_and_development/first_time_robot_setup_guide/sensors/mapping_localization/): use it to understand what `slam_toolbox` supplies, why its `map -> odom` ownership matters, and how static/obstacle/voxel/inflation layers fit together.
- [SLAM Toolbox repository](https://github.com/SteveMacenski/slam_toolbox): use it for supported configuration parameters and lifecycle/mapping behavior after the synthetic-scan baseline exists.
- [Nav2 costmap configuration](https://docs.nav2.org/configuration/packages/configuring-costmaps.html): use it to configure obstacle sources, clearing/marking, resolution, rolling windows, voxel behavior, and inflation. Do not infer safety values from tutorial defaults.
- [Nav2 plugin catalog](https://docs.nav2.org/rolling/configuration_and_development/navigation_plugins/): consult after standard costmaps work to select existing planner/controller plugins. It is a comparison/reference list, not a prerequisite to write a plugin.
- [ZED depth sensing in ROS 2](https://docs.stereolabs.com/docs/integrations/ros-2/depth-sensing): use it when replacing a synthetic obstacle source with registered depth or a point cloud; confirm frame, range, and confidence behavior.
- [Nav2 GPS localization](https://docs.nav2.org/rolling/tutorials/general_tutorials/navigation2_with_gps/navigation2_with_gps/): use only for the later outdoor GPS stage; protect the agreed TF ownership from global-frame jumps.

## Acceptance checks

- A valid `map -> odom -> base_link` chain exists, with one publisher per edge.
- `slam_toolbox` map creation/load is reproducible from the same recording.
- The local costmap marks obstacles and clears free space conservatively.
- Inflation reflects the measured rover footprint, not a guessed point robot.
- No-motors replay/simulation tests pass before any live navigation test.
- The navigation team can start the stack from the handoff without reading the legacy prototype.

## First independent milestone

Use a synthetic `LaserScan`/`PointCloud2` source and a standard Jazzy/Nav2 setup to bring up RViz, SLAM Toolbox, and visible local/global costmaps. Replace the synthetic source with Wobbles's topics later without redesigning the stack.
