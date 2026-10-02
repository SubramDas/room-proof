# External component record

Components below are used by the Phase 1 format audit. They run locally in the project virtual environment and do not upload capture files.

| Component | Version / source | License | Role | Data handling |
| --- | --- | --- | --- | --- |
| imageio-ffmpeg | 0.6.0; [PyPI release](https://pypi.org/project/imageio-ffmpeg/), Linux x86-64 wheel SHA-256 `c7e46fcec401dd990405049d2e2f475e2b397779df2519b544b8aab515195282` | BSD-2-Clause for the Python wrapper | Provides a pinned FFmpeg binary interface to count and decode the Stray HEVC `rgb.mp4`. | Processing is local. No capture media is sent to a service. |
| FFmpeg static binary bundled by imageio-ffmpeg | 7.0.2-static, reported by `imageio_ffmpeg.get_ffmpeg_version()` | `ffmpeg -L` reports GNU GPL version 3 or later for this build. | Decodes RGB video and reports actual decoded frame count. | Processing is local. The binary is installed in `.venv`; it is not tracked in Git. |

A clean temporary environment installed the wheel using `pip --require-hashes`; the Linux wheel is 29.5 MB and the resulting virtual environment was 92 MB. A later image/model dependency needs its own version, source, license/terms, role, hash where practical, data handling, and measured size/runtime entry here before use.

## Optional cloud candidate, not adopted

`roomproof.cloud_vision` contains a single-image adapter for Google's
`gemini-2.5-flash-lite` API. It has no local model file or software dependency
beyond Python's standard library. The [Google model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite)
and [pricing/terms page](https://ai.google.dev/gemini-api/docs/pricing) govern
the hosted service. A successful call would send the **original private image**
to Google, record the returned model version, raw response, token usage, and
latency, and use the result only as a development probe. No image was sent:
the sandboxed call failed before transfer, and automatic approval review
rejected an unsandboxed call for lack of explicit authorization for that
specific photo and destination. This candidate is not part of the live
prediction path or any reported accuracy number. Before use, confirm account
quota, current terms, property-specific transfer permission, and defense
availability; no free-tier SLA is assumed.
