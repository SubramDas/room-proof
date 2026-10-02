# Device and tier matrix — 2 October 2026

| Device and iOS | Photo folders | Ordinary Camera video | Stray Scanner LiDAR | Validated accuracy |
| --- | --- | --- | --- | --- |
| iPhone 15 or newer **without** a LiDAR Scanner | Supported capture route | Supported capture route | Unsupported sensor; reject LiDAR tier | No measured geometry accuracy yet. Photo/video absolute scale cannot be guaranteed from arbitrary unposed images. |
| iPhone 15 Pro Max (owner phone), owner-reported iOS 26.5, Stray Scanner 1.4 | Supported capture route | Supported capture route | Real export received and decoded, but one RGB frame is missing relative to depth/pose | No tape/laser truth or property-plan output yet; no centimetre or interval-coverage claim. |
| Other iPhone 15+ with a **confirmed LiDAR Scanner** and iOS ≥18.6 | Supported capture route | Supported capture route | Candidate only; sensor and app export must be checked on that device | Not measured on those devices. |

Apple lists a [LiDAR Scanner on iPhone 15 Pro Max](https://support.apple.com/en-in/111828). The [Stray Scanner India App Store listing](https://apps.apple.com/in/app/stray-scanner/id1557051662) says Free, requires iOS 18.6 or later, and describes depth, confidence, camera poses, calibration, RGB, IMU, Files access, and sharing. Its generic compatibility list includes phones without LiDAR, while the app description explicitly requires a LiDAR device; the sensor requirement controls this matrix. Later iPhone model names alone do not prove sensor support—check the actual hardware and exported fields.

## Real owner export check

The owner supplied `dummy_room.zip` from Stray Scanner 1.4 on an iPhone 15 Pro Max without changing app settings and extracted it to `dummy_room/`. All 1,144 extracted files match the ZIP byte for byte. The iOS version 26.5 is from the owner’s earlier report and should be reconfirmed during rehearsal. The [machine-readable audit](../reports/device_format_dummy_room.json) measured 570 pose/depth/confidence samples and 569 decoded HEVC RGB frames. The scan is a useful importer test, but exact RGB-to-depth alignment and metric accuracy remain unverified. See the [human-readable audit](../reports/device_format_dummy_room.md).

**Capture route status:** Camera photo/video paths are prescribed but untested on a fresh full property. The free LiDAR export works and contains the needed field types, subject to one-frame handling and a new full scan. The final device matrix must be updated with measured per-tier errors from the benchmark; store listings cannot establish them.
