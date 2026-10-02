"""Fetch the pinned Florence-2 Base checkpoint for local CPU comparison."""

import argparse
import hashlib
from pathlib import Path


MODEL_ID = "microsoft/Florence-2-base"
REVISION = "5ca5edf5bd017b9919c05d08aebef5e4c7ac3bac"
WEIGHTS_SHA256 = "03075d2d2d2bbd3e180b9ba0afae4aa8563226e2d32911656966e05b2f2ee060"
CODE_SHA256 = {
    "configuration_florence2.py": "de2e45a975b3582de05d2f4d963a3e9f9a3d20dccf78d28e0052932a0be93bdf",
    "modeling_florence2.py": "5162bf465e61b6e29cc113a467630ec3cb56ed8e4d46eb6207157f10fb9b8a24",
    "processing_florence2.py": "f146023a507c009f425a49ee39aa037f4f25c64e14336e3e4f3f1d7377a68e98",
}
DEFAULT_DESTINATION = Path(__file__).resolve().parents[1] / ".room-proof/models/florence-2-base"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    from huggingface_hub import snapshot_download

    destination = args.destination.resolve()
    snapshot_download(repo_id=MODEL_ID, revision=REVISION, local_dir=destination,
                      allow_patterns=["*.json", "*.safetensors", "configuration_florence2.py",
                                      "modeling_florence2.py", "processing_florence2.py"])
    weights = destination / "model.safetensors"
    if not weights.is_file():
        raise FileNotFoundError(f"download incomplete: {weights}")
    digest = hashlib.sha256()
    with weights.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != WEIGHTS_SHA256:
        raise ValueError("Florence-2 checkpoint SHA-256 mismatch")
    for name, expected in CODE_SHA256.items():
        path = destination / name
        if not path.is_file():
            raise FileNotFoundError(f"Florence-2 model code missing: {path}")
        code_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if code_digest != expected:
            raise ValueError(f"Florence-2 model code SHA-256 mismatch: {path}")
    print(f"model: {MODEL_ID}@{REVISION}")
    print(f"weights: {weights}")
    print(f"weights_sha256: {digest.hexdigest()}")


if __name__ == "__main__":
    main()
