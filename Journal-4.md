# Journal 4 — Ordinary video and photo geometry

**Status:** In progress on 2 October 2026. T32 and T36 are complete. T30 and T33 have checked substeps; T31, T34, T35, and T37 remain open.

## Work landed

- Added `roomproof/visual_geometry.py`, a bounded local RGB analysis path using the already pinned FFmpeg decoder and Python standard library. It extracts gradient corners and contrast-normalized image patches, makes mutual descriptor matches, and counts matches with coherent image displacement. The result is image-space evidence only. It does not claim camera pose, room boundaries, depth, or metric scale.
- Changed video sampling from isolated evenly spaced frames to up to six evenly spaced short bursts, each using source frames two apart. This keeps broad temporal coverage while providing nearby views for motion estimation. `frames.json` records the group and original frame index. `visual_geometry.json` distinguishes unsupported within-burst tracking from intentional gaps between bursts.
- Fixed sampled video frame dimensions in `frames.json`: the decoder header described the original input resolution even when FFmpeg emitted 640-pixel frames. The reader now checks the emitted RGB byte count and records the actual 640-pixel output size.
- Photo analysis decodes each still, records per-frame corner/luma/gradient quality, and checks up to 256 deterministic image pairs with within-room pairs first. Folder names remain identifiers; a matching pair alone does not create adjacency.
- The current scale policy uses no prior or learned metric-depth model. Video and photo metric measurements stay null with unbounded intervals in the common JSON. Reference tape values are not read by the inference path.

## Evidence

| Capture | Run | Result |
| --- | --- | --- |
| Standalone `single_room/c00a170fe1/rgb.mp4`, treated as an ordinary clip with no sidecars | `run-4cbe8839016e46acb2936a45cca58e33` | 24 sampled frames in six bursts; 14 of 18 within-burst transitions have supported image overlap, four are tracking gaps, five are intentional sampling gaps. This source came from a LiDAR export, so it is a video-reader development check, not an independent Camera-tier benchmark. |
| Two PNG stills derived from adjacent frames of that clip | `run-cdb77082c2ed4ea1add472f30e34a4b3` | One within-room pair has 17 mutual matches and 11 coherent inliers. This is a photo decoder/matcher check, not an independent iPhone still capture. |
| Earlier synthetic two-PNG fixture | `run-35e0a46f6f4544d191df57e87aff7fc2` | Zero usable corners and no false overlap claim. |
| Owner hall stills in `hall_photos/room-hall/` | `run-a498b59c570341a3898e34e2bd668dc0` | Eight JPEGs accepted with schema-valid output. The current matcher found no supported pair among 28 combinations. Visual review shows broad coverage of the living area, doorways, floor, and ceiling, but some views are isolated floor/ceiling shots with little shared texture. No metric geometry or adjacency is asserted. |
| Owner hall Camera clip `hall_video/IMG_0009.mp4` | `run-4d0b105f989b4ea7838a0f294a62810b` | 1,289 decoded frames; 24 sampled in six bursts; 13 of 18 within-burst transitions supported, five tracking gaps. Input accepted as valid-low-confidence because metric scale and structure remain unresolved. |

Runs are under `/tmp/roomproof-phase4-runs`. Derived stills are under `/tmp/roomproof-phase4-photo-derived`; raw source captures were not modified.

The owner hall runs are under the ignored `runs/` directory. Raw hall files remain in their supplied folders unchanged. The hall alone cannot test multiroom stitching; the owner has been asked for the other rooms plus a connector, with doorway views from both sides and one continuous cross-room video.

The owner supplied `Flat-805/` with `room-bed` (8 JPEGs), `room-hall` (7), `room-kitchen` (8), `room-toilet` (7), and one top-level MP4. The CLI now accepts that mixed folder for either tier without reading video as photo evidence. Photo run `run-6276894a18974e60962659117f1e67c8` accepted all 30 stills, created four room entries, and found no supported photo pair among the bounded comparisons. Video run `run-c8250e02f67b47e7baddf1207bc5eefa` decoded 3,328 frames and supported image motion on 9 of 18 within-burst transitions. Both wrote schema-valid unresolved plans. The photo matcher result is a method limitation, not an input-format rejection.

The Flat-805 stills decode at approximately 960×1280 or 1280×960, and the video at 478×850. The owner confirmed that these are the original files supplied for this capture. Preserve and evaluate them as supplied; resolution alone is not evidence of a transfer alteration.

After adding a bounded similarity transform to the matcher, photo run `run-a12996138a9b42f0a2a5d564d5b64ba2` found three supported within-room pairs (bed, kitchen, toilet) and zero supported cross-room pairs. Run `run-5a0fcbff2e0b4bf58b5c78f9c855b1a8` also records long vertical and horizontal contrast ridges per frame as unclassified wall/opening evidence. These ridges can also come from furniture, curtains, and window frames; no opening dimensions or room boundaries were inferred.

Video run `run-08357569b6104024adcda7c6af3a1b88` supported 11 of 18 local frame transitions and extracted a one-frame-per-second appearance profile. Its change heuristic flagged about 35, 103, and 108 seconds. Direct frame inspection showed a turn inside the toilet at about 35 seconds and turns around kitchen furnishings at about 103–108 seconds. These are **false room-transition candidates**. The report labels them appearance changes and leaves `room_transition_hypotheses` empty. A doorway-crossing method is still needed.

Photo run `run-732ee29b93a24b508091137148c1f4fc` added an explicit `placement_ambiguities` group for the four rooms to the schema-valid property plan and its SVG. This records the unresolved multiroom layout without inventing adjacency or metric dimensions. It satisfies T36's unresolved-placement path but does not satisfy T34's stitching gate.

The latest owner photo run took 17.68 seconds for 30 stills and its bounded pair comparisons; the latest video run took 9.92 seconds for 24 motion frames and 111 coarse scene samples. These are ingestion/evidence timings, not a successful full reconstruction timing. Matched LiDAR and scored-output timings remain for T37.

## Remaining gates

- **T30–T31:** Infer scene structure, rooms, door transitions, and a stitched layout from a genuine standalone Camera walkthrough; the current tracker only measures local image motion.
- **T33–T34:** Extract walls and doorway views from independent 2–8 stills per room; infer and optimize adjacency on a multiroom photo capture.
- **T35:** Evaluate any photo scale aid before adoption. The current output keeps metric quantities unbounded.
- **T37:** Time a fresh capture for each tier and confirm the frame/pair bounds meet the CPU and live-run constraints.
