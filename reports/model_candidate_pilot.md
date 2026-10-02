# Visual candidate pilot, 2 October 2026

Status: experimental. These runs establish execution and timing, not detection
accuracy. The photo and video plans remain unresolved in both modes. No
owner-reviewed opening/wall labels, tape measurements, or untouched capture
were used to choose thresholds or claim a benchmark improvement.

| Input | Model | Run ID | Total time | Model stage | Proposals | Final plan |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Flat-805 photo stills, 30 images | off | `run-07fca41aaa554d79941e78536974a48c` | 32.58 s | — | 0 | unresolved |
| Same photo stills | on | `run-fc0df29f8b2e4845aa31a6c8fd13b6ee` | 46.65 s | 17.56 s | 117 | unresolved |
| Flat-805 standalone video, 24 selected frames | off | `run-4913d51952514de2862786ec10a7ab70` | 15.37 s | — | 0 | unresolved |
| Same video | on | `run-59266333353045baa16f4268b7ac4662` | 25.15 s | 9.52 s | 83 | unresolved |

The photo input revision for both runs is
`2ca97814b981bae3b082d63ecc1eaf71064b3c97123a388f8d22ff469c5543fb`;
the video input revision is
`7702bb92e87b6f62ad47fae0aa971ae0899369d819c3bbaa4f524a050be5f89c`.
All four runs record code revision
`6f3b74918d6a9a821b41212424d0d11b986f02f0` as their starting commit,
with local changes flagged dirty. The weight SHA-256 is
`9a98d6daf3d926869ab8cc4c2ed7374a2bc23b889bb7ca3b0915d15e3c4756bb`.
These runs preceded the later provenance field and validator tightening; repeat
them before a frozen scored comparison.

The source `Flat-805/` tree has a room-level MP4 under `room-hall`, which the
photo input inspector correctly rejects. The pilot copied only the 30 JPEG
stills into `/tmp/roomproof-model-photo-stills` with the same room-folder
names; original captures were not modified. The standalone video input was
`Flat-805/IMG_0031.mp4`. The output root was
`/tmp/roomproof-model-pilot`. Exact command form:

```bash
.venv/bin/python -m roomproof process-capture /tmp/roomproof-model-photo-stills --tier photo --property-id prop-flat-805 --capture-id cap-flat-805-photo-model-development --visual-model on --max-model-frames 30 --runs-dir /tmp/roomproof-model-pilot
.venv/bin/python -m roomproof process-capture Flat-805/IMG_0031.mp4 --tier video --property-id prop-flat-805 --capture-id cap-flat-805-video-model-development --visual-model on --max-model-frames 24 --runs-dir /tmp/roomproof-model-pilot
```

Replace `on` with `off` for the paired baseline. The photo output proposed 36
wall, 18 floor, 23 ceiling, 15 door, and 25 window regions. The video output
proposed 30 wall, 17 floor, 8 ceiling, 18 door, and 10 window regions. Counts
are per-frame components and include repeated views, so they are not counts
of physical walls or openings. The model stage averages about 0.59 seconds
per selected photo and 0.40 seconds per selected video sample in these runs;
full end-to-end time also includes input inspection and existing geometry.
Peak memory was not captured.

Manual inspection found a visible bedroom door in `room-bed/IMG_0011.jpeg`
that the model did not propose. It proposed a door on a cabinet view in
`room-kitchen/IMG_0023.jpeg`, a likely false positive. It also proposed
several door fragments in `room-toilet/IMG_0003.jpeg`; these are not separate
physical doors. See [label review](../docs/model_label_review.md). Until
labels are reviewed, precision, recall, wall association, and shared-doorway
matching remain unscored. No evidence supports adopting this checkpoint for
final plans or metric measurements yet.
