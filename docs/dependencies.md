# External component record

Components below are used by the Phase 1 format audit. They run locally in the project virtual environment and do not upload capture files.

| Component | Version / source | License | Role | Data handling |
| --- | --- | --- | --- | --- |
| imageio-ffmpeg | 0.6.0; [PyPI release](https://pypi.org/project/imageio-ffmpeg/), Linux x86-64 wheel SHA-256 `c7e46fcec401dd990405049d2e2f475e2b397779df2519b544b8aab515195282` | BSD-2-Clause for the Python wrapper | Provides a pinned FFmpeg binary interface to count and decode the Stray HEVC `rgb.mp4`. | Processing is local. No capture media is sent to a service. |
| FFmpeg static binary bundled by imageio-ffmpeg | 7.0.2-static, reported by `imageio_ffmpeg.get_ffmpeg_version()` | `ffmpeg -L` reports GNU GPL version 3 or later for this build. | Decodes RGB video and reports actual decoded frame count. | Processing is local. The binary is installed in `.venv`; it is not tracked in Git. |

A clean temporary environment installed the wheel using `pip --require-hashes`; the Linux wheel is 29.5 MB and the resulting virtual environment was 92 MB.

## Experimental local visual candidate stage

`requirements-model.txt` pins hashes for the Ubuntu 24.04 / CPython 3.12
x86-64 wheels. Installed versions in the pilot were onnxruntime 1.30.0,
NumPy 2.3.3, Pillow 11.3.0, flatbuffers 25.12.19, packaging 26.3, and
protobuf 7.36.2. The [ONNX Runtime package](https://pypi.org/project/onnxruntime/)
is MIT licensed; the [NumPy package](https://pypi.org/project/numpy/) is BSD-3-Clause;
the [Pillow package](https://pypi.org/project/pillow/) is HPND licensed.
These run locally on CPU; no capture is uploaded. The current `.venv` is
251 MB after installation, versus the earlier 92 MB decoder-only environment;
this is an environment comparison, not an isolated package measurement.

The optional 4,418,863-byte [quantized SegFormer B0 ADE20K ONNX checkpoint](https://huggingface.co/Xenova/segformer-b0-finetuned-ade-512-512/blob/main/onnx/model_quantized.onnx)
has SHA-256 `9a98d6daf3d926869ab8cc4c2ed7374a2bc23b889bb7ca3b0915d15e3c4756bb`.
`scripts/fetch_visual_model.py` downloads and verifies it into an ignored
local directory. The [original SegFormer repository license](https://github.com/NVlabs/SegFormer/blob/master/LICENSE)
restricts its use to research and evaluation. The checkpoint is an
**experimental pilot only**; replace it or secure suitable rights before
commercial use. A 30-photo pilot took 17.56 seconds for the model stage;
24 video samples took 9.52 seconds on the current CPU. Peak memory and
clean-machine model setup time remain unmeasured. See
[the pilot](../reports/model_candidate_pilot.md) and
[candidate contract](visual_candidates.md).

## Optional OWLv2 opening candidate pilot

`--visual-backend owlv2` uses the local
[google/owlv2-base-patch16-ensemble](https://huggingface.co/google/owlv2-base-patch16-ensemble)
checkpoint at revision `cfd3195ba4ea9592eec887ded089f4c08eff231d`.
The model card lists Apache-2.0. `scripts/fetch_owlv2_model.py` downloads the
pinned revision into the ignored `.room-proof/models/` directory. The
`model.safetensors` file is 619,918,824 bytes with SHA-256
`e1e130b9e404cf91a75ad45644c1da9d7fa5284085eecc864266a6923efb99e7`.
The local pilot uses PyTorch 2.8.0+cpu, Transformers 4.57.1, SciPy 1.16.2,
and Hugging Face Hub 0.36.2. These packages and weights are optional and are not
included in `requirements-model.txt`; install them into the local environment
before using this backend. The run report records all local model file hashes,
package versions, prompts, threshold, selected frame IDs, and CPU timing.
For the tested Python 3.12 environment, provisioning commands were:

```bash
.venv/bin/python -m pip install 'torch==2.8.0' --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install 'transformers==4.57.1' 'scipy==1.16.2'
.venv/bin/python scripts/fetch_owlv2_model.py
```

Model loading uses `local_files_only=True`; capture images remain local. The
box detector proposes visible objects only. The paired depth and fitted-wall
checks can reject or leave those proposals unresolved; they do not turn its
score into a metric uncertainty interval.

## Optional Florence-2 Base visual candidate comparison

`--visual-backend florence2` uses Microsoft's
[Florence-2 Base](https://huggingface.co/microsoft/Florence-2-base) at commit
`5ca5edf5bd017b9919c05d08aebef5e4c7ac3bac`. The model card lists MIT.
`scripts/fetch_florence2_model.py` retrieves only the local inference assets
into ignored `.room-proof/models/florence-2-base/`, including the model's
Python configuration, processor, and modeling code. The 463,221,266-byte
`model.safetensors` has SHA-256
`03075d2d2d2bbd3e180b9ba0afae4aa8563226e2d32911656966e05b2f2ee060`.
The adapter hashes every local model file and checks the weight and custom
Python code digests. It
uses the pinned local PyTorch 2.8.0+cpu and Transformers 4.57.1 stack plus
`einops==0.8.1` and `timm==1.0.20`. The model's custom code is loaded only
from that local pinned snapshot into the ignored Hugging Face modules cache.
For this Transformers version, use its fast processor, eager attention, and
generation with `use_cache=False`; the alternative native loader did not
map the downloaded checkpoint weights correctly. No capture media is sent
to a service. Phrase grounding emits boxes without comparable confidence
scores, so the adapter stores a documented zero sentinel and leaves all
boxes as proposals. See `reports/florence2_kitchen_comparison.md` for the
CPU comparison against OWLv2.

## Optional ALIKED + LightGlue cross-capture matcher

The kitchen pilot uses the public [LightGlue repository](https://github.com/cvg/LightGlue)
at commit `eb42fee2d71449efb0aa5c10549752b5d75384d8` (Apache-2.0
LightGlue code/weights; ALIKED code follows BSD-3-Clause). The local
`aliked-n16.pth` SHA-256 is
`5be8704840ed662d9d8c561bf7279c222092674e7eb05fd0feab94899e9d82f2`;
`aliked_lightglue_v0-1_arxiv.pth` is
`d975e965b105311a6143194852297dff4f02aea5cc2e10cecfed966ca0e22503`.
The model cache and cloned source are ignored by Git. The pipeline checks
for both local weights before inference and does not download during a run.

For the current CPU Python 3.12 environment:

```bash
.venv/bin/python -m pip install 'opencv-python-headless==4.12.0.88' 'kornia==0.8.1' 'matplotlib==3.10.6'
.venv/bin/python -m pip install 'torch==2.8.0' 'torchvision==0.23.0+cpu' --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python scripts/fetch_lightglue.py
```

`--match-backend aliked-lightglue` runs locally and records the source
revision, weight hashes, model matches, and epipolar RANSAC inliers. Its
result is a 2D correspondence. The later PnP probe records held-out
reprojection error under explicitly assumed independent-camera focal
lengths; it does not certify metric placement without calibration and
cross-view agreement. The updated kitchen model-on stages plus learned
linker took 1,076.13 seconds (17.9 minutes) sequentially on this CPU,
above the 15-minute target, before provisioning or transfer. The learned
linker also uses OpenCV for every-frame low-resolution optical flow and
arbitrary-scale sparse video motion. A complete clean-machine timing
remains to be measured.

## Optional cloud candidate, not adopted

`roomproof.cloud_vision` contains a single-image adapter for Google's
`gemini-3.5-flash-lite` API. The initially coded `gemini-2.5-flash-lite`
returned HTTP 404 for this account with a message directing new users to
3.5 Flash-Lite. It has no local model file or software dependency
beyond Python's standard library. The [Google model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
and [pricing/terms page](https://ai.google.dev/gemini-api/docs/pricing) govern
the hosted service. A successful call sends the **original private image**
to Google and records the returned model version, raw response, token usage,
and latency for a development probe. The initial sandboxed call failed before
transfer, and automatic approval review
initially rejected an unsandboxed call for lack of explicit authorization for
that specific photo and destination. The owner subsequently supplied that
explicit authorization. One hall still was sent to Google in
`run-1a11bb4523bd4cb88e834bfb3b81a442` with the 3.5 model. The original
2.5 request returned 404 and no model result. This candidate is not part of the live
prediction path or any reported accuracy number. Before use, confirm account
quota, current terms, property-specific transfer permission, and defense
availability; no free-tier SLA is assumed.
