# Models and dependencies

Runtime is offline, with local weights under this directory. No private inference service or API token is used.

| Component | Source | Purpose | Disclosure |
|---|---|---|---|
| Depth Anything V2 Metric Hypersim Small | https://github.com/DepthAnything/Depth-Anything-V2 | Initial RGB metric-depth prior | Apache-2.0 small model; large systematic scale errors on supplied stills |
| Apple Depth Pro (optional) | https://github.com/apple/ml-depth-pro | Metric depth plus focal estimate | Use the license included in downloaded source/weights; larger CPU cost; results must be measured |
| Grounding DINO tiny | https://huggingface.co/IDEA-Research/grounding-dino-tiny | Open-vocabulary visual proposals | Model confidence is not calibrated damage probability |
| OpenCV GrabCut | OpenCV | Candidate region mask | Used instead of SAM; quality/occlusion limitations remain |
| Explicit staged marker mode | Project code | Black/brown prop localization | Not trained natural crack or flood detection |

Run `scripts/fetch_models.py`, optionally `--depth-pro`, and `scripts/fetch_semantic_models.py` from the project environment. Downloaded source revisions and weight hashes are recorded in manifests; each reconstruction also records its model fingerprint. The initial locally available detector weights and installed dependency packages were copied from an existing environment on this laptop. Application inference code in this project was implemented here. No existing application output or surveyed dimensions are used as predictions.

Do not commit model binaries, credentials or private imagery. A reproduction export can include weights as a separate local volume. Downloading from public model hosts requires network access but no user API key for these assets.
