# Bedrawn: Costmap-Ready Navigation Input Handoff

Branch: `bedrawn-nav-integration`

## Start here: the simple version

Bedrawn does **not** build the costmap or choose the route. Bedrawn delivers the reliable, replayable inputs that the costmap/planning team needs to make those decisions. The first question is: **“Can another team consume our obstacle observations and localization context without having to rediscover frames, timing, calibration, or safety limits?”**

Begin with synthetic or replayed messages while Wobbles performs IMU integration/validation. Bedrawn's baseline does not wait for an IMU result; it switches to Wobbles' agreed sensor/TF contract at the integration gate. Motors remain off. Read `FOUNDATIONS.md` before this plan.

### Vocabulary before implementation

- **Costmap-ready input:** a documented obstacle observation plus the time, source frame, transform chain, and semantics needed by another team to construct a costmap safely.
- **`LaserScan` / `PointCloud2`:** standard ROS messages carrying 2D ranges / 3D points. These are candidate obstacle inputs, not a costmap themselves.
- **`OccupancyGrid`:** a top-down free/occupied/unknown map. It may be supplied as optional map context; the receiving team decides how to use it.
- **Footprint/safety envelope:** measured rover dimensions and clearance assumptions that the costmap/planning team needs to select inflation and collision constraints.
- **Replay bundle:** a rosbag2 or synthetic fixture, manifest, and launch/readme instructions that reproduce the handoff without live hardware.

## Mission

Produce one large, costmap-ready navigation-input deliverable that an external costmap/planning team can consume directly. Bedrawn owns input quality and handoff evidence, not costmap configuration, planner/controller selection, goal selection, or motor commands.

## Scope

### Independent input baseline

- Build a depth-to-`LaserScan` adapter or constrained depth-slice source with synthetic-message tests.
- Define obstacle-input semantics: source frame, timestamp, range/confidence limits, invalid-data behavior, and what observations may mark or clear space.
- Prepare the replay bundle and document topic name, message type, rate, QoS, and expected TF chain.
- Measure and record rover footprint dimensions and the assumptions needed by the receiving team to choose a safety margin.

### Integration with Wobbles and Hedgie

- Replace synthetic observations with Wobbles replay/live topics only after the shared sensor-topic/TF contract is stable.
- Verify obstacle input is time-aligned with the agreed local odometry frame and behaves predictably through tracking loss/relocalization.
- Include Hedgie's optional map export as map context when available, with frame, resolution, occupancy/confidence, and provenance documented.
- Produce one representative replay bundle that exercises the complete handoff.

### Later GPS context

- Pass through the single approved global-localization source from Wobbles only after its quality/heading contract is accepted.
- Document global-frame jumps and localization validity for the receiving team; do not configure their costmap or waypoint behavior.

## Overall deliverable: costmap-ready navigation-input bundle

The bundle must contain:

1. A replayable `LaserScan` and/or `PointCloud2` obstacle source, plus an optional `OccupancyGrid` map-context export.
2. A handoff contract listing each message's type, topic, frame id, timestamp convention, rate, QoS, range/confidence limits, and marking/clearing semantics.
3. The required `map -> odom -> base_link -> sensor` transform ownership and a local pose/odometry validity contract.
4. Measured rover footprint dimensions, sensor mounting offsets, and stated safety assumptions for the receiving team's inflation/collision choices.
5. A manifest, replay command, small fixture or bag, and known failure cases such as invalid depth, tracking loss, and relocalization.

The receiving costmap/planning team owns conversion of this bundle into a costmap, route selection, planning/controller configuration, and any future motor integration.

## Code changes owned by Bedrawn

Create `2027_build/src/rover_navigation_inputs/` and add handoff configuration under `2027_build/config/`. Expected components:

- depth/point-cloud adapter nodes with synthetic-message tests;
- obstacle-input validation and replay harness;
- handoff contract/manifest generator or validator;
- measured-footprint and sensor-offset configuration;
- optional map-context exporter/adapter, without assuming a downstream costmap implementation.

Do not modify ZED camera acquisition in `main.py`. Consume standard ROS messages from Wobbles's contract. Do not implement `slam_toolbox`, Nav2 costmaps, planners, controllers, behavior trees, or costmap plugins on this branch.

## Reference docs: what to use and when

- [ROS 2 message interfaces](https://docs.ros.org/en/jazzy/p/sensor_msgs/interfaces/msg/LaserScan.html): use it to verify the `LaserScan` fields and units exported to the receiving team.
- [ROS 2 rosbag2 documentation](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data.html): use it to create and replay the evidence bundle.
- [ZED depth sensing in ROS 2](https://docs.stereolabs.com/docs/integrations/ros-2/depth-sensing): use it when replacing a synthetic obstacle source with registered depth or a point cloud; confirm frame, range, and confidence behavior.
- [Nav2 costmap configuration](https://docs.nav2.org/configuration/packages/configuring-costmaps.html): consult only to understand the fields a receiving costmap team will need; do not use it to implement their configuration here.

## Acceptance checks

- The replay bundle delivers the documented obstacle messages and TF chain without live hardware.
- Each obstacle message has an expected source frame, monotonic timestamp, documented range/confidence behavior, and known marking/clearing semantics.
- The handoff includes measured footprint and sensor offsets; it does not guess a point robot.
- A consumer can inspect or replay the input bundle without reading the legacy prototype.
- The bundle documents behavior during invalid depth, tracking loss, and relocalization.
- No costmap, planner, controller, or motor command is implemented or claimed by this branch.

## First independent milestone

Use a synthetic `LaserScan`/`PointCloud2` source to produce a documented replay bundle with the required TF/localization context and footprint metadata. Replace the synthetic source with Wobbles's topics later without changing the external handoff contract.
