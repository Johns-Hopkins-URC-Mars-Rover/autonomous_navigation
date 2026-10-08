# Hedgie: Offline Visual SLAM and Semantic Mapping

Branch: `hedgie-slam-research`

## Start here: the simple version

Hedgie receives recordings after someone else captures them. The job is to answer: **“Can we turn these camera/depth recordings into a more accurate, better explained map and trajectory than the raw ZED baseline?”** Hedgie begins its visual-only benchmark in parallel with Wobbles' IMU work, then consumes an IMU-qualified session at the integration gate.

This is not live camera setup or ROS plumbing. It is computer vision research using files: images, depth maps, camera calibration, and an initial ZED trajectory. The work begins with a dependable measurement baseline, then progresses to feature matching, loop closure, pose-graph optimization, dense maps, and semantic/dynamic-scene filtering.

Read `FOUNDATIONS.md` first, then the Inputs section below. Do not start with learned models; first make the ZED-baseline experiment reproduce from one session folder.

## Mission

Create the research-grade, camera-data-driven part of the project: an offline visual SLAM and semantic mapping pipeline that is quantitatively compared to the existing ZED trajectory baseline. This work must be useful even before live ROS 2 integration is complete.

Hedgie consumes prepared recordings and metadata. Hedgie is **not** responsible for plugging in the ZED, configuring a live ROS 2 camera node, debugging TF, or operating GPS hardware. Light ROS 2 familiarity is useful for reading bags and eventually publishing an offline map, but the main work is CV, 3D geometry, SLAM, and experiment design.

## Inputs and independence

Start with a small checked-in example manifest or a local session folder. The expected logical inputs are:

```text
session/
  manifest.json
  recording.svo OR rgb/ + depth/
  intrinsics.yaml
  zed_baseline.tum
  tracking_status.csv
  imu.csv              # optional for the visual-only benchmark; used at integration
  gps.csv              # optional until the GPS stage
```

Build loaders so the analysis can run from extracted files, not only from a live camera. If real recordings are unavailable, use a public RGB-D dataset or synthetic sequence strictly as a development fixture and label it as such.

### Vocabulary before implementation

- **Intrinsics:** the camera's focal length and optical center; needed to turn depth pixels into 3D points.
- **Trajectory:** the estimated camera path over time.
- **Feature match:** evidence that a visual point in one frame is the same physical point in another frame.
- **Loop closure:** evidence that the rover has returned to a previously seen place; it corrects accumulated drift.
- **Pose graph:** a network of poses and motion/loop constraints optimized together to make the path globally consistent.
- **Dense map:** many 3D points, rather than only sparse visual features.
- **BEV occupancy:** a top-down grid whose cells mean free, occupied, unknown, and optionally uncertain.

## Deliverables

### 1. Reproducible VSLAM benchmark

- Dataset/session manifest validator.
- A baseline report using the existing ZED TUM trajectory.
- Route-level metrics: tracked-frame fraction, trajectory discontinuities, path repeatability, relocalization events, runtime, and map coverage.
- A single command that regenerates an experiment output folder from a session.

### 2. Offline SLAM pipeline

Implement progressively, keeping a working baseline at every step:

1. RGB-D frame selection and calibration-aware back-projection.
2. Feature matching baseline (ORB or equivalent) and geometric verification.
3. Learned local-feature comparison such as SuperPoint/LightGlue only if hardware/runtime permits.
4. Place recognition / loop-closure candidates using global descriptors.
5. Geometric loop-closure verification and pose-graph optimization.
6. Dense colored point cloud or surfel-style map from optimized poses.

Do not claim that a learned method improves navigation until it has been evaluated on the same recorded routes as the ZED baseline.

### 3. Semantic and dynamic-scene mapping

- Reuse detections or segmentation masks to mark potentially dynamic objects.
- Prevent dynamic pixels/points from being used as stable SLAM landmarks when evidence supports that decision.
- Build a local bird's-eye-view representation with at least: free, occupied, unknown, and confidence.
- Compare depth-only geometry against geometry plus semantic/dynamic masking.

This is the research contribution most likely to improve map quality in real rover scenes: moving people, vehicles, and visually repetitive terrain should not become permanent map structure without confidence checks.

### 4. Later sensor research

When Wobbles provides a synchronized, IMU-qualified session at the integration gate, compare visual-only and visual-inertial trajectories under fast motion, texture-poor areas, and turns. This is a comparison against the independently completed visual baseline, not a prerequisite for starting it. When GPS exists, use it as a sparse global constraint in the offline pose graph and test cross-session relocalization. GPS must not be treated as high-rate local motion.

## Required outputs

```text
outputs/<session_id>/<experiment_id>/
  trajectory.tum
  trajectory_quality.json
  loop_closures.json
  pose_graph.g2o
  dense_map.ply
  bev_occupancy.*
  metrics.json
  report.md
```

Each output must record its input session id, calibration id, code revision, model/checkpoint id, and parameters.

## Acceptance checks

- Same input session and configuration reproduce the same result or explicitly document nondeterminism.
- Every loop closure has visual/geometric evidence retained for review.
- The method is compared against the ZED baseline, not judged only by qualitative screenshots.
- Dynamic masking never silently removes the only evidence of a real static obstacle; report its false-removal cases.
- Outputs are usable without ROS 2. An optional later exporter may write `PointCloud2` or `OccupancyGrid` for Bedrawn's handoff bundle and the external costmap/planning team.

## Code changes owned by Hedgie

Create new code only under `2027_build/src/rover_camera_ai/` or an equivalent research package. Initial modules should include:

- `session_io/`: manifest validation, RGB-D/trajectory readers, coordinate checks;
- `slam/`: feature front-end, matching, loop closure, pose graph;
- `mapping/`: back-projection, dense map, BEV occupancy/confidence;
- `evaluation/`: trajectory/map metrics and comparison plots;
- `tests/`: synthetic geometry and regression fixtures.

Hedgie may factor reusable, camera-independent detector utilities out of `object_detection.py` into the new package. Do not change `main.py` to run the research pipeline live and do not introduce a dependency on a live ZED or Nav2 while establishing the offline benchmark.

## Reference docs: what to use and when

- [ZED SVO recording and replay](https://docs.stereolabs.com/docs/recording/): consult when writing the session reader. Confirm exactly which data can be replayed through the SDK and which metadata must be preserved separately.
- [ZED camera calibration](https://www.stereolabs.com/docs/camera-calibration/): consult before back-projecting depth pixels; verify intrinsics, resolution dependence, and the coordinate convention rather than copying constants.
- [ZED positional tracking](https://www.stereolabs.com/docs/positional-tracking/): use it to interpret the supplied ZED trajectory, area-map relocalization, and tracking-state gaps. It provides the baseline to beat, not ground truth.
- [evo trajectory-format documentation](https://github.com/MichaelGrupp/evo/wiki/Formats#tum---tum-rgb-d-dataset-trajectory-format): use it when reading/writing the repository's TUM trajectory. Check timestamp units, quaternion ordering, and frame alignment before comparing trajectories.
- [OpenCV camera calibration and 3D reconstruction documentation](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html): use it for geometric verification, projection/back-projection, epipolar constraints, and pose estimation. Do not add a learned matcher before understanding the geometric checks it still needs.
- [Open3D documentation](https://www.open3d.org/docs/release/): optional but useful for point-cloud visualization, registration, and map review after the file-format/geometry baseline works.

## First independent milestone

Given one session folder, generate a validated baseline report, render the ZED trajectory, produce a depth-back-projected point cloud, and save a reviewable BEV occupancy/confidence image. This does not require anyone else's branch to merge.
