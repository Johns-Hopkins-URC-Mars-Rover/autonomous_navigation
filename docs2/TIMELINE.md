# Timeline: October 7 – 31, 2026, then mapping

After a short bring-up, **Phases 1, 2 and 3 run at the same time**, starting Oct 10. Each one ends at its own gate. Phase 4 (mapping) starts after the Oct 30 handoff. Parallel work is possible because every phase's inputs and outputs are fixed in [PHASES.md](PHASES.md) and each input has a stand-in. A gate passes only when its checks pass on the real rover computer, or on recorded sessions where stated. Task IDs refer to [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md).

## At a glance

| Phase | Runs | Theme | Ends at |
| --- | --- | --- | --- |
| 0 | Wed Oct 7 – Fri Oct 9 | Stack installed, camera in ROS | **G0** Oct 9: camera + IMU visible in RViz on 22.04 / Humble |
| 1 | Sat Oct 10 → Fri Oct 16 | Fusion operational and measured | **G1** Oct 16: fused odometry and TF pass the acceptance tests |
| 2 | Sat Oct 10 → Fri Oct 23 | Local perception: free / wall / obstacle / unknown | **G2** Oct 23: labelled local grid correct on recorded sessions |
| 3 | Sat Oct 10 → Fri Oct 30 | Recording, stand-ins, one launch, handoff | **G3** Oct 30: live demo and handoff to the algorithm team |
| — | Sat Oct 31 | Buffer | Fixes only, no new features |
| 4 | From Mon Nov 2 (end date to be set) | Persistent map, saved and reloadable | **G4**: saved map reloads and lines up in a new session |

```text
            Oct 7  8  9 |10 11 12 13 14 15 16 |17 ... 23 |24 ... 30 |31 | Nov 2 →
Phase 0     ■■■■■■■■■■■ G0
Phase 1                 ■■■■■■■■■■■■■■■■■■■■■ G1
Phase 2                 ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ G2
Phase 3                 ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ G3
                              C0 (Mon Oct 12): interfaces frozen, stand-ins exist
Phase 4                                                               buffer  ■■■■■ → G4
```

## Shared checkpoint C0: Mon Oct 12

Not a gate, but everything parallel depends on it. C0 passes when:

- Topic names, frames, the frame-dump format and the `core/` signatures in [PHASES.md](PHASES.md) are agreed (H2 draft).
- Frame dumps of sessions (a) and (b) exist (R5).
- `fake_pose` and `fake_perception` publish the contract topics (R6).
- `fusion.launch.py`, `perception.launch.py` and `rover.launch.py` exist and build, even if mostly empty (S5).

## Phase 0: bring-up (Oct 7–9)

Work: S1–S5. In parallel, record reference sessions (a)–(e) as SVO with the legacy `main.py --save-svo` so Phases 2 and 3 can start without ROS (R4, early option).

**G0 passes when:**

- The rover computer reports Ubuntu 22.04 and sees the GPU.
- The ZED wrapper (pinned tag) launches and RGB, depth, and IMU appear in RViz.
- `ros2 topic hz` shows steady depth and IMU rates.
- At least sessions (a) and (b) exist as SVO files.

**If G0 slips:** the most likely cause is the OS/JetPack version (a Jetson on JetPack 5 is Ubuntu 20.04 and needs reflashing to JetPack 6). Fall back to an x86 Ubuntu 22.04 machine with an NVIDIA GPU for development and keep reflashing in parallel. Phase 2 `core/` work and Phase 3 frame dumps do not need ROS and continue regardless.

## Phase 1: fusion (Oct 10 → G1 Oct 16)

Work: S6, F1–F7.

**G1 passes when:**

- `view_frames` shows one connected TF tree with one publisher per edge (F1).
- The IMU checks pass: rate, gravity magnitude, axis signs, timestamps (F3, F4).
- Fusion-on vs fusion-off comparison is written up with numbers and meets the odometry targets (F5).
- The failure behaviour of odometry and TF is documented for the lens-cover, blank-wall, dark, and fast-spin cases (F6).
- The area-memory decision is recorded (F7).

**This is the "sensor fusion fully operational" gate.** After G1, Phase 1 people move to P8 (health), P10 (performance) and H5 (soak test).

## Phase 2: perception (Oct 10 → G2 Oct 23)

Work: P1–P8 and P10, with H4 (unit tests) alongside. Until G1 and the ROS bags exist, P2–P5 run on frame dumps and P1, P6, P7 run on the wrapper's default output or `fake_pose`.

**G2 passes when (on recorded sessions):**

- Grid, class grid, scan, and objects publish at target rates from bag replay (P4–P7).
- On the hallway session, walls are labelled wall, the floor is free, and areas behind walls are unknown (P4, P5).
- On the cluttered-room session, boxes and chairs are labelled obstacle; YOLO objects are within 10% of measured distance (P5, P7).
- Lens-cover replay flips the health signal (P8).
- Unit tests pass (H4).

## Phase 3: recording and integration (Oct 10 → G3 Oct 30)

Work: R1–R6 first, then P9, H1, H2, H3, H5, H6.

**Checkpoints on the way:**

- C0 Oct 12: frame dumps and stand-ins exist (R5, R6).
- G1 Oct 16: ROS bags of sessions (a)–(e) recorded and replayable, with manifests (R1–R4).
- G2 Oct 23: `rover.launch.py` runs Phases 1 + 2 from a bag, and RViz shows every output (H1 draft, P9).

**G3 passes when:**

- One launch command brings everything up on the rover in under 60 s (H1).
- All rate and latency targets are met with everything running on the rover computer (P10).
- The 10-minute live soak test passes (H5).
- [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) v1.0 is frozen with no **[verify]** items left (H2).
- The algorithm team replays the handoff bags on their own machine and sees every output (H3).
- Live demo: the rover is pushed or driven manually through a hallway and a cluttered area while RViz shows pose, labelled grid, scan, objects, and health (H6).

## Phase 4: mapping (from Nov 2)

Work: M1–M6. Exact dates are set at the G3 demo, together with the algorithm team's November requests.

**G4 passes when:**

- A map of the hallway + cluttered-room route is saved, then reloaded in a new session, and lines up with the live local grid within a stated tolerance (M4, M5).
- Walls and obstacles keep their labels in the saved map (M2).
- A relocalization jump does not smear or duplicate walls (M3).
- The map topics and saved-map format are frozen in [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) §9 (M6).

## Rules for the schedule

1. **Build against the contract, not against each other.** Use the stand-ins in [PHASES.md](PHASES.md) until the real producer passes its gate. Changing an interface after C0 needs agreement from the consuming phase.
2. **Fusion problems come first.** If G1 is not met, fixing it takes priority over new perception features; Phase 2 keeps going on recordings meanwhile.
3. **Record once, test many times.** Every algorithm change is checked on the reference sessions before a live test.
4. **Cut scope, not quality.** If time runs short, drop in this order: YOLO objects (P7), confidence layer (part of P5), area memory (F7 decision = off, which pushes Phase 4 later). Never drop the health signal or the "unseen is unknown" rule.
5. **No motor commands** are part of any gate. The rover is pushed or driven manually by a person.
6. Any change to topic names, frames, or label codes after G2 needs a contract version bump and a message to the algorithm team.
7. **Phase 4 does not start before G3.** It must not take people away from the Oct 30 handoff.

## Biggest risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Rover computer is not on Ubuntu 22.04 (for example JetPack 5) | Phase 0 slips by days | Develop on an x86 22.04 machine; reflash in parallel |
| SDK, CUDA, and wrapper versions do not match | Wrapper fails to build or crashes | Pin the wrapper tag to the SDK major version; record versions (S6) |
| Interfaces change after C0 | Parallel work has to be redone | Freeze at C0; stand-ins publish exactly the contract names; changes go through the consuming phase |
| Not enough compute for depth + tracking + YOLO + grid | Rates miss targets | Lower resolution or frame rate, lighter depth mode, YOLO at a lower rate or off (P10) |
| Indoor scenes with blank walls or poor light | Tracking loss | IMU fusion, failure documentation (F6), health signal (P8) |
| Reflective or dark floors give bad depth | False obstacles or holes | Confidence threshold, "unseen is unknown" rule, test in the real environment early |
| Area memory turned off for the demo (F7) | No consistent `map` frame for Phase 4 | Phase 4 starts with M1 re-testing area memory; option B or C in [PHASES.md](PHASES.md) as fallback |
