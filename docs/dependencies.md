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
