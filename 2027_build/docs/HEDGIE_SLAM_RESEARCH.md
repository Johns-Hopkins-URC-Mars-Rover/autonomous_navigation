# VSLAM: Offline Visual SLAM and Semantic Mapping

Branch: `hedgie-slam-research`

## Start here: the simple version

This responsibility turns camera/depth sessions into trajectory and map evidence. The job is to answer: **“Can we turn these camera/depth recordings into a more accurate, better explained map and trajectory than the raw ZED baseline?”** It begins the visual-only benchmark in parallel with data-synthesis IMU work, then consumes an IMU-qualified session at the integration gate.

This is not live camera setup or ROS plumbing. It is computer vision research using files: images, depth maps, camera calibration, and an initial ZED trajectory. The work begins with a dependable measurement baseline, then progresses to feature matching, loop closure, pose-graph optimization, dense maps, and semantic/dynamic-scene filtering.

Read `FOUNDATIONS.md` first, then the Inputs section below. Do not start with learned models; first make the ZED-baseline experiment reproduce from one session folder.

## Mission

Create the research-grade, camera-data-driven part of the project: an offline visual SLAM and semantic mapping pipeline that is quantitatively compared to the existing ZED trajectory baseline. This work must be useful even before live ROS 2 integration is complete.

VSLAM consumes prepared recordings and metadata. It is **not** responsible for plugging in the ZED, configuring a live ROS 2 camera node, debugging TF, or operating GPS hardware. Light ROS 2 familiarity is useful for reading bags and eventually publishing an offline map, but the main work is CV, 3D geometry, SLAM, and experiment design.

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

When data synthesis provides a synchronized, IMU-qualified session at the integration gate, compare visual-only and visual-inertial trajectories under fast motion, texture-poor areas, and turns. This is a comparison against the independently completed visual baseline, not a prerequisite for starting it. When GPS exists, use it as a sparse global constraint in the offline pose graph and test cross-session relocalization. GPS must not be treated as high-rate local motion.

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
- Outputs are usable without ROS 2. An optional later exporter may write `PointCloud2` or `OccupancyGrid` for the integration handoff bundle and next subteam.

## Code changes owned by VSLAM

Create new code only under `2027_build/src/rover_camera_ai/` or an equivalent research package. Initial modules should include:

- `session_io/`: manifest validation, RGB-D/trajectory readers, coordinate checks;
- `slam/`: feature front-end, matching, loop closure, pose graph;
- `mapping/`: back-projection, dense map, BEV occupancy/confidence;
- `evaluation/`: trajectory/map metrics and comparison plots;
- `tests/`: synthetic geometry and regression fixtures.

VSLAM may factor reusable, camera-independent detector utilities out of `object_detection.py` into the new package. Do not change `main.py` to run the research pipeline live and do not introduce a dependency on a live ZED or Nav2 while establishing the offline benchmark.

## Reference docs: what to use and when

- [ZED SVO recording and replay](https://docs.stereolabs.com/docs/recording/): consult when writing the session reader. Confirm exactly which data can be replayed through the SDK and which metadata must be preserved separately.
- [ZED camera calibration](https://www.stereolabs.com/docs/camera-calibration/): consult before back-projecting depth pixels; verify intrinsics, resolution dependence, and the coordinate convention rather than copying constants.
- [ZED positional tracking](https://www.stereolabs.com/docs/positional-tracking/): use it to interpret the supplied ZED trajectory, area-map relocalization, and tracking-state gaps. It provides the baseline to beat, not ground truth.
- [evo trajectory-format documentation](https://github.com/MichaelGrupp/evo/wiki/Formats#tum---tum-rgb-d-dataset-trajectory-format): use it when reading/writing the repository's TUM trajectory. Check timestamp units, quaternion ordering, and frame alignment before comparing trajectories.
- [OpenCV camera calibration and 3D reconstruction documentation](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html): use it for geometric verification, projection/back-projection, epipolar constraints, and pose estimation. Do not add a learned matcher before understanding the geometric checks it still needs.
- [Open3D documentation](https://www.open3d.org/docs/release/): optional but useful for point-cloud visualization, registration, and map review after the file-format/geometry baseline works.

## First independent milestone

Given one session folder, generate a validated baseline report, render the ZED trajectory, produce a depth-back-projected point cloud, and save a reviewable BEV occupancy/confidence image. This does not require anyone else's branch to merge.

## Agent prompts by phase

These are copy-paste prompts for an AI coding agent (or a teammate) working on this responsibility, in the phase order from [TIMELINE.md](TIMELINE.md). Each prompt has a due date and lists anything it waits on. The dates and sync meetings come from [TIMELINE.md](TIMELINE.md#key-dates-and-sync-meetings-october-2026-milestone). A prompt marked **not this month** conflicts with the October plan in [`docs2/`](../../docs2/README.md); its date is set at the Oct 30 review. Start each prompt with the shared preamble below.

> **Preamble.** You are working in the `autonomous_navigation` repo. Before writing code, read `2027_build/docs/FOUNDATIONS.md`, `SUBTEAM_SCOPE.md`, `CODE_CHANGE_OWNERSHIP.md`, and `2027_build/docs/HEDGIE_SLAM_RESEARCH.md`. Work on branch `hedgie-slam-research`. Until Oct 30, 2026, `docs2/` is the working plan: Ubuntu 22.04 / ROS 2 Humble, the ZED wrapper owns `map -> odom` and `odom -> base_link` (decision D4), `main.py` stays untouched (D8), and topic names follow `docs2/OUTPUT_CONTRACT.md`. After that, the long-term target is Ubuntu 24.04 / Jazzy. Rules: exactly one component owns each TF edge (`map -> odom -> base_link -> camera_link -> imu_link`); no costmaps, planners, controllers, or motor commands; keep SVO, bags, and large outputs out of Git. If a fact is not in the docs or the data, write "to be decided" instead of inventing it.

### Phase 1: shared measurement preflight (all three, due C0 Mon Oct 12)

1. **Preflight checklist.** "Write a preflight script and checklist that verifies the ZED stream opens (live or SVO), the timestamp convention, the frame ids, and the measured `base_link -> camera_link -> imu_link` geometry. Record one replayable session with a minimal `manifest.json` that matches `docs/contract/session_manifest.example.json`. Output a pass/fail report."
2. **Freeze the manifest schema.** "Compare `docs/contract/SENSOR_DATA_CONTRACT.md`, the manifest example, and the 'Shared data handoff' list in `2027_build/docs/README.md`. Propose one JSON Schema for the session manifest and a validator with tests. List every field where the docs disagree." *All three agree on it at C0; everyone's loaders and fixtures build against it.*

### Phase 2: parallel work (visual-only baseline, due G2 Fri Oct 23)

Work on frame dumps and synthetic fixtures until G1 (Oct 16), then switch to Wobbles' recorded sessions. Nothing here needs the rover.

3. **Session IO.** "Create `2027_build/src/rover_camera_ai/session_io/` to validate and load a session folder (manifest, `rgb/` + `depth/` or SVO, `intrinsics.yaml`, `zed_baseline.tum`, `tracking_status.csv`). Add a synthetic fixture generator, clearly labelled as synthetic, so it works without a real recording." *Waits on: the manifest schema frozen at C0 (shared prompt 2).*
4. **Baseline benchmark.** "Write one command that takes a session and regenerates `outputs/<session_id>/<experiment_id>/` with a ZED-baseline report: tracked-frame fraction, discontinuities, relocalization events, runtime, and map coverage. Record the session id, calibration id, code revision, and parameters in `metrics.json`."
5. **Back-projection and BEV.** "Implement calibration-aware depth back-projection into a point cloud, and a BEV occupancy grid with free, occupied, unknown, and confidence. Test the geometry on a synthetic scene with known planes." *This is the docs2 local grid (P2, P4, P5), so it is checked at G2.*
6. **Feature front-end.** *Not this month* (research VSLAM is out of scope in docs2). "Implement an ORB matching baseline with geometric verification (essential matrix or PnP with RANSAC). Report inlier statistics. No learned features yet."
7. **Loop closure and pose graph.** *Not this month.* "Add place-recognition candidates, geometric loop verification, and pose-graph optimization that writes `pose_graph.g2o`. Keep the visual and geometric evidence for every accepted loop in `loop_closures.json`. Compare the optimized trajectory against the ZED baseline with evo."
8. **Dense map.** *Not this month; may become Phase 4 option C (from Nov 2).* "Build a dense colored map (`dense_map.ply`) from the optimized poses, plus a script that renders review images."
9. **Semantic/dynamic masking.** *Stretch goal, after G3 Oct 30.* "Move the camera-independent detector utilities out of `object_detection.py` into `rover_camera_ai`. Use the detections to keep likely-dynamic pixels out of SLAM landmarks and the BEV map. Compare depth-only and masked results, and report every case where masking removed a real static obstacle."
10. **Learned features (optional).** *Not this month.* "If runtime allows, compare SuperPoint/LightGlue against ORB on the same recorded routes. Claim an improvement only if the metrics show one."

### Phase 3: bundle gate (G1 Fri Oct 16 to G2 Fri Oct 23)

11. **Visual vs visual-inertial (start after G1 Oct 16, due G2 Oct 23).** "Using the IMU-qualified session from data synthesis, compare visual-only and visual-inertial trajectories on fast motion, turns, and low-texture segments." *Waits on: Wobbles prompt 11.*
12. **Map export for the handoff (due G2 Oct 23).** "Write an exporter from the BEV grid (and, later, the dense map) to `OccupancyGrid` / `PointCloud2`, with frame, resolution, confidence, and provenance metadata in the format the integration handoff contract expects." *Waits on: Bedrawn's contract draft (Bedrawn prompt 3). Bedrawn prompt 9 waits on this.*

### Phase 5: GPS (not this month; date set at the Oct 30 review)

13. **GPS as a sparse constraint.** "Add GPS as a sparse global constraint in the offline pose graph and test cross-session relocalization. Do not use GPS as high-rate local motion." *Waits on: Wobbles prompt 12 and prompt 7.*

Prompts 3 to 5 cover the [first independent milestone](#first-independent-milestone).
