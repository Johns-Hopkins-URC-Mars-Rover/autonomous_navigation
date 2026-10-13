# Sensor Data Contract

This file defines the conventions every sensor recording and replay follows: units, axes, timestamps, invalid depth, frames, and the session folder format. It serves the October 2026 milestone in [`docs2/`](../../docs2/README.md) (Ubuntu 22.04, ROS 2 Humble) and carries over the session and evidence rules from [`2027_build/docs/`](../../2027_build/docs/README.md), restated for the docs2 phases.

- Perception outputs for the algorithm team are defined in [`docs2/OUTPUT_CONTRACT.md`](../../docs2/OUTPUT_CONTRACT.md), which builds on §1 here.
- An example manifest is [`session_manifest.example.json`](session_manifest.example.json).
- How the 2027_build plan maps onto the docs2 phases is in [README.md](README.md).

**Owner:** Phase 3 (recording and integration), tasks R1, R2 and R5. Phase 1 supplies the measured mount (F1) and the version table (S6). **Frozen at checkpoint C0 (Mon Oct 12)**, like every other interface in [`docs2/PHASES.md`](../../docs2/PHASES.md). Changes after C0 need agreement from the consuming phase.

Items marked **[verify]** depend on the pinned ZED SDK / wrapper release or the camera model. Confirm them on the real setup.

---

## 1. Units, axes, timestamps, invalid depth

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
2. **One clock.** IMU and image stamps come from the same clock (task F4). Stamps never go backwards within a session (acceptance target: none in a 10-minute run).
3. **Replay uses recorded time.** Bags play with `ros2 bag play --clock` and every node runs with `use_sim_time:=true` (task R3). SVO replay through the wrapper uses the SVO's own timestamps.
4. **Manifest times** (`start_t_ns`, `end_t_ns`, failure events) use the same clock as the recorded stamps.

### Invalid depth

Depth images are `float32`, metres, registered to the rectified left image (ROS encoding `32FC1`). Invalid pixels are kept exactly as the ZED SDK gives them and are **never** replaced with 0 or a max range:

| Value | Meaning (ZED SDK convention, **[verify]** on the pinned SDK) |
| --- | --- |
| `NaN` | No measurement (occlusion, no texture, low confidence) |
| `+inf` | Beyond the maximum depth range |
| `-inf` | Closer than the minimum depth range |

Consumers decide how to treat these. The rule that applies everywhere (docs2 decision D7): **missing depth never means free space.**

---

## 2. Frames and TF ownership

```text
map → odom → base_link → zed_camera_link → … → zed_left_camera_frame → left optical frame
                                         └→ zed_imu_link
```

This is the docs2 form of the 2027_build chain `map -> odom -> base_link -> camera_link -> imu_link`. `zed_camera_link` and `zed_imu_link` are the ZED wrapper's names for `camera_link` and `imu_link`.

| Edge | Single publisher | Source |
| --- | --- | --- |
| `map → odom` | ZED wrapper (area memory) | docs2 decision D4 |
| `odom → base_link` | ZED wrapper (visual-inertial tracking) | D4 |
| `base_link → zed_camera_link` | `robot_state_publisher` from `rover_description` | measured mount, task F1 |
| `zed_camera_link → camera/IMU frames` | ZED wrapper / ZED xacro (factory calibration) | not duplicated in our URDF |

- `base_link` is at floor level under the rover's turning centre.
- **One publisher per edge.** No `robot_localization`, `slam_toolbox`, AMCL or GPS filter may also publish `map → odom` (2027_build rule; docs2 D3, D4). Phase 4 option B would change this and must revise D4 first.
- Every recorded session stores the static `base_link → zed_camera_link` transform in its manifest (§4), so recordings stay interpretable if the mount changes later.
- **The mount is a placeholder for now.** The rover is still changing, so its values come from [`rover_geometry.yaml`](rover_geometry.yaml) (dummy, `placeholder: true`). A session recorded with the dummy mount says so in its manifest. When the real mount is measured, old sessions can be re-processed by swapping the transform; no algorithm changes. Algorithms must work for any mount (see `docs2/OUTPUT_CONTRACT.md` §10).

---

## 3. Recorded topics

`record_session.sh` (task R1) records this fixed list to rosbag2 in **MCAP** format, plus an SVO of the same run. Topic definitions (types, frames, rates) are in [`docs2/OUTPUT_CONTRACT.md`](../../docs2/OUTPUT_CONTRACT.md) §1. Only `/rover/...` names are used; the launch file remaps wrapper names.

| Group | Topics | Needed for |
| --- | --- | --- |
| Camera | `/rover/camera/rgb/image`, `/rover/camera/rgb/camera_info`, `/rover/camera/depth/image`, `/rover/camera/depth/camera_info` | Phase 2 perception replay |
| IMU | `/rover/imu` | F3 IMU checks, P3 gravity direction |
| Pose | `/rover/odom`, `/rover/pose` | Phase 2 grid placement, F5 fusion report |
| Transforms | `/tf`, `/tf_static` | everything |
| Tracking status | `/rover/tracking/status`, remapped from the wrapper's tracking-status topic (message type **[placeholder]** until the pinned tag is checked) | F6 failure table, P8 health |
| Diagnostics | `/diagnostics` | sensor-health evidence |
| Perception (handoff bags only, H3) | `/rover/perception/*`, `/rover/status/ok` | algorithm team |

The SVO keeps the raw stereo pair so a session can be re-processed with different depth or tracking settings. The bag keeps exactly what ROS saw. Keep both whenever possible (2027_build rule).

---

## 4. Session folder and manifest

Every recording is a **session** with a stable id. Sessions are stored **outside Git**. A shared index lists their paths and checksums (task R4).

### Session id

Proposed form: `<YYYY-MM-DD>_<ref>_<short-name>`, for example `2026-10-08_b_hallway-loop`. `<ref>` is the reference-session letter (a)–(e) from task R4, or `x` for ad-hoc recordings.

### Folder layout

```text
sessions/<session_id>/
  manifest.json        # §4 fields below; written by scripts/write_manifest.py (R2)
  recording.svo        # ZED SVO of the run (extension .svo or .svo2 depending on SDK, [verify])
  bag/                 # rosbag2 folder, MCAP storage, topic list from §3
  trajectory.tum       # optional: ZED pose export, TUM format (timestamp tx ty tz qx qy qz qw)
  notes.md             # optional: free-text observations from the person recording
```

Frame dumps made from a session (interface I3, task R5) live separately under `frames/<session_id>/`. Their format is defined in [`docs2/PHASES.md`](../../docs2/PHASES.md) ("I3 frame-dump format") and follows §1 of this file.

Early sessions recorded with legacy `main.py --save-svo` before ROS is ready have no `bag/`. Their manifest sets `"bag": null`.

### Manifest fields

The minimum set comes from the 2027_build "shared data handoff" list. The bag folder and reference-session fields were added for docs2.

| Field | Content | Filled by |
| --- | --- | --- |
| `schema_version` | Version of this contract, for example `"1.0"` | R2 |
| `session_id`, `reference_session` | Id (above) and letter `a`–`e` or `x` | R2 |
| `camera` | Model, serial or anonymised device id, resolution, FPS, depth mode | R2 from the SDK |
| `intrinsics` | `fx, fy, cx, cy, width, height` of the rectified left image (= depth image) | R2 from the SDK |
| `conventions` | Units, axes, timestamp source and invalid-depth encoding as in §1 | R2 (constant) |
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

Done-when for R2: a generated manifest validates against [`session_manifest.example.json`](session_manifest.example.json) and its checksums match the files.

---

## 5. Reference sessions

From task R4. Each is about 2–5 minutes. Every F and P test should be runnable from these without the rover.

| Ref | Content | Used by |
| --- | --- | --- |
| a | Static | F3 static IMU test, F5 static drift, P3 floor mislabel check |
| b | Hallway loop back to a floor mark | F5 closed loop, P4/P5 hallway labels, Phase 4 |
| c | Cluttered room with boxes and chairs | P5 obstacles, P7 object distances, Phase 4 |
| d | Fast turns and shaking | F5 fusion on vs off |
| e | Deliberate lens cover | F6 failure table, P8 health flip |

Handoff bags (H3) re-record (b), (c) and (e) with all output topics.

---

## 6. Evidence rule

Carried over from 2027_build `FOUNDATIONS.md`: a replay, a plot, or a YOLO box is evidence that one component ran, not evidence that navigation is safe. Every result (fusion report, perception check, map) records the session id, the software versions, and the parameters it used, so anyone can reproduce it from the session folder alone.

## 7. Not covered yet

- **GPS.** Not part of this milestone (docs2 out-of-scope list). When it returns, add `NavSatFix` with covariance, fix quality and the antenna offset to §3 and §4, as described in 2027_build `WOBBLES_SENSOR_LOCALIZATION.md`.
- **Wheel odometry or a second IMU.** Not present (docs2 D3). If added, they need a frame, a topic in §3 and a TF ownership decision in §2.
