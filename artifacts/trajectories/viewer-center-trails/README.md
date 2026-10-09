# Offline center trail viewer

[Open the refreshed viewer](trial-1.html). The color/ID legend uses distinct colors. Click a square or its legend entry to highlight its trail and dim the others; enable `only selected trail` to hide the others entirely. Set `Trail frames` to 20 for a recent window or 0 for full history. Turn off `show squares`, `show container boundary`, IDs and orientation marks for clean center trails. Dots mark retained centers; connecting lines do not reconstruct skipped motion or physical speed. Non-finite centers break the trail. Orientation marks clear the upright ID labels. Container side captions sit outside the drawing, validation uses readable measurements, and the provisional warning banner has been removed.

Zoom the current panel with the wheel or numeric `Zoom ×` field (0.25–65536), and drag to pan. Container, squares and trails share one scene transform; labels and line widths remain readable screen sizes. `Fit container` and `Fit full trajectory` explicitly set the camera. `Focus selected ID` centers the current pose without changing magnification. The camera does not follow frame changes automatically. For micromovements, select an ID, use a short trail window, focus it and increase the zoom.

Drag markers A/B, edit their zero-based frame indices, or use `Set A here` / `Set B here`. Choose `Play range once` to stop on B or `Loop range` to return to A. The default range is the complete recording. Manual frame navigation pauses playback. SVG export preserves the camera, history window and visibility settings.

This is an offline rendering of the existing [dense CUDA trajectory](../demo-sweeps/trajectories/trial-1.npz), with its [original metadata](../demo-sweeps/trajectories/trial-1.meta.json.gz). No simulation was rerun. The 139 recorded frames and original replay comparison remain unchanged; the original HTML, metadata, reports and publication manifests were preserved. The NPZ SHA256 is `940d7a51aa14b530d177a007e53db152b1d04ea51d4e085cc3bef9760500c829`.

The refreshed dense HTML is 135690 bytes. Accepted-mode examples are [ID 1](accepted/trial-1.html) (83718 bytes), [ID 7](accepted/trial-7.html) (83688 bytes) and [ID 10](accepted/trial-10.html) (83755 bytes). The [historical ID 4124](historical/trial-4124.html) viewer is 116064 bytes and retains its original replay mismatch status.

[Chromium evidence](browser.json.gz) and [screenshot](browser/trajectory-viewer.png) verify playback, slider controls, Canvas trail visibility, the fixed initial reference, exact saved center coordinates, recent history, square picking, focus dimming, visibility toggles, unique legend colors and SVG label clearance. Real mouse events verify wheel zoom, drag panning and both marker drags. Zoom 4096 and 65536 preserve the shared geometry transform; frame changes preserve the camera. One-shot playback stops on B, loops wrap to A, and manual seeking pauses playback. The browser made no non-file requests and emitted no JavaScript errors. Temporary browser fixtures cover single-frame playback, all 32 legend colors, two-digit IDs, a 45-degree rotation and a non-finite center gap; those fixtures are not scientific evidence. Maximum-size 4096-frame playback performance was not benchmarked.

Focused verification: `uv run --no-sync pytest tests/test_trajectory_viewer.py tests/test_trajectory_format.py tests/test_trajectory_workflow.py tests/test_publication.py -q` — **42 passed**, 3.83 s. Production CUDA code was not changed by this viewer correction.

Regenerate another viewer without CUDA:

```bash
uv run asquerix trace-render artifacts/trajectories/demo-sweeps/trajectories/trial-1.npz \
  --output runs/center-trails-view.html --json
```

Reproduce the browser check:

```bash
uv run python tools/trajectory_browser_smoke.py \
  --html artifacts/trajectories/viewer-center-trails/trial-1.html \
  --output /tmp/center-trails-browser.json.gz \
  --screenshot-dir /tmp/center-trails-browser-screens
```
