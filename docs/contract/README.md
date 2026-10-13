# docs/contract: sensor data contract and 2027_build crosswalk

| File | What it is |
| --- | --- |
| [SENSOR_DATA_CONTRACT.md](SENSOR_DATA_CONTRACT.md) | Units, axes, timestamps, invalid depth (§1), frames (§2), recorded topics (§3), session folder and manifest (§4), reference sessions (§5) |
| [session_manifest.example.json](session_manifest.example.json) | Example manifest that task R2's writer validates against |
| This README | How the longer-term plan in [`2027_build/docs/`](../../2027_build/docs/README.md) maps onto the October plan in [`docs2/`](../../docs2/README.md) |

`docs2/` replaces `2027_build/docs/` **for the October 2026 milestone only** ([docs2 README](../../docs2/README.md)). The tables below show where each 2027_build item went, using docs2's phases (0–4) and task IDs from [`docs2/WORK_BREAKDOWN.md`](../../docs2/WORK_BREAKDOWN.md).

Status key: **Kept** = same idea, now a docs2 task. **Changed** = kept but reshaped. **Later** = deferred past Oct 30 or to a stretch goal. **Out** = out of scope this milestone. **Gap** = in 2027_build, not yet in docs2.

## Platform and structure

| 2027_build item | docs2 equivalent | Phase / task | Status |
| --- | --- | --- | --- |
| Ubuntu 24.04 + ROS 2 Jazzy | Ubuntu 22.04 + ROS 2 Humble (decision D1) | 0 / S1–S4 | Changed |
| Jazzy setup record (OS, SDK, CUDA, wrapper, camera) | Pinned version table | 1 / S6 | Kept |
| Packages `rover_camera_ai`, `rover_localization`, `rover_navigation_inputs`, `rover_bringup` | `rover_description`, `rover_bringup`, `rover_perception`, `rover_mapping` | 0 / S5 | Changed |
| "Package conversion" gate after integration | Packages exist from day one; logic lives in `core/` without ROS | 0 / S5 | Changed |
| Lanes per person (Wobbles, Hedgie, Bedrawn) | Owners not assigned yet; work split by phase | all | Changed |
| Legacy prototype stays runnable | Decision D8: `main.py` untouched, fallback recorder | all | Kept |
| `pipeline.svg` | Still describes the 2027_build plan; not regenerated for docs2 | — | Not updated |

## Data synthesis and sensor evidence (Wobbles) → mostly Phases 1 and 3

| 2027_build item | docs2 equivalent | Phase / task | Status |
| --- | --- | --- | --- |
| Shared measurement preflight: camera stream, clock, frames, one recording | Bring-up + mount + timing | 0 / S1–S5, 1 / F1, F4 | Kept |
| IMU publish/record, bias, noise, axes, rate | IMU validation | 1 / F3 | Kept |
| Camera-only vs IMU-fused on matched runs | Fusion on vs off on the same SVO | 1 / F5 | Kept |
| Rover URDF/xacro with base, camera, IMU frames | `rover_description` | 1 / F1 | Kept |
| ZED parameter overlays, no upstream edits | `zed_overrides.yaml` | 1 / F2 | Kept |
| Session manifest generator | Manifest writer + this contract §4 | 3 / R2 | Kept |
| SVO + rosbag2 capture/replay | Record script, replay path | 3 / R1, R3 | Kept |
| Sensor-health report from `/diagnostics` | Health signal | 2 / P8 | Changed (now a live output) |
| `robot_localization` only with extra sensors | Decision D3 | — | Kept |
| Single owner of `map → odom` | Decision D4 (ZED wrapper), area-memory decision | 1 / F7 | Kept |
| `main.py` exports (IMU CSV, tracking status, calibration JSON) | Replaced by the bag topics (§3) and frame dumps from SVO | 3 / R1, R5 | Changed |
| GPS stage (`NavSatFix`, heading, `navsat_transform`) | — | — | Out |

## VSLAM and map research (Hedgie) → narrowed to Phases 2 and 4

| 2027_build item | docs2 equivalent | Phase / task | Status |
| --- | --- | --- | --- |
| Session-folder input that runs without ROS | Frame dumps (interface I3) | 3 / R5 | Changed |
| Baseline report on the ZED TUM trajectory, `evo` metrics | Fusion report with `evo` trajectory plots | 1 / F5 | Kept |
| RGB-D back-projection | Depth → 3D points | 2 / P2 | Kept |
| BEV occupancy: free / occupied / unknown + confidence | Local grid + class grid + confidence | 2 / P4, P5 | Kept |
| Feature matching, learned features, loop closure, pose graph | — (ZED SDK does tracking and relocalization, D2) | — | Out |
| Dense colored point cloud / surfel map | Phase 4 option C (ZED spatial mapping) | 4 / M1 | Later |
| Semantic / dynamic-object masking | Temporal filtering of moving objects | stretch | Later |
| Visual vs visual-inertial comparison | Fusion on vs off | 1 / F5 | Kept |
| Cross-session relocalization | Save and reload map with ZED area map | 4 / M5 | Later |
| Experiment outputs record session id, code revision, parameters | Evidence rule, this contract §6 | all | Kept |

## Integration and handoff (Bedrawn) → Phases 2 and 3

| 2027_build item | docs2 equivalent | Phase / task | Status |
| --- | --- | --- | --- |
| Depth → `LaserScan` adapter | Obstacle points + scan | 2 / P6 | Kept |
| Obstacle semantics: frame, stamp, range, invalid data | `OUTPUT_CONTRACT.md` §1, §3, §4 | 3 / H2 | Kept |
| Handoff contract (type, topic, frame, rate) | `OUTPUT_CONTRACT.md` v1.0 | 3 / H2 | Kept |
| Synthetic source first, swap in real data later | Stand-ins `fake_pose`, `fake_perception` | 3 / R6 | Kept |
| Replay bundle + readme | Handoff bags + `HANDOFF_README` | 3 / H3 | Kept |
| Behaviour through tracking loss / relocalization | Failure table | 1 / F6, `OUTPUT_CONTRACT.md` §4 | Kept |
| Optional `OccupancyGrid` map context | Local grid now; persistent map in Phase 4 | 2 / P4, 4 / M4 | Kept + Later |
| QoS documented per topic | Not listed in `OUTPUT_CONTRACT.md` | — | **Gap** |
| Measured rover footprint and safety assumptions | Not in docs2 (F1 measures only the camera mount) | — | **Gap** |
| No costmap, planner, controller, motors | `OUTPUT_CONTRACT.md` §7, schedule rule 5 | — | Kept |

## Gaps to raise with the team

1. **Rover footprint.** 2027_build required measured footprint dimensions so the algorithm team can choose inflation. docs2 has no task for it. The natural place is F1 (same tape-measure session) with a row in `OUTPUT_CONTRACT.md`.
2. **QoS per topic.** 2027_build required it in the handoff contract. Add a QoS column to `OUTPUT_CONTRACT.md` §1 before v1.0 (H2), especially for latched map topics in Phase 4.
3. **`pipeline.svg`** still shows the 2027_build plan. Either mark it as the long-term view or generate a docs2 version with the same script approach.
