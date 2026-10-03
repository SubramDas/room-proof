"""Fetch pinned Grounding DINO Tiny inference assets for offline CPU runs."""

import argparse
import hashlib
from pathlib import Path


MODEL_ID = "IDEA-Research/grounding-dino-tiny"
REVISION = "a2bb814dd30d776dcf7e30523b00659f4f141c71"
WEIGHTS_SHA256 = "1a2412ef99bd74bcd3c2a246fa1e48581f8889a1300c9051974741314fc042f3"
DEFAULT_DESTINATION = Path(__file__).resolve().parents[1] / ".room-proof/models/grounding-dino-tiny"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    from huggingface_hub import snapshot_download

    destination = args.destination.resolve()
    snapshot_download(repo_id=MODEL_ID, revision=REVISION, local_dir=destination,
                      allow_patterns=["*.json", "*.txt", "*.safetensors"])
    weights = destination / "model.safetensors"
    if not weights.is_file():
        raise FileNotFoundError(f"download incomplete: {weights}")
    digest = hashlib.sha256()
    with weights.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != WEIGHTS_SHA256:
        raise ValueError("Grounding DINO checkpoint SHA-256 mismatch")
    print(f"model: {MODEL_ID}@{REVISION}")
    print(f"weights: {weights}")
    print(f"weights_sha256: {digest.hexdigest()}")


if __name__ == "__main__":
    main()
