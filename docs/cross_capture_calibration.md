# Optional independent camera and scan pixel calibration

`link-captures --match-backend aliked-lightglue --calibration FILE` accepts a
version 1 JSON file. It supplies the *sampled image* intrinsics used for
registration and the affine map from the displayed scan-RGB pixels to depth
pixels. The scan RGB view is rotated by `--lidar-rgb-rotation` before matching;
`scan_view_size` refers to that rotated view. The affine map must describe
the same rotated view. The photos or video frames must be rectified before
using this path; the current PnP stage does not model lens distortion.

```json
{
  "version": 1,
  "camera_intrinsics": {
    "photo": {"image_size": [320, 426], "fx": 264, "fy": 264, "cx": 160, "cy": 213},
    "video": {"image_size": [640, 1138], "fx": 600, "fy": 600, "cx": 320, "cy": 569}
  },
  "scan_rgb_to_depth": {
    "scan_view_size": [480, 640],
    "depth_size": [256, 192],
    "affine_2x3": [[0, 0, 0], [0, 0, 0]]
  }
}
```

**The numbers above are illustrative placeholders and must not be used as a
calibration.** A zero affine map fails to locate useful depth landmarks.
Camera entries may instead use an exact source reference as the key when
different photos came from different cameras. Record how intrinsics and the
RGB-to-depth mapping were obtained. Do not include evaluator tape or laser
room dimensions in this file.

The linker validates dimensions and finite coefficients, uses depth-backed
3D landmarks, tests PnP on held-out image points, checks that the landmarks
span 3D, and compares poses from scan views separated by at least 0.5 m.
Only cross-view-consistent calibrated poses can support a metric opening.
The kitchen pilot does not include this calibration and remains unresolved.
