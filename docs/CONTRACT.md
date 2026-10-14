# Contract: what we record and publish (draft v0.2, names frozen at C0)

This file is the single contract for sensor recordings and for the outputs the algorithm (planning/control) team builds against, live or from our recorded bags. Target: **v1.0 frozen by October 30, 2026** (task H2).

| Section | Covers |
| --- | --- |
| §0 | Units, axes, timestamps, invalid depth |
| §1–§3 | Topics, TF tree and ownership, label codes |
| §4–§6 | Failure behaviour, performance, YOLO classes |
| §7–§8 | What is not provided, open items before v1.0 |
| §9 | Persistent map (Phase 4 draft) |
| §10 | Placeholders and mount independence |
| §11–§13 | Recorded topics, session folder and manifest, reference sessions |

Data files: [`contract/session_manifest.example.json`](contract/session_manifest.example.json) (example manifest) and [`contract/rover_geometry.yaml`](contract/rover_geometry.yaml) (placeholder mount and footprint).

**Owner.** Phase 3 (recording and integration), tasks R1, R2, R5 and H2. Phase 1 supplies the measured mount (F1) and the version table (S6).

**What is frozen and how it changes.** Topic names, message types, frame roles, label codes and the session format are frozen at C0 (Mon Oct 12). Values marked **[placeholder]** are dummies that let code run while the rover is still changing. They are listed in §10 and replaced later without a version bump. Items marked **[verify]** depend on the pinned ZED SDK / wrapper release or the camera model. Other changes follow these rules:

- After C0, a change needs agreement from the person who consumes it.
- After G2 (Fri Oct 23), it also needs a version bump and a message to the algorithm team.

## 0. Units, axes, timestamps, invalid depth

### Units

SI everywhere.

| Quantity | Unit |
| --- | --- |
| Position, depth, range | metres (m) |
| Angle | radians (rad) in messages and files; degrees only in human-readable reports |
| Linear acceleration | m/s² |
| Angular velocity | rad/s |
| Time | integer nanoseconds (`t_ns`) in CSV/JSON; float seconds only in TUM files (the format requires it) |
| Orientation | unit quaternion, order `x, y, z, w` |

The legacy prototype already uses metres (`main.py` `_build_init_params`: `coordinate_units = sl.UNIT.METER`).

### Axes

| Frame kind | Convention |
| --- | --- |
| Body and world frames (`map`, `odom`, `base_link`, `zed_camera_link`, `zed_imu_link`) | REP 103: X forward, Y left, Z up, right-handed |
| Optical frames (`*_optical_frame`) | REP 103 optical: X right, Y down, Z forward (into the scene) |
| ZED world frame in non-ROS files (frame dumps, TUM exports) | `RIGHT_HANDED_Z_UP_X_FWD`, the same axes as REP 103 body frames; set in `main.py` `_build_init_params` |

Axis signs are checked by task F3: tilting nose-down, rolling left and yawing left must give the signs REP 103 predicts.

### Timestamps

1. **Acquisition time, not publish time.** Every image, depth frame, IMU sample and pose carries the time the sensor captured it. In the ZED SDK this is `TIME_REFERENCE.IMAGE` for frames. ROS message `header.stamp` holds the same value.
2. **Outputs inherit the input stamp.** Every perception output carries the `header.stamp` of the depth frame it was computed from, not the time it was published. Consumers look up TF at that stamp.
3. **One clock.** IMU and image stamps come from the same clock (task F4). Stamps never go backwards within a session (acceptance target: none in a 10-minute run).
4. **Replay uses recorded time.** Bags play with `ros2 bag play --clock` and every node runs with `use_sim_time:=true` (task R3). SVO replay through the wrapper uses the SVO's own timestamps.
5. **Manifest times** (`start_t_ns`, `end_t_ns`, failure events) use the same clock as the recorded stamps.

### Invalid depth

Depth images are `float32`, metres, registered to the rectified left image (ROS encoding `32FC1`). Invalid pixels are kept exactly as the ZED SDK gives them and are **never** replaced with 0 or a max range:

| Value | Meaning (ZED SDK convention, **[verify]** on the pinned SDK) |
| --- | --- |
| `NaN` | No measurement (occlusion, no texture, low confidence) |
| `+inf` | Beyond the maximum depth range |
| `-inf` | Closer than the minimum depth range |

Consumers decide how to treat these. The rule that applies everywhere (decision D7): **missing depth never means free space.**

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
| Height band counted as obstacle | 0.05 m above the fitted floor up to rover height + 0.10 m (rover height from `contract/rover_geometry.yaml`, **[placeholder]**) |
| Valid depth range | 0.3 – 8.0 m |

## 2. TF tree and ownership

```text
map → odom → base_link → zed_camera_link → … → zed_left_camera_frame → left optical frame
                                         └→ zed_imu_link
```

`zed_camera_link` and `zed_imu_link` are the ZED wrapper's names for the generic `camera_link` and `imu_link` in the per-person plans.

| Edge | Single publisher | Notes |
| --- | --- | --- |
| `map → odom` | ZED wrapper (area memory) | Decision D4. Can jump on relocalization. |
| `odom → base_link` | ZED wrapper (visual-inertial tracking) | D4. Smooth. |
| `base_link → zed_camera_link` | `robot_state_publisher` from `rover_description` | From `contract/rover_geometry.yaml`. **[placeholder]** until the tape measurement (task F1). |
| `zed_camera_link → camera/IMU frames` | ZED wrapper / ZED xacro (factory calibration) | Not duplicated in our URDF. |

- `base_link` is at floor level under the rover's turning centre. **[verify]** the optical-frame name on the pinned wrapper tag.
- **One publisher per edge.** No `robot_localization`, `slam_toolbox`, AMCL or GPS filter may also publish `map → odom` (D3, D4). Phase 4 option B would change this and must revise D4 first.
- Every recorded session stores the static `base_link → zed_camera_link` transform in its manifest (§12), so recordings stay interpretable if the mount changes. A session recorded with the dummy mount says so; when the real mount is measured, old sessions are re-processed by swapping the transform.
- **If area memory is turned off (decision F7, G1):** `map → odom` is published as a fixed identity, and `/rover/pose` equals the `odom` pose. **[placeholder]**: check how the pinned wrapper behaves with area memory off, then update this line.

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
- No GPS or global position. When GPS returns, add `NavSatFix` with covariance, fix quality and the antenna offset to §11 and §12 (see [people/WOBBLES.md](people/WOBBLES.md)).
- No wheel odometry or second IMU (D3). If added, each needs a frame, a topic in §11 and a TF ownership decision in §2.

## 8. Open items before v1.0

- **[verify]** Wrapper topic names, frame names, and parameter names on the pinned tag.
- **[verify]** IMU publish rate available on the camera model.
- Fill §4 observed behaviour (F6), §5 measurements (P10), §6 classes.
- Final grid size, cell size, and wall thresholds after G2.
- Confirm with the algorithm team that two `OccupancyGrid` topics are enough, or whether they want a multi-layer `grid_map` instead (stretch goal).

## 9. Persistent map (Phase 4, draft, not part of v1.0)

Added after the October 30 handoff by Phase 4 (tasks M1–M6). Nothing in v1.0 depends on it. Final names and the TF owner of `map → odom` depend on decision M1; see [PLAN.md](PLAN.md#phase-4-mapping-after-g3-from-nov-2-end-date-to-be-set).

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
    - both come from [`contract/rover_geometry.yaml`](contract/rover_geometry.yaml).
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

## 11. Recorded topics

`record_session.sh` (task R1) records this fixed list to rosbag2 in **MCAP** format, plus an SVO of the same run. Topic definitions are in §1. Only `/rover/...` names are used; the launch file remaps wrapper names.

| Group | Topics | Needed for |
| --- | --- | --- |
| Camera | `/rover/camera/rgb/image`, `/rover/camera/rgb/camera_info`, `/rover/camera/depth/image`, `/rover/camera/depth/camera_info` | Phase 2 perception replay |
| IMU | `/rover/imu` | F3 IMU checks, P3 gravity direction |
| Pose | `/rover/odom`, `/rover/pose` | Phase 2 grid placement, F5 fusion report |
| Transforms | `/tf`, `/tf_static` | everything |
| Tracking status | `/rover/tracking/status` | F6 failure table, P8 health |
| Diagnostics | `/diagnostics` | sensor-health evidence |
| Perception (handoff bags only, H3) | `/rover/perception/*`, `/rover/status/ok` | algorithm team |

The SVO keeps the raw stereo pair so a session can be re-processed with different depth or tracking settings. The bag keeps exactly what ROS saw. Keep both whenever possible.

## 12. Session folder and manifest

Every recording is a **session** with a stable id. Sessions are stored **outside Git**. A shared index lists their paths and checksums (task R4).

**Session id.** Proposed form: `<YYYY-MM-DD>_<ref>_<short-name>`, for example `2026-10-08_b_hallway-loop`. `<ref>` is the reference-session letter (a)–(e) from §13, or `x` for ad-hoc recordings.

```text
sessions/<session_id>/
  manifest.json        # fields below; written by scripts/write_manifest.py (R2)
  recording.svo        # ZED SVO of the run (extension .svo or .svo2 depending on SDK, [verify])
  bag/                 # rosbag2 folder, MCAP storage, topic list from §11
  trajectory.tum       # optional: ZED pose export, TUM format (timestamp tx ty tz qx qy qz qw)
  notes.md             # optional: free-text observations from the person recording
```

Frame dumps made from a session (interface I3, task R5) live separately under `frames/<session_id>/`; their format is in [PLAN.md](PLAN.md#i3-frame-dump-format-phase-3-writes-phase-2-and-4-read). Early sessions recorded with legacy `main.py --save-svo` before ROS is ready have no `bag/`; their manifest sets `"bag": null`.

### Manifest fields

| Field | Content | Filled by |
| --- | --- | --- |
| `schema_version` | Version of this contract, for example `"1.0"` | R2 |
| `session_id`, `reference_session` | Id (above) and letter `a`–`e` or `x` | R2 |
| `camera` | Model, serial or anonymised device id, resolution, FPS, depth mode | R2 from the SDK |
| `intrinsics` | `fx, fy, cx, cy, width, height` of the rectified left image (= depth image) | R2 from the SDK |
| `conventions` | Units, axes, timestamp source and invalid-depth encoding as in §0 | R2 (constant) |
| `static_transforms` | Measured `base_link → zed_camera_link` (translation m, rotation quaternion) | F1 |
| `tracking` | IMU fusion on/off, area memory on/off, area-map file used if any | R2 from parameters |
| `files` | Path and SHA-256 checksum of the SVO and bag folder; `null` if absent | R2 |
| `time` | `start_t_ns`, `end_t_ns`, `duration_s` | R2 |
| `software` | OS, JetPack/CUDA, ZED SDK, wrapper tag, ROS distro, Python, git commit | S6 table + R2 |
| `calibration_version` | Factory calibration id, or our calibration id if we ever recalibrate | R2 |
| `availability` | `imu`, `gps` (always `false` this milestone) | R2 |
| `tracking_timeline` | Intervals of tracking state (OK, SEARCHING, LOST, …) with `t_ns` | R2 from the status topic |
| `route` | Route description, environment, lighting, start/end floor marks | person recording |
| `failure_events` | Known events: `type`, `start_t_ns`, `end_t_ns`, note (for example the lens-cover in session e) | person recording + F6 |

Done-when for R2: a generated manifest validates against [`contract/session_manifest.example.json`](contract/session_manifest.example.json) and its checksums match the files.

## 13. Reference sessions

From task R4. Each is about 2–5 minutes. Every F and P test should be runnable from these without the rover.

| Ref | Content | Used by |
| --- | --- | --- |
| a | Static | F3 static IMU test, F5 static drift, P3 floor mislabel check |
| b | Hallway loop back to a floor mark | F5 closed loop, P4/P5 hallway labels, Phase 4 |
| c | Cluttered room with boxes and chairs | P5 obstacles, P7 object distances, Phase 4 |
| d | Fast turns and shaking | F5 fusion on vs off |
| e | Deliberate lens cover | F6 failure table, P8 health flip |

Handoff bags (H3) re-record (b), (c) and (e) with all output topics.
