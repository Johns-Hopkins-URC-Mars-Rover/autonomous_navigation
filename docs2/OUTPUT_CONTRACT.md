# Output Contract for the Algorithm Team (draft v0.2, names frozen at C0)

This is what our sensor-fusion and perception stack publishes. The algorithm (planning/control) team builds against this, live or from our recorded bags. Target: **v1.0 frozen by October 30, 2026** (task H2).

Units, axes, timestamps, and invalid-depth encoding follow `docs/contract/SENSOR_DATA_CONTRACT.md` §1 (SI units, REP 103 axes, acquisition-time stamps, `NaN` / `±inf` depth).

**What is frozen and how it changes.** Topic names, message types, frame roles and label codes are frozen at C0 (Mon Oct 12). Values marked **[placeholder]** are dummies that let code run while the rover is still changing. They are listed in §10 and replaced later without a version bump. Other changes follow these rules:

- After C0, a change needs agreement from the person who consumes it.
- After G2 (Fri Oct 23), it also needs a version bump and a message to the algorithm team.

## 1. Topics

All `/rover/...` names are ours and stay stable. If the pinned ZED wrapper publishes different names, our launch file remaps them; consumers never adapt to the wrapper. **[verify]** source names on the pinned wrapper tag.

### Pose and sensors (from the ZED wrapper, fused camera + IMU)

| Topic | Type | Frame | Target rate | Meaning |
| --- | --- | --- | --- | --- |
| `/rover/odom` | `nav_msgs/Odometry` | `odom` → child `base_link` | camera rate (15–30 Hz) | Smooth visual-inertial pose and velocity. Use this for local control. |
| `/rover/pose` | `geometry_msgs/PoseWithCovarianceStamped` | `map` | camera rate | Pose corrected by ZED area memory. May jump on relocalization. |
| `/rover/imu` | `sensor_msgs/Imu` | `zed_imu_link` | ≥ 100 Hz | Accelerations (m/s²), angular rates (rad/s), fused orientation. |
| `/rover/camera/rgb/image` | `sensor_msgs/Image` | `<left optical frame>` **[placeholder]** | camera rate | Rectified left colour image. |
| `/rover/camera/rgb/camera_info` | `sensor_msgs/CameraInfo` | `<left optical frame>` | camera rate | Intrinsics for the image above. |
| `/rover/camera/depth/image` | `sensor_msgs/Image` (32FC1, metres) | `<left optical frame>` | camera rate | Depth registered to the RGB image. |
| `/rover/camera/depth/camera_info` | `sensor_msgs/CameraInfo` | `<left optical frame>` | camera rate | Intrinsics for depth. |
| `/rover/tracking/status` | wrapper's tracking-status message **[placeholder]** type | — | camera rate | Positional-tracking state (OK, SEARCHING, LOST, …). Feeds `status/ok` and the failure table. |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | see §2 | — | Transform tree. |

**Frame names in code.** Code may hardcode only `map`, `odom` and `base_link`. Every other frame (camera, optical, IMU) is read from the message's `header.frame_id` and resolved through TF. Then a wrapper rename or a new camera mount changes no code.

### Perception (from `rover_perception`)

| Topic | Type | Frame | Target rate | Meaning |
| --- | --- | --- | --- | --- |
| `/rover/perception/grid` | `nav_msgs/OccupancyGrid` | `odom` | ≥ 5 Hz | Standard occupancy: `0` free, `100` occupied, `-1` unknown. |
| `/rover/perception/class_grid` | `nav_msgs/OccupancyGrid` | `odom` | ≥ 5 Hz | Same cells as `grid`, holding **label codes** (§3), not probabilities. |
| `/rover/perception/confidence` | `nav_msgs/OccupancyGrid` | `odom` | ≥ 5 Hz | Confidence of each cell's label, `0`–`100`; `-1` never observed. |
| `/rover/perception/obstacle_points` | `sensor_msgs/PointCloud2` (x, y, z float32) | `odom` | ≥ 5 Hz | 3D points classified as obstacle or wall (ground removed). |
| `/rover/perception/scan` | `sensor_msgs/LaserScan` | `base_link` | ≥ 5 Hz | Nearest obstacle per bearing, within the camera's field of view. |
| `/rover/perception/objects` | `vision_msgs/Detection3DArray` | `base_link` | ≥ 5 Hz | YOLO objects with 3D centre, size, class name, and score. |
| `/rover/status/ok` | `std_msgs/Bool` | — | ≥ 5 Hz | `true` only when tracking is OK, depth is usable, and outputs are fresh. |
| `/diagnostics` | `diagnostic_msgs/DiagnosticArray` | — | 1 Hz | Details behind `ok`: tracking state, valid-depth fraction, grid age, latencies. |

**Output timestamps.** Every perception output carries the `header.stamp` of the depth frame it was computed from, not the time it was published. Consumers look up TF at that stamp.

### QoS **[placeholder]**

| Topics | Reliability | Durability | Depth |
| --- | --- | --- | --- |
| Camera images and `camera_info` | reliable | volatile | 5 |
| `/rover/imu` | reliable | volatile | 50 |
| `/rover/odom`, `/rover/pose`, `/rover/tracking/status` | reliable | volatile | 10 |
| `/rover/perception/*`, `/rover/status/ok` | reliable | volatile | 5 |
| `/tf_static` | reliable | transient local | 1 (ROS standard) |

These are starting values. Measure them against the pinned wrapper's defaults and the rover's CPU load (P10) before v1.0.

### Grid geometry (starting values; final values in v1.0)

| Property | Value |
| --- | --- |
| Size | 10 m × 10 m, rolling, centred on the rover |
| Cell size | 0.05 m |
| Frame | `odom` (never jumps; moves with the rover in steps) |
| Height band counted as obstacle | 0.05 m above the fitted floor up to rover height + 0.10 m (rover height from `docs/contract/rover_geometry.yaml`, **[placeholder]**) |
| Valid depth range | 0.3 – 8.0 m |

## 2. TF tree and ownership

```text
map → odom → base_link → zed_camera_link → … → zed_left_camera_frame → left optical frame
                                         └→ zed_imu_link
```

| Edge | Published by | Notes |
| --- | --- | --- |
| `map → odom` | ZED wrapper (area memory) | Only publisher. Can jump on relocalization. |
| `odom → base_link` | ZED wrapper (visual-inertial tracking) | Only publisher. Smooth. |
| `base_link → zed_camera_link` | `robot_state_publisher` from `rover_description` | From `docs/contract/rover_geometry.yaml`. **[placeholder]** until the tape measurement (task F1). |
| `zed_camera_link → camera/IMU frames` | ZED wrapper / ZED xacro (factory calibration) | Not duplicated in our URDF. |

`base_link` is at floor level under the rover's turning centre. **[verify]** the optical-frame name on the pinned wrapper tag.

**If area memory is turned off (decision F7, G1):** `map → odom` is published as a fixed identity, and `/rover/pose` equals the `odom` pose. **[placeholder]**: check how the pinned wrapper behaves with area memory off, then update this line.

**Rule for consumers:** use `odom` for local planning and control. Use `map` only for things that must stay put across a session, and expect it to jump.

## 3. Label codes in `class_grid`

The values are chosen so that RViz's standard map view shows free as white, obstacles as grey, walls as black, and unknown as the background colour.

| Code | Label | Meaning |
| --- | --- | --- |
| `-1` | unknown | Never observed, out of range, or depth invalid. **Not drivable by default.** |
| `0` | free | Floor was seen here, or depth saw past this cell. |
| `50` | obstacle | Occupied, not part of a wall. May carry a YOLO class in `/rover/perception/objects`. |
| `100` | wall | Occupied and part of a straight vertical structure at least 1.0 m long and 0.5 m tall (thresholds in v1.0). |

Labels come from 3D geometry. YOLO only adds an object class on top; a missed YOLO detection never makes a cell free.

## 4. Behaviour when things go wrong

The "observed behaviour" column is filled in by task F6 from real tests. The "perception behaviour" column is what our node is designed to do.

| Situation | Observed ZED behaviour (F6) | Perception behaviour | `status/ok` |
| --- | --- | --- | --- |
| Tracking lost (lens covered, blank wall, darkness) | to be measured | Grid stops integrating new depth and keeps its last state. `scan` and `objects` keep publishing in `base_link`, since they do not need the pose. | `false` |
| Tracking recovers with a pose jump > 0.3 m | to be measured | Grid is cleared to unknown and rebuilt. | `false` until 1 s after recovery |
| `map → odom` jumps (relocalization) | to be measured | No effect: the grid lives in `odom`. | unchanged |
| More than 50% of depth invalid | — | Cells are not updated from missing pixels; they stay unknown or keep their old value. | `false` |
| Input older than 0.5 s | — | Outputs stop updating. | `false` |

## 5. Performance (filled by task P10)

| Output | Target rate | Measured rate | Target latency | Measured latency |
| --- | --- | --- | --- | --- |
| `/rover/odom` | camera rate | — | < 100 ms | — |
| `/rover/imu` | ≥ 100 Hz | — | — | — |
| `/rover/perception/grid` | ≥ 5 Hz | — | < 250 ms | — |
| `/rover/perception/objects` | ≥ 5 Hz | — | < 300 ms | — |

## 6. YOLO classes

The class list comes from `models/best.pt` (`model.names`). Fill it in at v1.0; do not guess it.

| ID | Name |
| --- | --- |
| — | to be listed from the model |

## 7. Not provided

- No costmap, inflation, footprint padding, path, or velocity command.
- No guarantee that `free` is safe to drive: free means "seen and empty at the time", within the camera's field of view only.
- No drop-off, stair, or glass detection. These appear as unknown or, in bad cases, as free. The algorithm team must treat this as a known limitation.
- No GPS or global position.

## 8. Open items before v1.0

- **[verify]** Wrapper topic names, frame names, and parameter names on the pinned tag.
- **[verify]** IMU publish rate available on the camera model.
- Fill §4 observed behaviour (F6), §5 measurements (P10), §6 classes.
- Final grid size, cell size, and wall thresholds after G2.
- Confirm with the algorithm team that two `OccupancyGrid` topics are enough, or whether they want a multi-layer `grid_map` instead (stretch goal).

## 9. Persistent map (Phase 4, draft, not part of v1.0)

Added after the October 30 handoff by Phase 4 (tasks M1–M6). Nothing in v1.0 depends on it. Final names and the TF owner of `map → odom` depend on decision M1; see [PHASES.md](PHASES.md).

| Topic / file | Type | Frame | Meaning |
| --- | --- | --- | --- |
| `/rover/map/grid` | `nav_msgs/OccupancyGrid`, latched (transient local) | `map` | Persistent free / occupied / unknown for the whole mapped area |
| `/rover/map/class_grid` | `nav_msgs/OccupancyGrid`, latched | `map` | Same label codes as §3 |
| `maps/<map_id>/map.yaml` + `map.pgm` | Nav2 `map_server` format | `map` | Saved occupancy, loadable by standard tools |
| `maps/<map_id>/class.pgm` | image, same size and origin as `map.pgm` | `map` | Saved label codes |
| `maps/<map_id>/area_map.area` | ZED area map | — | Lets the ZED relocalize so a new session's `map` frame matches the saved map |
| `maps/<map_id>/map_manifest.json` | JSON | — | Source sessions, resolution, origin, software versions, alignment check result |

Rules: the local grid in `odom` (§1) stays the input for local control; the persistent map is for "what does this area look like" and may be corrected after relocalization. Saved maps are stored outside Git.

## 10. Placeholders and mount independence

The rover is still changing, so geometry and some wrapper details are dummies for now. Code is written so that replacing a dummy means editing one file, not changing algorithms.

### Rules

1. **No algorithm hardcodes rover geometry.** Camera position, tilt, rover size and IMU offset are inputs:
    - live code reads them from TF;
    - offline code reads them from the session manifest or the frame dump's `mount.json`;
    - both come from [`docs/contract/rover_geometry.yaml`](../docs/contract/rover_geometry.yaml).
2. **Gravity and the floor are measured, not assumed.** Ground fitting uses the IMU gravity direction and the depth data, never a fixed camera height or pitch.
3. **Outputs are placed through TF.** The grid lives in `odom`; `scan` and `objects` are transformed into `base_link` at the input stamp. A new mount changes those transforms, not the code.
4. **Tested on more than one mount.** Every geometry-dependent unit test also runs on the `test_mounts` in `rover_geometry.yaml`: rear and yawed, tilted down, and rolled to the side. A test that passes only on the default mount counts as failing.

### Placeholder register

Each row is replaced later, without a contract version bump, by the owner when its trigger happens.

| Placeholder | Current dummy | Where it lives | Replaced by | Trigger |
| --- | --- | --- | --- | --- |
| Camera mount `base_link → zed_camera_link` | x 0.20, y 0, z 0.30 m; no rotation | `rover_geometry.yaml` | Wobbles (F1) | Rover design settles; tape-measure session |
| Footprint | 0.60 × 0.40 × 0.40 m, centred on `base_link` | `rover_geometry.yaml` | Bedrawn | Same session |
| Rover height in the obstacle band | footprint height | `rover_geometry.yaml` | Bedrawn | Same session |
| Optical frame name | `<left optical frame>` | §1 | Wobbles | Pinned wrapper tag checked (S4) |
| Tracking-status message type | wrapper's type, unnamed | §1 | Wobbles | Pinned wrapper tag checked |
| QoS values | §1 QoS table | §1 | Bedrawn | P10 load measurements |
| `map → odom` with area memory off | identity | §2 | Wobbles | Decision F7 at G1 |
| Grid size, cell size, wall thresholds | §1 grid geometry, §3 | §1, §3 | Hedgie | G2 |
