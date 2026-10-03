# Ground-truth scope and independent evidence

Source: `measurements.txt`, laser measurements supplied by the user. Instrument make/model and uncertainty were not supplied. Height/doorway-height duplicate labels were corrected by the user before scoring.

Physical mapping: room_1 is kitchen, room_2 is hall, room_3 is corridor. Hall connects kitchen and corridor. This mapping is reference annotation, not an input used to force reconstructed dimensions or adjacency.

Room lengths and breadths have no wall IDs, offsets, thicknesses or nonrectangular corner coordinates. Accordingly, current scoring compares sorted room-axis extents as **proxies**, not every wall. The doorway entries do not identify unique openings independently: kitchen and hall may refer to the same shared .88 m opening, while corridor lists .81 m. No denominator for all doors/windows, including other openings, is known. A full detection/phantom score cannot honestly be calculated.

Missing measurement evidence: opening IDs and wall associations for every opening/window; damage polygons/width/height or marked reference dimensions; a measured global plan; repeat scans (deferred); independent calibration scenes; consumer-app exports (unavailable tonight). The given dimensions remain useful for the partial height and extent benchmark.

Kitchen photo files also occur in the multi-room kitchen folder. Those two collections must never be split between calibration and testing as independent captures. The extracted Stray RGB video reuses the LiDAR session but the video-tier algorithm receives only RGB; a separate native-camera capture would add valuable camera-path validation.
