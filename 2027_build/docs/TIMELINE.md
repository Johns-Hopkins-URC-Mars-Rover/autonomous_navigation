# IMU-First Timeline

The visual roadmap is [`pipeline.svg`](pipeline.svg). Its source of truth is [`scripts/generate_pipeline_svg.py`](scripts/generate_pipeline_svg.py), not the generated SVG.

Regenerate it from the repository root after changing timeline content:

```bash
python3 2027_build/docs/scripts/generate_pipeline_svg.py
```

## Agreed delivery order

1. **Short shared measurement preflight:** establish camera/IMU timing, fixed physical frames, and one replayable recording. This supplies the evidence needed to interpret IMU measurements; it is not a separate camera-only feature phase.
2. **Parallel individual milestones:** Wobbles performs IMU integration and a matched camera-only versus IMU-fused comparison. Hedgie independently completes the visual-only SLAM benchmark from files/fixtures. Bedrawn independently completes the costmap-ready obstacle/localization input bundle in synthetic/replay.
3. **Integration gate:** verify one replayable session against the manifest, sensor-topic/TF, map/obstacle, single-`map -> odom`, and external costmap/planning handoff contracts.
4. **Package conversion:** convert only the vertical slices proven at integration. Minimal scaffolding may exist earlier; do not migrate the legacy prototype merely to fill the target workspace.
5. **GPS:** evaluate global localization after the local stack and its replay evidence are stable.

The resulting dependencies are intentionally asymmetric: Hedgie and Bedrawn can start without the IMU result, but all three workstreams need the final Wobbles sensor/frame contract for end-to-end validation. Bedrawn supplies the external costmap/planning team with input and evidence; that team owns costmap construction and route decisions.
