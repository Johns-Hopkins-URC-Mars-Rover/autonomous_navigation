# Subteam Timeline: Data Synthesis, VSLAM, and Integration

The visual roadmap is [`pipeline.svg`](pipeline.svg). Its source of truth is [`scripts/generate_pipeline_svg.py`](scripts/generate_pipeline_svg.py), not the generated SVG.

Regenerate it from the repository root after changing timeline content:

```bash
python3 2027_build/docs/scripts/generate_pipeline_svg.py
```

## Agreed delivery order

1. **Short shared measurement preflight:** establish camera/IMU timing, fixed physical frames, and one replayable recording. This supplies the evidence needed to interpret IMU measurements; it is not a separate camera-only feature phase.
2. **Parallel subteam work:** data synthesis creates/records replayable sessions and validates IMU evidence; VSLAM establishes visual and visual-inertial trajectory/map evidence; integration prepares the synthetic fixture and final handoff contract.
3. **Bundle gate:** verify one replayable Navigation Data & VSLAM Handoff Bundle against the manifest, sensor-topic/TF, VSLAM map/trajectory, obstacle, and single-`map -> odom` contracts.
4. **Package conversion:** convert only the vertical slices proven at integration. Minimal scaffolding may exist earlier; do not migrate the legacy prototype merely to fill the target workspace.
5. **GPS:** evaluate global localization after the local stack and its replay evidence are stable.

The responsibilities can start independently, but all three are complete only when their evidence is assembled into the validated handoff bundle. The next subteam owns costmap construction, route decisions, planning/control, and motors.
