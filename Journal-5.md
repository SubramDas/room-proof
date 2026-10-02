# Journal 5 — Damage, concealed flags, and scope

Status: partial. Added a versioned visible-damage vocabulary draft and a
source-evidence-gated rule engine. It creates surface-specific, conditional
flags and scope entries only for supplied damage regions, and returns empty
lists for no evidence. No detector, labelled two-class samples, cloud/local
comparison, or metric surface mapping is claimed. Added an optional bounded
Gemini still-image probe with disclosed data transfer and run
latency; its labels do not enter plan inference. A sandboxed pilot failed before
network transfer in `run-ad5b96056bc84e8c89fd5a81a4366fe7`. Automatic
approval review then rejected the requested network call because the specific
private photo and Google destination were not explicitly authorized in the
conversation. The owner later explicitly authorized that exact transfer.
`gemini-2.5-flash-lite` returned HTTP 404 for this account; the API directed
new users to `gemini-3.5-flash-lite`. The authorized 3.5 pilot completed in
`run-1a11bb4523bd4cb88e834bfb3b81a442`: 1.94 seconds, 1,149 prompt
tokens and 73 output tokens. It reported a visible door and window and no
visible damage in one hall still. These are unverified labels, not a measured
accuracy result. T38–T41 remain open; T42–T43
have reusable implementation but cannot pass their end-to-end gates yet.

The successful pilot uses `gemini-3.5-flash-lite`. Its raw API response,
returned model version, prompt, usage, and latency are in ignored
`runs/run-1a11bb4523bd4cb88e834bfb3b81a442/vision_probe.json`.
