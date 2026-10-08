# Wobbles: ZED, IMU, GPS, and Localization Data Contract

Branch: `wobbles-sensor-localization`

## Start here: the simple version

Wobbles makes the rover's sensor data trustworthy. The first question is: **“When the camera says it moved, what exactly moved, in which coordinate frame, at what time, and can we replay the evidence?”**

Do a short shared measurement preflight, then make **IMU integration and validation the first substantive Wobbles milestone**. The preflight verifies the camera stream, timestamps, and `base_link -> camera_link -> imu_link` geometry needed to interpret IMU data; it is not a prolonged camera-only feature phase. GPS remains last because it is a slow/noisy global correction, not a replacement for local camera motion. Read `FOUNDATIONS.md` before this plan; its TF diagram is the contract this work protects.

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
- Do not expand this into a separate camera-only implementation phase; Hedgie and Bedrawn begin their independent work immediately.

### First substantive stage: IMU integration and validation

- Publish and record the ZED IMU with its frame and timing documented.
- Characterize stationary bias/noise, vibration, axis orientation, and data rate.
- Compare camera-only tracking with ZED IMU-fused tracking on the same route.
- Decide whether an additional `robot_localization` filter is warranted only after documenting real additional sensors, such as wheel odometry or an external IMU.

### Integration stage

- Stabilize the session manifest and sensor-topic/TF contract with Hedgie and Bedrawn.
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

## Code changes owned by Wobbles

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

After the shared preflight, use a Jazzy-supported ZED wrapper configuration with an SVO or live camera to publish/record the IMU, characterize it, and show a matched camera-only versus IMU-fused trajectory comparison. Record one complete manifest. This can be done without Hedgie's or Bedrawn's code.
