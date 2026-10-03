# Capture protocol | Stray Scanner 1.4

**Part 1 · Option 2: Stock Capture Protocol.**  
**Tested capture device:** iPhone 15 Pro Max. **Operator:** no technical experience required.

## 1. Install and prepare (about 2 minutes)

Install **Stray Scanner** by Kenneth Blomqvist from the App Store (app ID 1557051662); allow camera access. This submission uses **version 1.4**. Keep the existing 1.4 installation; if the store offers another version, record it and request a short compatibility check before the full capture. Charge the phone, check free storage, clean its rear lenses, switch on room lights and open connecting doors. Keep people and pets out of the walking path. Do a 10-second trial recording and confirm that the saved video plays before proceeding.

## 2. Walk and record (30–60 seconds per room; 2–4 minutes here)

Hold the phone upright at chest height, with rear cameras and LiDAR uncovered. Start recording in the kitchen at a recognisable corner. Walk slowly around its accessible perimeter, aiming across the room at the walls; gently tilt down to show floor edges and up to show ceiling edges. Show every corner and the whole doorway, including both sides and the top.

Follow one continuous route: **kitchen → hall → corridor → hall → kitchen**. Cover the hall and corridor in the same way. Pause briefly on each side of connecting doorways so the next space and shared features are visible. Finish by viewing the original kitchen corner, then stop and save. For another property, visit every room through its connecting passage and return to the start. Use extra time if coverage is incomplete.

## 3. Precautions and damage views

Avoid fast turns, walking backwards, zoom changes, covering the sensors and recording in darkness. Keep furniture still. Include textured surfaces alongside blank walls. Mirrors, glass and shiny surfaces may give unreliable depth; show adjacent solid walls. For damage, take an overall view and a closer view with surrounding wall visible. Do not touch damaged surfaces. Here, **black props represent cracks; brown props represent waterlogging/floods**. Record them as staged examples. If tracking is lost or recording stops, save separately and repeat the complete route.

## 4. Hand off the original files

In the iPhone **Files** app, open **On My iPhone → Stray Scanner** and locate the saved scan. Copy the entire scan folder to a shared drive or external storage using Files, then download/copy it onto the Ubuntu laptop. Confirm the upload/copy finishes. Keep the phone copy until receipt is confirmed. Do not send only the video for the LiDAR tier or compress media through a messaging app.

Deliver one folder containing **rgb.mp4, odometry.csv, camera_matrix.csv, imu.csv, depth/ and confidence/**. Keep all additional exported files, names and numbered frames unchanged. Send a separate note with device, app version, capture date, room names, connections and staging labels. The receiver checks video playback and matching depth/confidence files before processing. Do not edit timestamps, calibration or IMU values; the pipeline handles these.

## 5. Photo and video tiers (separate inputs)

**Photos:** use the native Camera on iPhone 15 or newer. Take **6–8 overlapping photos per room** (2–8 accepted), moving sideways between shots; include ceiling/floor edges and doorways from both sides. Use ordinary Photo mode at 1×. Export JPEG/PNG at original resolution into one named folder per room; convert HEIC to JPEG first. Supply no depth or poses.

**Video:** use ordinary native Camera video at 1×, upright, following the same continuous route and timing. Transfer the original clip without trimming. Native MOV needs a decoder check; supplied benchmark videos are Stray Scanner RGB-only MP4 exports. Only the clip enters the video pipeline.

**Official references:** apps.apple.com/app/id1557051662 · docs.strayrobots.io
