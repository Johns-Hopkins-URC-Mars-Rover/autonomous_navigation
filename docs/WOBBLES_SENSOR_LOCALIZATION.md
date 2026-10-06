# Wobbles: ZED, IMU, GPS, and Localization Data Contract

Branch: `wobbles-sensor-localization`

## Mission

Make sensor data reliable, time-aware, replayable, and correctly framed. Build the path from camera-only localization to IMU-assisted localization and finally GPS-supported outdoor global localization.

## Scope

### Camera-only stage

- Move the live data path to Ubuntu 24.04 / ROS 2 Jazzy using the official ZED ROS 2 wrapper.
- Publish/validate rectified RGB, registered depth, point cloud, camera info, odometry, pose, and diagnostics.
- Create the physical `base_link -> camera_link` static transform from measured mounting geometry.
- Record matching SVO and rosbag2 sessions plus the shared manifest.
- Verify timestamps, frame ids, image/depth alignment, point-cloud registration, and tracking status.

### IMU stage

- Publish and record the ZED IMU with its frame and timing documented.
- Characterize stationary bias/noise, vibration, axis orientation, and data rate.
- Compare camera-only tracking with ZED IMU-fused tracking on the same route.
- Decide whether an additional `robot_localization` filter is warranted only after documenting real additional sensors, such as wheel odometry or an external IMU.

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

## Acceptance checks

- No TF edge has more than one publisher.
- Every sensor message has the expected frame and monotonic timestamp.
- Recorded SVO/bag replay reproduces the relevant topic set without hardware.
- The camera-only path works before IMU work is considered complete.
- IMU benefits are demonstrated on matched runs, not assumed.
- GPS is not declared navigation-ready without covariance/fix-quality and heading evidence.

## First independent milestone

Use a Jazzy-supported ZED wrapper configuration with an SVO or live camera to show RGB, depth, point cloud, odometry/pose, and diagnostics in RViz, then write one complete manifest. This can be done without Hedgie's or Bedrawn's code.
