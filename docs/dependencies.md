# External component record

Components below are used by the Phase 1 format audit. They run locally in the project virtual environment and do not upload capture files.

| Component | Version / source | License | Role | Data handling |
| --- | --- | --- | --- | --- |
| imageio-ffmpeg | 0.6.0; [PyPI release](https://pypi.org/project/imageio-ffmpeg/), Linux x86-64 wheel SHA-256 `c7e46fcec401dd990405049d2e2f475e2b397779df2519b544b8aab515195282` | BSD-2-Clause for the Python wrapper | Provides a pinned FFmpeg binary interface to count and decode the Stray HEVC `rgb.mp4`. | Processing is local. No capture media is sent to a service. |
| FFmpeg static binary bundled by imageio-ffmpeg | 7.0.2-static, reported by `imageio_ffmpeg.get_ffmpeg_version()` | `ffmpeg -L` reports GNU GPL version 3 or later for this build. | Decodes RGB video and reports actual decoded frame count. | Processing is local. The binary is installed in `.venv`; it is not tracked in Git. |

A clean temporary environment installed the wheel using `pip --require-hashes`; the Linux wheel is 29.5 MB and the resulting virtual environment was 92 MB. A later image/model dependency needs its own version, source, license/terms, role, hash where practical, data handling, and measured size/runtime entry here before use.
