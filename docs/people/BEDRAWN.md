# Integration: Navigation Data & VSLAM Handoff Bundle

Branch: `bedrawn-nav-integration`

## Start here: the simple version

This responsibility does **not** build the costmap or choose the route. It assembles the reliable, replayable data-synthesis and VSLAM outputs that the next subteam needs to make those decisions. The first question is: **“Can another team consume our obstacle observations, localization context, and VSLAM evidence without having to rediscover frames, timing, calibration, or safety limits?”**

Begin with synthetic or replayed messages while data synthesis performs IMU integration/validation. This baseline does not wait for an IMU result; it switches to the agreed sensor/TF contract at the integration gate. Motors remain off. Read [`docs/README.md`](../README.md) before this plan.

### Vocabulary before implementation

- **Costmap-ready input:** a documented obstacle observation plus the time, source frame, transform chain, and semantics needed by another team to construct a costmap safely.
- **`LaserScan` / `PointCloud2`:** standard ROS messages carrying 2D ranges / 3D points. These are candidate obstacle inputs, not a costmap themselves.
- **`OccupancyGrid`:** a top-down free/occupied/unknown map. It may be supplied as optional map context; the receiving team decides how to use it.
- **Footprint/safety envelope:** measured rover dimensions and clearance assumptions that the costmap/planning team needs to select inflation and collision constraints.
- **Replay bundle:** a rosbag2 or synthetic fixture, manifest, and launch/readme instructions that reproduce the handoff without live hardware.

## Mission

Produce one large, costmap-ready navigation-input deliverable that the next subteam can consume directly. Integration owns input quality and handoff evidence, not costmap configuration, planner/controller selection, goal selection, or motor commands.

## Scope

### Independent input baseline

- Build a depth-to-`LaserScan` adapter or constrained depth-slice source with synthetic-message tests.
- Define obstacle-input semantics: source frame, timestamp, range/confidence limits, invalid-data behavior, and what observations may mark or clear space.
- Prepare the replay bundle and document topic name, message type, rate, QoS, and expected TF chain.
- Measure and record rover footprint dimensions and the assumptions needed by the receiving team to choose a safety margin.

### Integration with data synthesis and VSLAM

- Replace synthetic observations with data-synthesis replay/live topics only after the shared sensor-topic/TF contract is stable.
- Verify obstacle input is time-aligned with the agreed local odometry frame and behaves predictably through tracking loss/relocalization.
- Include the optional VSLAM map export as map context when available, with frame, resolution, occupancy/confidence, and provenance documented.
- Produce one representative replay bundle that exercises the complete handoff.

### Later GPS context

- Pass through the single approved global-localization source from data synthesis only after its quality/heading contract is accepted.
- Document global-frame jumps and localization validity for the receiving team; do not configure their costmap or waypoint behavior.

## Overall deliverable: costmap-ready navigation-input bundle

The bundle must contain:

1. A replayable `LaserScan` and/or `PointCloud2` obstacle source, plus an optional `OccupancyGrid` map-context export.
2. A handoff contract listing each message's type, topic, frame id, timestamp convention, rate, QoS, range/confidence limits, and marking/clearing semantics.
3. The required `map -> odom -> base_link -> sensor` transform ownership and a local pose/odometry validity contract.
4. Measured rover footprint dimensions, sensor mounting offsets, and stated safety assumptions for the receiving team's inflation/collision choices.
5. A manifest, replay command, small fixture or bag, and known failure cases such as invalid depth, tracking loss, and relocalization.

The receiving costmap/planning team owns conversion of this bundle into a costmap, route selection, planning/controller configuration, and any future motor integration.

## Code changes owned by integration

Create `2027_build/src/rover_navigation_inputs/` and add handoff configuration under `2027_build/config/`. Expected components:

- depth/point-cloud adapter nodes with synthetic-message tests;
- obstacle-input validation and replay harness;
- handoff contract/manifest generator or validator;
- measured-footprint and sensor-offset configuration;
- optional map-context exporter/adapter, without assuming a downstream costmap implementation.

Do not modify ZED camera acquisition in `main.py`. Consume standard ROS messages from the data-synthesis contract. Do not implement `slam_toolbox`, Nav2 costmaps, planners, controllers, behavior trees, or costmap plugins on this branch.

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

Use a synthetic `LaserScan`/`PointCloud2` source to produce a documented replay bundle with the required TF/localization context and footprint metadata. Replace the synthetic source with data-synthesis topics later without changing the external handoff contract.

## Agent prompts by phase

Start each prompt with the shared preamble in [TEAM.md](../TEAM.md#shared-preamble), using this file and branch `bedrawn-nav-integration`. Stage 1 (preflight checklist and manifest schema, prompts 1 and 2) is shared by all three people and is listed there too. Due dates and sync meetings are in [TEAM.md](../TEAM.md#sync-meetings). Stages are explained in [TEAM.md](../TEAM.md#delivery-stages).

### Stage 2: parallel work (synthetic baseline, due G2 Fri Oct 23)

Build against stand-ins until G1 (Oct 16), then switch to Wobbles' recorded sessions. The only work that needs the rover is the footprint measurement.

3. **Handoff contract (draft by C0 Oct 12, v1.0 frozen at G3 Oct 30).** "Draft the handoff contract. For each message, list its type, topic, frame id, timestamp convention, rate, QoS, range/confidence limits, and marking/clearing semantics. Also list the TF chain and the owner of each edge. Write a validator that checks a bag against the contract." *Waits on: Wobbles' topic list (Wobbles prompt 4). Build on `docs/CONTRACT.md`, which already has placeholder QoS values (§1) and a placeholder footprint (§10, `docs/contract/rover_geometry.yaml`). After G2, any change needs a version bump and a message to the algorithm team.*
4. **Synthetic fixture (due C0 Oct 12).** "Create a synthetic rosbag2 fixture with `LaserScan`, `PointCloud2`, odometry, and TF for a short, known scene, so the bundle can be tested without hardware." *Topic names must match the contract exactly so that swapping in real data later changes nothing.*
5. **Depth to obstacle adapter (due G2 Oct 23).** "Create `2027_build/src/rover_navigation_inputs/` with a depth-to-`LaserScan` (or constrained depth-slice) adapter node. Handle invalid depth, min/max range, and the source frame. Test it with synthetic messages."
6. **Footprint and offsets (due G1 Oct 16).** "Add a config file in `2027_build/config/` for the measured rover footprint and sensor mounting offsets, plus a short doc on the safety assumptions. Put a TODO where a measurement is missing. Never assume a point robot." *Measure in the same session as Wobbles prompt 3.*
7. **Replay harness (due G2 Oct 23).** "Write one replay command that plays the bundle and runs the contract validator: topics present, monotonic timestamps, frames resolving through TF, and one publisher per TF edge."

### Stage 3: bundle gate (G1 Fri Oct 16 to G3 Fri Oct 30)

8. **Switch to real data (start after G1 Oct 16, due G2 Oct 23).** "Replace the synthetic obstacle source with replayed data-synthesis topics without changing the external contract. Check time alignment with the odometry frame, and document behavior during invalid depth, tracking loss, and relocalization." *Waits on: Wobbles prompts 7 and 11.*
9. **Assemble the bundle (dry run Tue Oct 27, due G3 Fri Oct 30).** "Assemble the Navigation Data & VSLAM Handoff Bundle: manifest, bag or fixture, obstacle source, optional VSLAM `OccupancyGrid`, footprint and offsets, a README with the replay command, and known failure cases. Then give a fresh agent only the bundle README and confirm it can validate the bundle without reading the legacy prototype." *Waits on: Hedgie prompt 12 and Wobbles prompt 10.*

### Stage 4: package conversion (not this month; date set at the Oct 30 review)

10. **Package gate.** "List the vertical slices that passed the bundle gate. Convert only those into the final Jazzy ROS 2 packages (`rover_camera_ai`, `rover_localization`, `rover_navigation_inputs`, `rover_bringup`) with `colcon build` and tests. Do not migrate the legacy prototype or add empty scaffolding." *Waits on: G3. The October plan uses its own Humble packages (see `docs/README.md`).*

### Stage 5: GPS (not this month; date set at the Oct 30 review)

11. **Global-localization pass-through.** "Pass through only the global-localization source that data synthesis approved. Document global-frame jumps and when localization is valid, for the next subteam. Do not configure their costmap or waypoint behavior." *Waits on: Wobbles prompt 12.*

Prompts 3, 4, and 6 cover the [first independent milestone](#first-independent-milestone).
