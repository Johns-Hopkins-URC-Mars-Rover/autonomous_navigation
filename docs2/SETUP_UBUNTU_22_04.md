# Setup: Ubuntu 22.04 + ROS 2 Humble + ZED

Tasks S1–S6 in [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md). Follow the linked official guides for exact install commands; they change between releases. This page says **what** to install, **which versions must match**, and **how to check** each step.

## 1. The stack

| Layer | Choice | Must match |
| --- | --- | --- |
| OS | Ubuntu 22.04 (x86) or JetPack 6.x (Jetson; Ubuntu 22.04 based) | — |
| GPU stack | NVIDIA driver + CUDA (x86), or the CUDA bundled with JetPack | ZED SDK installer |
| ROS 2 | Humble Hawksbill | Ubuntu 22.04 |
| ZED SDK | Current release for Ubuntu 22.04 / your CUDA, or for your L4T (JetPack) version | GPU stack |
| ZED ROS 2 wrapper | `zed-ros2-wrapper`, **pinned release tag** for the installed SDK major version, Humble | ZED SDK |
| Python | 3.10 (system Python on 22.04) | ROS 2 Humble |
| YOLO | `ultralytics` + `torch` (on Jetson, NVIDIA's JetPack 6 torch wheel first) | Python 3.10, CUDA |

A Jetson on JetPack 5.x is Ubuntu 20.04 and does **not** fit this plan; it needs reflashing to JetPack 6.

## 2. Install order and checks

| Step | Guide | Check that it worked |
| --- | --- | --- |
| 1. OS + GPU | Ubuntu 22.04 install or NVIDIA SDK Manager (JetPack 6) | `lsb_release -a` → 22.04; `nvidia-smi` (x86) or `tegrastats` (Jetson) |
| 2. ROS 2 Humble | [docs.ros.org/en/humble/Installation](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) — `ros-humble-desktop` on machines with a screen, `ros-humble-ros-base` on a headless rover | `ros2 run demo_nodes_cpp talker` and `listener` in two terminals |
| 3. ZED SDK | [stereolabs.com/developers/release](https://www.stereolabs.com/developers/release) — pick the Ubuntu 22.04 / CUDA or L4T build | `ZED_Diagnostic` passes; `python3 -c "import pyzed.sl"` works |
| 4. ZED ROS 2 wrapper | [github.com/stereolabs/zed-ros2-wrapper](https://github.com/stereolabs/zed-ros2-wrapper) README, checked out at a release tag | `ros2 launch zed_wrapper zed_camera.launch.py camera_model:=<model>` and topics appear in `ros2 topic list` |
| 5. Our packages | this repository, `2027_build/` | `colcon build` and `colcon test` succeed |

Building the wrapper (from its README; adjust the tag):

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone --branch <pinned-tag> https://github.com/stereolabs/zed-ros2-wrapper.git
cd ~/ros2_ws
sudo apt update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --cmake-args=-DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

Extra Humble packages this plan uses:

```bash
sudo apt install ros-humble-pointcloud-to-laserscan ros-humble-vision-msgs \
  ros-humble-robot-state-publisher ros-humble-xacro ros-humble-tf2-tools \
  ros-humble-rosbag2-storage-mcap
```

`evo` (trajectory comparison for task F5) installs with `pip install evo`.

## 3. Smoke tests after setup

Run these once the camera is plugged in. All should pass before gate G0.

```bash
# Camera and IMU topics exist and have steady rates
ros2 topic list | grep zed
ros2 topic hz /zed/zed_node/imu/data          # [verify] name on the pinned tag
ros2 topic hz /zed/zed_node/depth/depth_registered

# One connected TF tree
ros2 run tf2_tools view_frames                 # writes frames_<date>.pdf

# Record and replay
ros2 bag record -s mcap -o test_bag /zed/zed_node/imu/data /tf /tf_static
ros2 bag play test_bag --clock
```

Also check that the legacy prototype still runs on this machine: `python3 main.py --no-display --no-plot`.

## 4. Pinned versions (fill in during S6)

| Item | Version |
| --- | --- |
| Machine and OS | |
| JetPack / L4T (Jetson) | |
| NVIDIA driver / CUDA | |
| ZED SDK | |
| ZED camera model and firmware | |
| `zed-ros2-wrapper` tag | |
| ROS 2 Humble (`apt` version of `ros-humble-desktop`) | |
| Python | |
| `torch` / `ultralytics` | |

## 5. Fallbacks

- **No 22.04 rover computer yet:** develop on any x86 Ubuntu 22.04 machine with an NVIDIA GPU and replay SVO files through the wrapper.
- **Wrapper will not build:** check that the wrapper tag matches the SDK major version first; that is the most common cause.
- **Docker:** Stereolabs publishes ZED SDK + ROS 2 container images; usable if a host OS cannot be changed. **[verify]** a Humble image exists for your platform before relying on it.
