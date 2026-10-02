"""Download one pinned OWLv2 revision for optional offline CPU inference."""

import argparse
import hashlib
from pathlib import Path


MODEL_ID = "google/owlv2-base-patch16-ensemble"
REVISION = "cfd3195ba4ea9592eec887ded089f4c08eff231d"
WEIGHTS_SHA256 = "e1e130b9e404cf91a75ad45644c1da9d7fa5284085eecc864266a6923efb99e7"
DEFAULT_DESTINATION = Path(__file__).resolve().parents[1] / ".room-proof/models/owlv2-base-patch16-ensemble"


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
        raise ValueError("OWLv2 checkpoint SHA-256 mismatch")
    print(f"model: {MODEL_ID}@{REVISION}")
    print(f"weights: {weights}")
    print(f"weights_sha256: {digest.hexdigest()}")


if __name__ == "__main__":
    main()
