# Autonomous Navigation Pipeline — Full Documentation

---

## Table of Contents

1. [Read This First](#read-this-first)
2. [Overview](#overview)
3. [Project Structure](#project-structure)
4. [Architecture](#architecture)
5. [Installation & Dependencies](#installation--dependencies)
6. [Quick Start](#quick-start)
7. [CLI Reference — `main.py`](#cli-reference--mainpy)
8. [Module Reference](#module-reference)
   - [main.py](#mainpy)
   - [object_detection.py](#object_detectionpy)
   - [slam/zed_vo_core.py](#slamzed_vo_corepy)
   - [slam/zed_scene_core.py](#slamzed_scene_corepy)
9. [Data Structures](#data-structures)
10. [Configuration & Tuning](#configuration--tuning)
11. [Outputs & Saved Files](#outputs--saved-files)
12. [Display Window Layout](#display-window-layout)
13. [Coordinate System](#coordinate-system)
14. [Platform Notes (Jetson / Headless)](#platform-notes-jetson--headless)
15. [Standalone Modes](#standalone-modes)
16. [Limitations](#limitations)

---

## Read This First

This is the detailed reference for the **existing standalone Python camera prototype**. Read `docs/FOUNDATIONS.md` first if terms such as VIO, TUM trajectory, area map, TF, occupancy grid, or Nav2 are new.

In plain language, the current program can watch through a ZED camera, estimate the camera's movement, use the camera IMU to help that estimate, save a replayable ZED recording, save the estimated path, and draw object/depth hints. That is a strong perception/localization baseline. It is **not** yet a complete autonomous-navigation system: it does not publish ROS 2 topics, produce a Nav2 occupancy map/costmap, plan a route, command motors, or establish GPS localization.

Read this document in this order:

1. Overview and Architecture: what runs once per camera frame.
2. Quick Start and Outputs: how to run/replay it and what files it creates.
3. Coordinate System and Limitations: what the numbers mean and when not to trust them.
4. Module Reference and Configuration: implementation detail only when changing code.

## Overview

This pipeline fuses three capabilities into a single, real-time loop driven by a Stereolabs ZED stereo camera:

- **Visual Odometry (VO)** — ZED estimates the camera's 6-DoF pose (position plus orientation) from images; on IMU-equipped cameras it also fuses accelerometer/gyroscope information. This is local motion estimation, not a guaranteed global map.
- **Scene Understanding** — wall/hallway detection via depth-grid variance voting, forward line-of-sight probing, and morphological object clustering.
- **Object Detection** — YOLOv8 model inference on each camera frame; detected targets get labelled bounding boxes and distance estimates from the depth map, rendered alongside the scene and VO overlays.

All three share a single `sl.Camera` handle and a single `zed.grab()` call per frame. The ZED SDK, VO math, scene analysis, and YOLO inference are cleanly separated so each module can be tested or replaced independently.

### What the saved artifacts mean

- **SVO:** replayable ZED camera recording; use it to reproduce camera-side behavior without hardware.
- **TUM trajectory:** timestamped pose estimate used by trajectory tools. It is a baseline estimate, not ground truth.
- **ZED area map:** private ZED visual-memory data that helps the ZED tracker revisit a prior area. It is not a Nav2 2D occupancy map.
- **YOLO/depth result:** a perception hint. It does not itself stop the rover or create an obstacle costmap.

---

## Project Structure

```
autonomous_navigation/
│
├── main.py                    ← unified entry point (run this)
├── object_detection.py        ← YOLO model loading, inference, overlay
├── DOCS.md                    ← this file
├── requirements.txt           ← pip dependencies (ZED SDK + torch installed separately)
│
├── models/
│   ├── best.pt                ← primary YOLOv8 model weights (Git LFS)
│   └── best_bw.pt             ← secondary / greyscale model weights (Git LFS)
│
└── slam/
    ├── zed_vo_core.py         ← VO data structures, tracking, smoothing, plotting
    └── zed_scene_core.py      ← scene analysis, depth processing, visualisation
```

The `slam/` modules never call the YOLO model. `object_detection.py` never opens a camera. `main.py` is the only file that wires all three together.

---

## Architecture

```
main.py  ←  single entry point, owns sl.Camera handle
│
├── pyzed.sl                   ← ZED SDK Python bindings
│
├── slam/zed_vo_core.py        ← all VO logic (no camera, no YOLO)
│   ├── NavState               — per-frame navigation snapshot dataclass
│   ├── DisplacementTracker    — accumulates path statistics
│   ├── EMASmoothing           — velocity smoothing
│   ├── rotation_matrix_to_euler
│   ├── smooth_trajectory      (Savitzky-Golay)
│   ├── LivePlotter            — real-time matplotlib window
│   └── save_analysis_plots    — post-session figure suite
│
├── slam/zed_scene_core.py     ← all scene-understanding logic (no camera, no YOLO)
│   ├── SceneConfig / Config   — tuneable parameter class
│   ├── WallInfo, HallwayInfo, LOSObject, SceneState
│   ├── preprocess_depth       — NaN-fill, range clamp
│   ├── detect_walls           — grid-cell flatness voting
│   ├── detect_hallway         — corridor geometry inference
│   ├── probe_line_of_sight    — centre-patch median probe
│   ├── find_forward_clusters  — connected-component object detection
│   ├── draw_scene_overlay     — OpenCV HUD rendering
│   └── colorise_depth         — JET/Turbo depth colourmap panel
│
└── object_detection.py        ← YOLO model loading and inference (no camera, no SLAM)
    ├── DetectionConfig        — model paths, confidence/IoU thresholds, display options
    ├── DetectionResult        — per-frame result dataclass
    ├── ObjectDetector         — loads model, runs inference, draws overlays
    └── draw_detection_overlay — burns labelled YOLO boxes + depth onto frame
```

---

## Installation & Dependencies

### ZED SDK

Download and install from [stereolabs.com/developers/release](https://www.stereolabs.com/developers/release/). The SDK version must match the camera firmware. `pyzed` is installed automatically by the SDK installer — do **not** install it from PyPI.

### Python packages

Install PyTorch first, for your platform:

- **Desktop:** `pip install torch torchvision`
- **Jetson:** use NVIDIA's JetPack-specific wheels. A plain `pip install torch` gives a CPU-only build.

Then install the rest:

```bash
pip install -r requirements.txt
```

### Model weights

The weights are stored with [Git LFS](https://git-lfs.com). After cloning, run `git lfs install && git lfs pull` if `models/*.pt` are small text pointer files.

Place your trained weights in `models/`:

```
models/best.pt       ← primary model
models/best_bw.pt    ← optional secondary / greyscale model
```

`main.py` defaults to `models/best.pt`. Override with `--model`.

---

## Quick Start

```bash
# Live camera — all features enabled
python main.py

# Replay a recorded SVO file
python main.py --svo recording.svo

# Use a specific model
python main.py --model models/best_bw.pt

# Headless (no OpenCV windows) — suitable for Jetson without a display
python main.py --no-display --no-plot

# Record session to SVO while running
python main.py --save-svo output.svo

# Relocalise into (and update) a named area map
python main.py --area-map maps/rover_yard.area

# HD1080 at 60 FPS, 2-D trajectory view
python main.py --resolution HD1080 --fps 60 --view-2d

# First-generation ZED (no IMU)
python main.py --no-imu

# Disable object detection (SLAM + scene only)
python main.py --no-detection

# Tune detection confidence
python main.py --conf 0.4 --iou 0.5
```

Press **Q** or **ESC** in any OpenCV window to stop.

---

## CLI Reference — `main.py`

### Input / Output

| Flag | Default | Description |
|---|---|---|
| `--svo PATH` | None | SVO file for replay. Omit to use the live camera. |
| `--save-svo PATH` | None | Record the live session to an SVO file (H.264). |
| `--area-map PATH` | `zed_area_map.area` | Area map to load at startup (if the file exists) and save on exit. A reloaded map puts the run in the same world frame as the earlier one. |
| `--no-area-map` | off | Don't load or save an area map. |

### Camera

| Flag | Default | Choices | Description |
|---|---|---|---|
| `--resolution MODE` | `HD720` | `HD2K`, `HD1080`, `HD720`, `VGA` | Camera resolution. |
| `--fps N` | `30` | — | Target framerate. |

### Object Detection

| Flag | Default | Description |
|---|---|---|
| `--model PATH` | `models/best.pt` | Path to YOLOv8 `.pt` weights file. |
| `--conf F` | `0.35` | Minimum confidence threshold for a detection to be reported. |
| `--iou F` | `0.45` | IoU threshold for NMS duplicate suppression. |
| `--no-detection` | off | Disable YOLO inference entirely (SLAM + scene only). |

### Display / Plotting

| Flag | Default | Description |
|---|---|---|
| `--no-display` | off | Disable all OpenCV windows. |
| `--no-plot` | off | Disable matplotlib live and post-session trajectory windows. |
| `--view-2d` | off | Top-down (X–Y) trajectory view instead of 3-D. |
| `--plot-interval N` | `10` | Refresh live trajectory plot every N frames. |

### VO Smoothing

| Flag | Default | Description |
|---|---|---|
| `--ema-alpha A` | `0.7` | EMA factor for velocity smoothing. Range `[0, 1]`. |
| `--savgol-window W` | `11` | Savitzky-Golay window for post-run plots (odd). |
| `--savgol-poly P` | `3` | Savitzky-Golay polynomial order. |
| `--speed-window N` | `10` | Rolling window size for smoothed speed estimate. |

### IMU

| Flag | Default | Description |
|---|---|---|
| `--no-imu` | off | Skip IMU retrieval. Use on ZED gen-1 cameras. |

### Verbosity

| Flag | Default | Description |
|---|---|---|
| `--verbose-interval N` | `10` | Print combined state to stdout every N frames. |

---

## Module Reference

### `main.py`

The unified entry point. Owns the `sl.Camera` handle from open to close. Imports from `slam/` and `object_detection.py`.

**`run(args)`** — The main loop. Each frame:

1. `zed.grab(runtime)` — acquire frame.
2. Retrieve left image and depth map (shared by all three pipelines).
3. VO pipeline: query 6-DoF pose → `pose.get_rotation_matrix()` → compute velocity → update `DisplacementTracker` → pack `NavState`. When tracking is not `OK`, the velocity reference and EMA are reset, so a relocalisation jump doesn't show up as a speed spike.
4. Scene pipeline: `preprocess_depth` → `detect_walls` → `detect_hallway` → `probe_line_of_sight` → `find_forward_clusters`.
5. Detection pipeline (if enabled): `ObjectDetector.run(frame_bgr, depth_raw)` → `DetectionResult`. Detection uses the raw depth (camera range up to 20 m), not the scene-clamped depth, so distant targets still get a distance.
6. Compose display: scene overlay → VO HUD → detection overlay → depth colourmap panel.
7. Every `--plot-interval` frames, refresh live matplotlib trajectory.

On exit: saves the area map, closes the camera, prints the session summary, and saves the trajectory file and analysis plots.

---

### `object_detection.py`

YOLO-based target detection. No ZED SDK calls. Operates entirely on NumPy arrays.

#### `DetectionConfig`

All tuneable detection parameters as class attributes:

| Parameter | Default | Description |
|---|---|---|
| `MODEL_PATH` | `"models/best.pt"` | Path to YOLOv8 `.pt` file. |
| `CONF_THRESH` | `0.35` | Minimum detection confidence. |
| `IOU_THRESH` | `0.45` | NMS IoU overlap threshold. |
| `DEPTH_SAMPLE_FRAC` | `0.3` | Fractional size of centre crop for depth sampling. |
| `BOX_COLOR_DEFAULT` | `(0, 200, 255)` | BGR colour for boxes whose class has no entry in `CLASS_COLORS`. |
| `CLASS_COLORS` | `{}` | Per-class BGR colours, keyed by class id. |
| `BOX_THICKNESS` | `2` | Bounding box line thickness in pixels. |
| `LABEL_FONT_SCALE` | `0.55` | Label text scale. |
| `SHOW_CONF` | `True` | Whether to include confidence score in label. |
| `SHOW_DEPTH` | `True` | Whether to include depth estimate in label. |

#### `DetectionResult`

Per-frame result dataclass:

| Field | Type | Description |
|---|---|---|
| `boxes` | `list[tuple]` | List of `(x1, y1, x2, y2, conf, class_id, label, depth_m)` per detection. |
| `count` | `int` | Number of detections this frame. |
| `frame_idx` | `int` | Frame counter. |
| `any_detected` | `bool` | True if `count > 0`. |

#### `ObjectDetector`

Wraps a YOLOv8 model loaded via `ultralytics`.

**Constructor:** `ObjectDetector(cfg: DetectionConfig)`

Loads the model from `cfg.MODEL_PATH` on construction. Raises `RuntimeError` if the file is missing.

**`run(frame_bgr, depth_clean, frame_idx) → DetectionResult`**

Runs YOLO inference on `frame_bgr`. For each detection above `CONF_THRESH`, samples the median depth from the centre crop of its bounding box in `depth_clean`. Returns a `DetectionResult`.

**`draw_overlay(frame, result, depth_clean, cfg) → np.ndarray`**

Draws labelled bounding boxes on a copy of `frame`. Each box includes the class label, confidence score (if `SHOW_CONF`), and depth estimate (if `SHOW_DEPTH`). Also renders a status panel below the image showing total detections and per-class counts.

---

### `slam/zed_vo_core.py`

Pure-Python VO helpers. No ZED SDK calls. Independently importable and testable.

#### `NavState`

Frozen-per-frame dataclass carrying every navigation quantity for one grab cycle:

| Field | Type | Description |
|---|---|---|
| `position` | `np.ndarray (3,)` | XYZ position in metres |
| `orientation` | `np.ndarray (3,)` | Roll, pitch, yaw in degrees |
| `rotation_matrix` | `np.ndarray (3,3)` | SO(3) rotation from ZED pose |
| `velocity` | `np.ndarray (3,)` | EMA-smoothed velocity in m/s |
| `speed` | `float` | Scalar speed in m/s |
| `cumulative_distance` | `float` | Total path length in metres |
| `net_displacement` | `float` | Straight-line distance from origin |
| `linearity_ratio` | `float` | `net / cumulative` — 1.0 = perfectly straight |
| `imu_available` | `bool` | True for ZED 2 / 2i / X |
| `linear_acceleration` | `np.ndarray (3,)` | m/s² from IMU |
| `angular_velocity` | `np.ndarray (3,)` | deg/s from IMU |
| `frame_idx` | `int` | Frame counter |
| `timestamp_s` | `float` | Camera timestamp in seconds |

#### `DisplacementTracker`

Accumulates pose updates and exposes navigation statistics.

```python
tracker = DisplacementTracker(speed_window=10)
stats   = tracker.update(pos, dt)   # call once per frame with tracking OK
tracker.mark_gap()                  # call when tracking is lost
summary = tracker.summary()         # call at end of session
```

`update()` returns a dict with keys: `step`, `step_mag`, `cumulative_distance`, `net_displacement`, `net_magnitude`, `smoothed_speed`, `linearity_ratio`.

`summary()` returns: `total_frames`, `total_path_length`, `final_net_magnitude`, `mean_speed`, `max_speed` (both in m/s), `linearity_ratio`.

#### `EMASmoothing`

Exponential Moving Average for `np.ndarray` velocity vectors.

```python
ema = EMASmoothing(alpha=0.7)
smoothed_velocity = ema.update(raw_velocity)
```

Higher `alpha` tracks more closely; lower `alpha` smooths more aggressively.

#### `smooth_trajectory(traj, window=11, poly=3) → np.ndarray`

Applies Savitzky-Golay smoothing independently to X, Y, Z columns of an `(N, 3)` trajectory. Window is auto-clamped to array length.

#### `rotation_matrix_to_euler(R) → np.ndarray`

Converts a 3×3 SO(3) rotation matrix to `[roll, pitch, yaw]` in degrees (ZYX convention, Z-up). Yaw is heading about +Z. Handles the gimbal-lock singularity (`sy < 1e-6`).

#### `LivePlotter`

Real-time matplotlib trajectory window.

```python
plotter = LivePlotter(view_3d=True)
plotter.update(traj, frame_idx, net_dist, savgol_w=11, savgol_p=3)
plotter.close()   # call at session end
```

#### `save_analysis_plots(tracker, savgol_w, savgol_p, view_3d)`

Saves two PNG files at session end:
- `zed_displacement_analysis.png` — 6-panel figure: position over time, per-frame step size, cumulative vs net distance, linearity ratio, XY top-down path, height (Z) over time.
- `zed_trajectory_plot.png` — full-resolution 3-D or 2-D trajectory with raw + smoothed overlays.

---

### `slam/zed_scene_core.py`

Scene understanding functions. No ZED SDK calls after data retrieval. Can also be run standalone.

#### `preprocess_depth(depth_np, cfg) → np.ndarray`

Replaces all non-finite values and values outside `[cfg.DEPTH_MIN_M, cfg.DEPTH_MAX_M]` with `NaN`. Returns a cleaned `float32` array.

#### `detect_walls(depth, cfg) → WallInfo`

Divides the depth image into a `GRID_ROWS × GRID_COLS` grid. Each cell is marked **flat** if its depth variance is below `WALL_VAR_THRESH` and mean depth is below `WALL_MEAN_MAX_M`. The grid is split into left, centre, and right thirds — a zone is classified as a wall if more than 40% of its cells are flat.

#### `detect_hallway(depth, walls, cfg) → HallwayInfo`

Computes mean depth of left, centre, and right vertical strips. Declares a hallway when both side strips are close, the centre is significantly deeper, and the depth ratio exceeds `HALLWAY_OPEN_RATIO`. Width is estimated by back-projecting the centre column of each side strip using the calibrated focal length (`SceneConfig.FX_PX`, set from the ZED calibration at startup).

#### `probe_line_of_sight(depth, cfg) → LOSObject`

Samples the centre rectangle of fractional size `LOS_WIDTH_FRAC × LOS_HEIGHT_FRAC`. Reports an object if median finite depth is below `LOS_OBJECT_MAX_M`.

#### `find_forward_clusters(depth, frame_bgr, cfg) → list[tuple]`

Thresholds depth at `CLUSTER_DEPTH_MAX_M`, dilates the binary mask, and runs connected components. Returns `(x, y, w, h, mean_depth)` tuples for each cluster larger than `CLUSTER_MIN_PIXELS`, sorted nearest-first.

#### `draw_scene_overlay(frame, depth, scene, clusters, cfg) → np.ndarray`

Composes the scene visualisation on a copy of `frame`:
- Semi-transparent orange tint over detected left/right wall zones.
- Blue tint over a detected front wall.
- Green (object detected) or grey (clear) rectangle for the LOS probe region.
- Cyan bounding boxes with distance labels per cluster.
- Dark status panel at the bottom with wall distances, hallway info, LOS status, cluster count.

#### `colorise_depth(depth, max_m) → np.ndarray`

Normalises depth to `[0, 255]` and applies `COLORMAP_TURBO`. Returns a BGR `uint8` array.

#### `SceneConfig`

All tuneable scene parameters as class attributes (see [Configuration & Tuning](#configuration--tuning) below).

---

## Data Structures

### `DetectionResult`

```python
@dataclass
class DetectionResult:
    boxes:        list   # [(x1, y1, x2, y2, conf, class_id, label, depth_m), ...]
    count:        int
    frame_idx:    int
    any_detected: bool
```

### `WallInfo`

| Field | Type | Description |
|---|---|---|
| `left_wall` | `bool` | Left zone classified as a wall |
| `right_wall` | `bool` | Right zone classified as a wall |
| `front_wall` | `bool` | Centre zone classified as a wall |
| `left_dist_m` | `float` | Mean depth of left zone in metres |
| `right_dist_m` | `float` | Mean depth of right zone in metres |
| `front_dist_m` | `float` | Mean depth of centre zone in metres |

### `HallwayInfo`

| Field | Type | Description |
|---|---|---|
| `detected` | `bool` | True when hallway criteria are met |
| `width_est_m` | `float` | Rough corridor width estimate in metres |
| `centre_open_m` | `float` | Mean depth of the open centre strip |

### `LOSObject`

| Field | Type | Description |
|---|---|---|
| `detected` | `bool` | True when median probe depth < `LOS_OBJECT_MAX_M` |
| `dist_m` | `float` | Median depth of the probe region in metres |
| `label` | `str` | Object label string |

### `SceneState`

```python
@dataclass
class SceneState:
    walls:     WallInfo
    hallway:   HallwayInfo
    los_obj:   LOSObject
    frame_idx: int
```

### `NavState`

See [slam/zed_vo_core.py](#slamzed_vo_corepy) above.

---

## Configuration & Tuning

### Object Detection (`DetectionConfig` in `object_detection.py`)

| Parameter | Default | Effect |
|---|---|---|
| `CONF_THRESH` | `0.35` | Lower = more detections (more false positives); higher = fewer (more misses). |
| `IOU_THRESH` | `0.45` | Controls how aggressively duplicate boxes are suppressed. |
| `DEPTH_SAMPLE_FRAC` | `0.3` | Fraction of the bounding box used for depth sampling. Reduce if objects overlap depth boundaries. |

### Scene Understanding (`SceneConfig` in `slam/zed_scene_core.py`)

| Parameter | Default | Effect |
|---|---|---|
| `DEPTH_MIN_M` | `0.3` | Ignore depth closer than this. Increase to reduce housing noise. |
| `DEPTH_MAX_M` | `8.0` | Ignore depth farther than this in scene analysis. Does not affect YOLO distance estimates. |
| `GRID_COLS` / `GRID_ROWS` | `12` / `8` | Finer grids catch smaller wall surfaces. |
| `WALL_VAR_THRESH` | `0.04` | Max depth variance (m²) for a flat cell. Increase for textured surfaces. |
| `WALL_MEAN_MAX_M` | `5.0` | Far walls beyond this are not classified. |
| `HALLWAY_SIDE_MAX_M` | `2.5` | Side walls must be closer than this. Increase for wider corridors. |
| `HALLWAY_CENTRE_MIN_M` | `1.2` | Minimum depth difference between centre and sides. |
| `HALLWAY_OPEN_RATIO` | `1.5` | Centre-to-side depth ratio. Reduce for narrower hallways. |
| `FX_PX` | `None` | Left-camera focal length in pixels. Set automatically from calibration. |
| `HFOV_FALLBACK_DEG` | `110.0` | Horizontal FOV used for the width estimate if `FX_PX` is unset. |
| `LOS_WIDTH_FRAC` / `LOS_HEIGHT_FRAC` | `0.15` | Fractional half-size of the LOS probe rectangle. |
| `LOS_OBJECT_MAX_M` | `4.0` | Report LOS object if median probe depth is below this. |
| `CLUSTER_DEPTH_MAX_M` | `4.0` | Only search for clusters within this range. |
| `CLUSTER_MIN_PIXELS` | `400` | Minimum cluster area in pixels. Increase to suppress noise. |
| `CLUSTER_DILATE_ITER` | `3` | Morphological dilation passes before clustering. |
| `OVERLAY_ALPHA` | `0.45` | Opacity of wall highlight overlays. |

### VO Smoothing (CLI flags)

| Flag | Default | Effect |
|---|---|---|
| `--ema-alpha` | `0.7` | Higher = more responsive velocity; lower = smoother. |
| `--savgol-window` | `11` | Larger window = smoother post-run trajectory. Must be odd. |
| `--savgol-poly` | `3` | Polynomial order for Savitzky-Golay (must be < window). |
| `--speed-window` | `10` | Longer window = more stable speed estimate. |

---

## Outputs & Saved Files

All files are written to the **working directory** at session end.

| File | Condition | Description |
|---|---|---|
| `zed_trajectory.txt` | Always (if frames > 0) | Trajectory in [TUM format](https://github.com/MichaelGrupp/evo/wiki/Formats#tum---tum-rgb-d-dataset-trajectory-format): `timestamp tx ty tz qx qy qz qw`, one row per tracked frame. Evaluate it with `evo`, e.g. `evo_traj tum zed_trajectory.txt --plot`. |
| `zed_area_map.area` | Unless `--no-area-map` | ZED area map, reloaded on the next run for relocalisation. |
| `zed_displacement_analysis.png` | Unless `--no-plot`, frames > 2 | 6-panel analysis figure. |
| `zed_trajectory_plot.png` | Unless `--no-plot`, frames > 2 | Full-resolution smoothed trajectory. |
| `<name>.svo` | Only with `--save-svo` | H.264-compressed SVO recording. |

Session summary always printed to stdout:

```
================================================================
NAVIGATION PIPELINE — SESSION SUMMARY
================================================================
Frames processed      : 1420
Total path length     : 18.3421 m
Net displacement      : 12.0034 m
Mean speed            : 0.3870 m/s
Max speed             : 1.4130 m/s
Linearity ratio       : 0.654  (1.0 = straight)
================================================================
```

---

## Display Window Layout

The combined OpenCV window shows three regions:

```
┌──────────────────────────────────────────┬────────────────────┐
│  Camera image                            │  Depth colourmap   │
│  ├─ VO HUD          (top-left)           │  (COLORMAP_TURBO)  │
│  ├─ YOLO boxes      (green/labelled)     │                    │
│  ├─ Wall highlights  (orange/blue tint)  │                    │
│  └─ Depth clusters  (cyan boxes)         │                    │
├──────────────────────────────────────────┤  (padded to match) │
│  Scene HUD panel                         │                    │
├──────────────────────────────────────────┤                    │
│  Detection HUD panel                     │                    │
└──────────────────────────────────────────┴────────────────────┘
```

**VO HUD** (top-left, semi-transparent): Position XYZ, Roll/Pitch/Yaw, speed, frame index, cumulative and net distance, IMU readings (ZED 2/2i/X only).

**YOLO boxes**: each detected target gets a bounding box coloured by class, labelled with class name, confidence, and depth estimate in metres.

**Wall highlights**: orange tint over left/right wall zones; blue tint over front wall zone.

**LOS probe**: green rectangle = object within threshold; grey = clear.

**Cluster boxes**: cyan rectangles with distance labels around morphological depth blobs.

**Scene HUD panel**: wall distances, hallway status, LOS distance, cluster count.

**Detection HUD panel**: total target count, per-class breakdown, frame index.

Press **Q** or **ESC** to quit cleanly.

---

## Coordinate System

The ZED SDK is configured with `RIGHT_HANDED_Z_UP_X_FWD`, the ROS convention (REP 103):

- **+X** → forward
- **+Y** → left
- **+Z** → up

The ground plane is X–Y and height is Z. Poses can be passed straight to ROS 2 / Nav2 without remapping axes.

All positions and distances are in **metres**. The origin is the camera's pose at session start (or SVO start).

---

## Platform Notes (Jetson / Headless)

**NVIDIA Jetson (JetPack 5 / 6):** Use `--no-plot` to skip matplotlib. Use `--no-display` for fully headless operation. Recommended minimum: Jetson Orin Nano with ZED 2i at HD720 30 FPS.

**Headless Linux:**

```bash
python main.py --no-display --no-plot
```

Trajectory and analysis files are still saved. Console output at `--verbose-interval` is the primary monitoring channel.

**SVO replay:** Frames are processed as fast as the host allows, not at original capture rate. Use live camera if real-time timing is required.

**ZED gen-1 (no IMU):** Pass `--no-imu` to suppress `get_sensors_data`. VO and scene understanding operate identically; IMU rows in the HUD display `"IMU: not available on ZED gen-1"`.

---

## Standalone Modes

**SLAM + scene only (no YOLO):**

```bash
python main.py --no-detection
```

**Scene understanding only (no VO, no YOLO):**

```bash
python slam/zed_scene_core.py
python slam/zed_scene_core.py --svo file.svo
python slam/zed_scene_core.py --no-display
```

This is useful for tuning `SceneConfig` parameters before integrating the full pipeline.

---

## Limitations

- Wall detection uses a flat-variance heuristic and assumes approximately fronto-parallel surfaces. Angled or highly textured walls may be missed.
- Hallway width is a rough estimate: it uses mean strip depth, so clutter in a side strip biases it.
- The LOS probe reports median depth of the probe region but does not classify object type — that role is now filled by the YOLO pipeline.
- Cluster detection is purely geometric; overlapping clusters at similar depths may merge into a single bounding box.
- YOLO depth estimates are sampled from the centre crop of each bounding box. Objects whose depth is partly occluded or at a range boundary may show inaccurate distance readings.
- Area memory (`enable_area_memory = True`) improves loop-closure but increases RAM. Disable in `main.py`:`_build_tracking_params()` if memory is constrained.
