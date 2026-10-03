# Stock capture protocol — one page

**Route 2.** Capture device used: iPhone 15 Pro Max. LiDAR capture app: **Stray Scanner 1.4**. Runtime: Ubuntu laptop; no phone app developed for this submission. Ask the operator to select one tier before capture.

## Prepare

1. Charge the phone, clean its camera, enable normal room lighting and open connecting doors. Keep furniture in place. Get consent before recording people or private items.
2. Draw a rough room-name list (room_1, room_2, etc.). Include connecting corridors in the route. Mark a starting spot you can return to. Do not add laser measurements to the pipeline's input folder.
3. Avoid changing zoom or lens. Keep the phone upright. Walk slowly; pause at doorways and wall corners. Scan glass/mirrors at oblique angles from both sides where safe; do not treat a reflected room as extra space. Add close-ups of wet-looking or damaged surfaces without touching them.

## LiDAR tier — iPhone Pro with LiDAR

Install/open Stray Scanner 1.4; record RGB, depth, confidence, camera poses/intrinsics and IMU. Begin in a visible corner, scan floor-to-wall and wall-to-ceiling junctions, then all walls. Sweep gently up to the ceiling and down to the floor. Walk through each doorway, showing both jambs and lintel from both sides. Traverse every room and corridor. Return to the starting area and view the original corner again to provide loop-closure evidence. About 30–60 seconds per room; prioritize complete coverage over a fast rotation. Export the original scan directory, without trimming or re-encoding its video.

Deliver one directory containing `rgb.mp4`, `odometry.csv`, `camera_matrix.csv`, `imu.csv`, `depth/*.png`, `confidence/*.png`. A parent folder containing one such export is also accepted. Preserve file names and frame order.

## Video tier — iPhone 15 or newer

Use the native Camera, ordinary video, 1× lens, portrait orientation, good lighting, no cinematic mode. Follow the same continuous path, including doorway views and the return loop. Avoid quick pans, motion blur and stopping/restarting between rooms. Transfer the original MP4/MOV supported by the decoder. The current adapter is tested on the supplied MP4; other containers require conversion/remuxing and verification before the defense. Supply only the video. If a raw export displays sideways, use the documented `--rotation 90` option; test the first extracted frame.

## Photo tier — iPhone 15 or newer

Take 6–8 overlapping stills per room (2 minimum supported, but often insufficient for registration). Include all wall/ceiling/floor junctions. Photograph each connecting doorway from both rooms, with common textured features in view. Move sideways between shots to give parallax; do not just rotate in place. No panorama, digital zoom or portrait blur. Keep original images and metadata. Deliver `photos/room_1/*.jpg`, `photos/room_2/*.jpg`, etc., 2–8 JPEG/PNG images each. HEIC must be exported as JPEG before running this implementation. Do not supply LiDAR or AR poses to this tier.

## Handoff and benchmark

Copy files using cable or original-quality transfer; avoid messaging-app compression. Run the README command for the chosen tier. Keep the original files unchanged. For scoring, independently measure named walls, ceiling height and every opening; give opening IDs, connected rooms, widths, heights and wall offsets. Measure staging props separately. Repeat the complete capture from scratch when measuring repeatability; replaying the same files is not a repeat scan. Inspect the output's warnings and unresolved connections before accepting the plan.
