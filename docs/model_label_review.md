# Owner review: visible openings in Flat-805

This is a draft review list, not reference truth. Open the original JPEGs in
`Flat-805/`; the candidate IDs below are from photo run
`run-fc0df29f8b2e4845aa31a6c8fd13b6ee`. For each visible opening, record
its image box or polygon, the room and wall it belongs to, whether another
room view shows the same physical opening, and whether it is occluded. Mark
uncertain examples as ambiguous. Do not supply tape measurements in this
visual-label file; keep those only in the benchmark reference manifest.

| Source image | Draft observation to confirm | Model proposal |
| --- | --- | --- |
| `room-bed/IMG_0011.jpeg` | Bedroom door partly blocked by clothes; confirm visible door region and destination room. | No door proposal in this image. |
| `room-hall/IMG_0018.jpeg` | White door at left and open kitchen at right; identify which room each connects. | `candidate-2e4db138ed5f7bc5` door box `[150,500,300,810]`. |
| `room-hall/IMG_0017.jpeg` | Open kitchen entry and glass doors; identify which opening is a room connection versus exterior/glazing. | Review all door/window proposals in run artifact. |
| `room-kitchen/IMG_0023.jpeg` | Cabinet on left; confirm it is furniture rather than a doorway. | `candidate-a8978634ad2d7f2f` door box `[67.5,1010,135,1190]`, likely false. |
| `room-kitchen/IMG_0029.jpeg` | Sink/window scene; confirm whether any doorway is visible. | `candidate-d73aa104949988b7` door box `[1040,345,1280,960]`, likely false. |
| `room-toilet/IMG_0003.jpeg` | Doorway looking toward hall; identify its visible boundary and reciprocal hall view if any. | Three door fragments: `candidate-b3dd9f86ee9a94ae`, `candidate-b04c0383326158da`, `candidate-5201ea00907cbedc`. |

Please identify one view of each doorway from **both connected rooms** where
available. If the current photos do not show both sides, mark the pair
`not visible`; the pipeline must leave that room link unresolved. Also mark
any dark gap, wardrobe, cabinet, mirror, or window that might be confused with
a door as a negative. This review can be returned as a marked image set or a
simple table with source image, physical opening ID, room/wall, class, box,
matching view, and ambiguity reason.

The current 30 photos and selected video frames are development material.
Hold out the promised new property capture intact for later evaluation; do
not use it to set model thresholds or resolve these examples.
