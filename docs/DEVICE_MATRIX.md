# Device and runtime matrix

| Hardware | Photos | Video | LiDAR | Evidence |
|---|---|---|---|---|
| iPhone 15 Pro Max, Stray Scanner 1.4 | Yes | Yes | Yes | Supplied captures used |
| Other iPhone 15 or newer | Expected for supported JPEG/PNG | Expected for supported original video | Only devices with LiDAR and compatible export | Not physically tested |
| Ubuntu 24 laptop, Intel i7-1265U, 64 GB RAM, no GPU | CPU inference | CPU inference | CPU reconstruction | Actual development machine |
| Kaggle with GPU | Optional | Optional | CPU geometry still used | Notebook/setup supplied; hosted run not validated |

All tiers use local public models; no paid model API. The depth model's optional CUDA path and model download setup need a compatible torch installation. A GPU changes runtime, not the measurement gate or validation status.

Accuracy is reported from actual runs in `reports/benchmark.md`, not inferred from hardware specifications. The LiDAR height gate, photo/video scale gates, calibrated uncertainty, opening detection score and complete photo stitch must each be assessed independently. Insufficient scene coverage can make a measurement unavailable on every device.
