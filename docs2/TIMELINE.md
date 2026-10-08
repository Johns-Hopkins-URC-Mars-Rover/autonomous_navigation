# Timeline: October 7 – 31, 2026

Four short phases, each ending in a gate on a Friday. A gate passes only when its checks pass on the real rover computer (or on recorded sessions where stated). Task IDs refer to [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md).

## At a glance

| Phase | Dates | Theme | Gate (Friday) |
| --- | --- | --- | --- |
| 0 | Wed Oct 7 – Fri Oct 9 | Stack installed, camera in ROS | **G0** Oct 9: camera + IMU visible in RViz on 22.04 / Humble |
| 1 | Sat Oct 10 – Fri Oct 16 | Fusion operational and measured | **G1** Oct 16: fused odometry and TF pass the acceptance tests |
| 2 | Sat Oct 17 – Fri Oct 23 | Free / wall / obstacle perception | **G2** Oct 23: labelled grid correct on recorded sessions |
| 3 | Sat Oct 24 – Fri Oct 30 | One launch, hardening, handoff | **G3** Oct 30: live demo and handoff to the algorithm team |
| — | Sat Oct 31 | Buffer | Fixes only, no new features |

## Phase 0: bring-up (Oct 7–9)

Work: S1, S2, S3, S4, S5 started. In parallel, record reference sessions (a)–(e) as SVO with the legacy `main.py --save-svo` so perception work is not blocked (R4, early option).

**G0 passes when:**

- The rover computer reports Ubuntu 22.04 and sees the GPU.
- The ZED wrapper (pinned tag) launches and RGB, depth, and IMU appear in RViz.
- `ros2 topic hz` shows steady depth and IMU rates.
- At least sessions (a) and (b) exist as SVO files.

**If G0 slips:** the most likely cause is the OS/JetPack version (a Jetson on JetPack 5 is Ubuntu 20.04 and needs reflashing to JetPack 6). Fall back to an x86 Ubuntu 22.04 machine with an NVIDIA GPU for development and keep reflashing in parallel. Do not move on to Phase 1 work that needs live ROS topics until a 22.04 machine runs the wrapper.

## Phase 1: fusion operational (Oct 10–16)

Work: S6, F1–F7, R1–R4. Perception `core/` development (P2–P4) starts on the SVO sessions.

**G1 passes when:**

- `view_frames` shows one connected TF tree with one publisher per edge (F1).
- The IMU checks pass: rate, gravity magnitude, axis signs, timestamps (F3, F4).
- Fusion-on vs fusion-off comparison is written up with numbers and meets the odometry targets (F5).
- The failure behaviour of odometry and TF is documented for the lens-cover, blank-wall, dark, and fast-spin cases (F6).
- Record → replay works with rosbag2 and with SVO (R1–R3).

**This is the "sensor fusion fully operational" gate.** If it fails, Phase 2 still continues on recordings, but fixing G1 takes priority over new perception features.

## Phase 2: perception (Oct 17–23)

Work: P1–P8, H4 (unit tests alongside).

**G2 passes when (on recorded sessions):**

- Grid, class grid, scan, and objects publish at target rates from bag replay (P4–P7).
- On the hallway session, walls are labelled wall, the floor is free, and areas behind walls are unknown (P4, P5).
- On the cluttered-room session, boxes and chairs are labelled obstacle; YOLO objects are within 10% of measured distance (P5, P7).
- Lens-cover replay flips the health signal (P8).
- Unit tests pass (H4).

## Phase 3: integration and handoff (Oct 24–30)

Work: P9, P10, H1, H2, H3, H5, H6.

**G3 passes when:**

- One launch command brings everything up on the rover in under 60 s (H1).
- All rate and latency targets are met with everything running on the rover computer (P10).
- The 10-minute live soak test passes (H5).
- [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) v1.0 is frozen with no **[verify]** items left (H2).
- The algorithm team replays the handoff bags on their own machine and sees every output (H3).
- Live demo: the rover is pushed or driven manually through a hallway and a cluttered area while RViz shows pose, labelled grid, scan, objects, and health (H6).

## Rules for the schedule

1. **Fusion before features.** If G1 is not met, fix it before adding perception features.
2. **Record once, test many times.** Every algorithm change is checked on the reference sessions before a live test.
3. **Cut scope, not quality.** If time runs short, drop in this order: YOLO objects (P7), confidence layer (part of P5), area memory (F7 decision = off). Never drop the health signal or the "unseen is unknown" rule.
4. **No motor commands** are part of any gate. The rover is pushed or driven manually by a person.
5. Any change to topic names, frames, or label codes after G2 needs a contract version bump and a message to the algorithm team.

## Biggest risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Rover computer is not on Ubuntu 22.04 (for example JetPack 5) | Phase 0 slips by days | Develop on an x86 22.04 machine; reflash in parallel |
| SDK, CUDA, and wrapper versions do not match | Wrapper fails to build or crashes | Pin the wrapper tag to the SDK major version; record versions (S6) |
| Not enough compute for depth + tracking + YOLO + grid | Rates miss targets | Lower resolution or frame rate, lighter depth mode, YOLO at a lower rate or off (P10) |
| Indoor scenes with blank walls or poor light | Tracking loss | IMU fusion, failure documentation (F6), health signal (P8) |
| Reflective or dark floors give bad depth | False obstacles or holes | Confidence threshold, "unseen is unknown" rule, test in the real environment early |
