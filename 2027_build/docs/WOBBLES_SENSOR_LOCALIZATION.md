# Data Synthesis: ZED, IMU, GPS, and Session Evidence

Branch: `wobbles-sensor-localization`

## Start here: the simple version

This responsibility makes the rover's sensor data trustworthy and turns recorded or synthetic observations into reusable session evidence. The first question is: **“When the camera says it moved, what exactly moved, in which coordinate frame, at what time, and can we replay the evidence?”**

Do a short shared measurement preflight, then make **IMU integration and validation the first substantive data-synthesis milestone**. The preflight verifies the camera stream, timestamps, and `base_link -> camera_link -> imu_link` geometry needed to interpret IMU data; it is not a prolonged camera-only feature phase. GPS remains last because it is a slow/noisy global correction, not a replacement for local camera motion. Read `FOUNDATIONS.md` before this plan; its TF diagram is the contract this work protects.

### Vocabulary before implementation

- **Frame:** a named coordinate system attached to the map, rover body, camera, or IMU.
- **TF:** ROS 2's time-aware record of how frames relate. For example, a fixed `base_link -> camera_link` transform says where the camera is bolted onto the rover.
- **Odometry:** smooth short-term motion estimate. It drifts over time.
- **Localization:** a global correction that says where the rover is in a known map/world.
- **Covariance:** the sensor's stated uncertainty; a GPS fix without meaningful covariance is not enough for safe fusion.
- **rosbag2 / SVO:** recordings for ROS messages / ZED camera data respectively. Keep both when possible because they serve different replay needs.

## Mission

Make sensor data reliable, time-aware, replayable, and correctly framed. Establish a measured IMU-assisted local-localization baseline first, compare it against the existing camera-only baseline, and only later add GPS-supported outdoor global localization.

## Scope

### Shared measurement preflight

- Verify one camera/IMU recording path (live or SVO replay), timestamp convention, frame ids, and the physical `base_link -> camera_link -> imu_link` geometry.
- Record one replayable session and a minimal manifest so matched comparisons are possible.
- Do not expand this into a separate camera-only implementation phase; VSLAM and integration begin their independent work immediately.

### First substantive stage: IMU integration and validation

- Publish and record the ZED IMU with its frame and timing documented.
- Characterize stationary bias/noise, vibration, axis orientation, and data rate.
- Compare camera-only tracking with ZED IMU-fused tracking on the same route.
- Decide whether an additional `robot_localization` filter is warranted only after documenting real additional sensors, such as wheel odometry or an external IMU.

### Integration stage

- Stabilize the session manifest and sensor-topic/TF contract with VSLAM and integration.
- Provide one replayable IMU-qualified session for their end-to-end integration checks.
- Agree on the single owner of `map -> odom` before handing localization to the external costmap/planning team or combining a global-localization stack.

### GPS stage

- Integrate the GPS driver and record `NavSatFix`, covariance, timestamp, fix quality, and antenna frame offset.
- Establish an absolute-heading plan before accepting GPS navigation results.
- Compare ZED GNSS fusion with `robot_localization` + `navsat_transform`; select one final owner of global localization rather than publishing duplicate `map -> odom` transforms.
- Validate outdoor repeat routes, global-frame jumps, and recovery after poor GNSS visibility.

## Deliverables

- Jazzy installation/setup record: Ubuntu, ROS, ZED SDK, CUDA/NVIDIA driver, wrapper revision, and camera model.
- Launch/config files for camera-only, IMU, and GPS modes.
- TF diagram and `view_frames` artifact for each mode.
- Session manifest generator and capture/replay instructions.
- Sensor-health report from `/diagnostics` plus tracking/fix status summaries.
- Camera-only vs IMU-fused vs GPS-assisted trajectory comparison.

## Code changes owned by data synthesis

Create `2027_build/src/rover_localization/` and `2027_build/src/rover_bringup/` as needed. Expected artifacts:

- ZED wrapper parameter overlays; do not edit upstream wrapper files.
- Rover URDF/xacro fragment defining base, camera, IMU, and later GPS frames.
- launch files for live ZED, SVO replay, IMU/GPS logging, and RViz validation.
- session-manifest/logging node or script.
- optional localization configs only after the TF ownership decision is documented.

The existing `main.py` may receive narrowly scoped export improvements: timestamped IMU CSV, tracking status/confidence, calibration JSON, and explicit tracking-gap records. Preserve its current standalone behavior.

## Reference docs: what to use and when

- [ZED ROS 2 overview](https://docs.stereolabs.com/docs/integrations/ros-2): start here for the Jazzy installation/build path, wrapper packages, SVO replay, and the camera data products that can be published.
- [ZED Stereo Node topic reference](https://docs.stereolabs.com/docs/integrations/ros-2/zed-stereo-node): use it to confirm exact topic names, message types, frames, and publication settings instead of guessing from examples.
- [ZED positional tracking in ROS 2](https://docs.stereolabs.com/docs/integrations/ros-2/positional-tracking): use this before configuring tracking, `odom`, `pose`, tracking confidence, area maps, or `map -> odom` behavior.
- [ZED robot integration](https://docs.stereolabs.com/docs/integrations/ros-2/robot-integration): use it while creating the rover URDF/xacro and deciding whether ZED tracking or an external filter owns a transform.
- [ZED Geo Tracking](https://docs.stereolabs.com/docs/integrations/ros-2/geo-tracking): read only in the GPS stage. It explains the accepted `NavSatFix` input and the ZED GNSS-fusion results.
- [ROS 2 rosbag2 documentation](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data.html): use it to record/replay the ROS message evidence that complements an SVO.
- [Nav2 GPS localization](https://docs.nav2.org/rolling/tutorials/general_tutorials/navigation2_with_gps/navigation2_with_gps/): use it to compare ZED GNSS fusion with `robot_localization` plus `navsat_transform`; pay special attention to covariance, heading, and the single-owner TF rule.

## Acceptance checks

- No TF edge has more than one publisher.
- Every sensor message has the expected frame and monotonic timestamp.
- Recorded SVO/bag replay reproduces the relevant topic set without hardware.
- The short measurement preflight is complete before IMU results are interpreted.
- IMU benefits are demonstrated on matched runs, not assumed.
- GPS is not declared navigation-ready without covariance/fix-quality and heading evidence.

## First independent milestone

After the shared preflight, use a Jazzy-supported ZED wrapper configuration with an SVO or live camera to publish/record the IMU, characterize it, and show a matched camera-only versus IMU-fused trajectory comparison. Record one complete manifest. This can be done without VSLAM or integration code.

## Agent prompts by phase

These are copy-paste prompts for an AI coding agent (or a teammate) working on this responsibility, in the phase order from [TIMELINE.md](TIMELINE.md). Each prompt has a due date and lists anything it waits on. The dates and sync meetings come from [TIMELINE.md](TIMELINE.md#key-dates-and-sync-meetings-october-2026-milestone). A prompt marked **not this month** conflicts with the October plan in [`docs2/`](../../docs2/README.md); its date is set at the Oct 30 review. Start each prompt with the shared preamble below.

> **Preamble.** You are working in the `autonomous_navigation` repo. Before writing code, read `2027_build/docs/FOUNDATIONS.md`, `SUBTEAM_SCOPE.md`, `CODE_CHANGE_OWNERSHIP.md`, and `2027_build/docs/WOBBLES_SENSOR_LOCALIZATION.md`. Work on branch `wobbles-sensor-localization`. Until Oct 30, 2026, `docs2/` is the working plan: Ubuntu 22.04 / ROS 2 Humble, the ZED wrapper owns `map -> odom` and `odom -> base_link` (decision D4), `main.py` stays untouched (D8), and topic names follow `docs2/OUTPUT_CONTRACT.md`. After that, the long-term target is Ubuntu 24.04 / Jazzy. Rules: exactly one component owns each TF edge (`map -> odom -> base_link -> camera_link -> imu_link`); no costmaps, planners, controllers, or motor commands; keep SVO, bags, and large outputs out of Git. If a fact is not in the docs or the data, write "to be decided" instead of inventing it.

### Phase 1: shared measurement preflight (all three, due C0 Mon Oct 12)

1. **Preflight checklist.** "Write a preflight script and checklist that verifies the ZED stream opens (live or SVO), the timestamp convention, the frame ids, and the measured `base_link -> camera_link -> imu_link` geometry. Record one replayable session with a minimal `manifest.json` that matches `docs/contract/session_manifest.example.json`. Output a pass/fail report."
2. **Freeze the manifest schema.** "Compare `docs/contract/SENSOR_DATA_CONTRACT.md`, the manifest example, and the 'Shared data handoff' list in `2027_build/docs/README.md`. Propose one JSON Schema for the session manifest and a validator with tests. List every field where the docs disagree." *All three agree on it at C0; everyone's loaders and fixtures build against it.*

### Phase 2: parallel work (IMU first, due G1 Fri Oct 16)

Wobbles is on the critical path: the other two switch from stand-ins to real data only after G1. Wobbles also gets the rover and camera first until G1 (docs2 schedule rule 2).

3. **Rover frames.** "Create a URDF/xacro fragment that defines `base_link`, `camera_link`, `imu_link`, and a placeholder GPS antenna frame. Use only measured offsets and put a TODO where a measurement is missing. Add a launch file that shows the frames in RViz and produces a `view_frames` PDF." *Do this in the same tape-measure session as Bedrawn's footprint (Bedrawn prompt 6).*
4. **ZED wrapper overlays.** "Write ZED ROS 2 wrapper parameter overlays (without editing upstream files) for two modes: camera-only and IMU-fused tracking. Use the ZED Stereo Node docs to list the exact topic names and message types for each mode." *Send the topic list to Bedrawn for the handoff contract (Bedrawn prompt 3).*
5. **IMU characterization.** "Write a script that reads a stationary IMU recording (rosbag2 or `imu.csv`) and reports bias, noise density, data rate, timestamp monotonicity, and axis orientation, with plots. Test it on synthetic IMU data with known bias and noise."
6. **Camera-only vs IMU-fused comparison.** "Build a matched-run comparison: given two TUM trajectories of the same route (camera-only and IMU-fused), report drift, discontinuities, tracking-loss gaps, and a top-down overlay plot. Draw the conclusion from the data; do not assume the IMU helps."
7. **Session recorder.** "Write a node or script that records a session folder: SVO plus rosbag2 with checksums, a manifest, `tracking_status.csv`, `imu.csv`, the calibration JSON, and labelled failure events. Add capture and replay instructions." *Hedgie and Bedrawn both consume these sessions after G1.*
8. **`main.py` narrow exports.** *Not this month:* docs2 decision D8 keeps `main.py` untouched, and the bag topics replace these exports. If it is reopened after Oct 30: "Add timestamped IMU CSV, tracking status/confidence, calibration JSON, and tracking-gap records to `main.py`'s outputs without changing its existing standalone behavior. Show a before/after run."

### Phase 3: bundle gate (G1 Fri Oct 16 to G2 Fri Oct 23)

9. **TF ownership check (due G1 Oct 16).** "Confirm with evidence that the ZED wrapper is the only publisher of `map -> odom` (docs2 D4), and record the area-memory on/off decision. Add a check that fails when any TF edge has more than one publisher during replay."
10. **Sensor health report (due G2 Oct 23).** "Summarize `/diagnostics`, tracking status, and IMU availability from a bag into a sensor-health report that the integration bundle can include." *Bedrawn needs it for the bundle (Bedrawn prompt 9).*
11. **Hand off a qualified session (due G1 Oct 16).** "Package one replayable, IMU-qualified session (manifest, bag, SVO reference, calibration) and confirm that the VSLAM loaders and the integration replay harness both accept it." *This unblocks Hedgie prompt 11 and Bedrawn prompt 8.*

### Phase 5: GPS (not this month; date set at the Oct 30 review)

12. **GPS fusion comparison.** "Record `NavSatFix` with covariance, fix quality, timestamp, and the antenna frame offset. On repeated outdoor routes, compare ZED GNSS fusion with `robot_localization` + `navsat_transform`. Report global-frame jumps, the source of absolute heading, and recovery after poor GNSS visibility. Do not call GPS navigation-ready without covariance, fix-quality, and heading evidence." *Hedgie prompt 13 and Bedrawn prompt 11 wait on this.*

Prompts 4 to 7 cover the [first independent milestone](#first-independent-milestone).
