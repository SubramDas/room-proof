"""Fetch pinned ESANet NYUv2 source and checkpoint for local RGB-D comparison."""

import argparse
import hashlib
from pathlib import Path
import subprocess
import tarfile

import gdown


REPOSITORY = "https://github.com/TUI-NICR/ESANet.git"
REVISION = "820c5bb633e49e69dcd075d4330165bb540a0cc9"
DRIVE_ID = "1C5-kJv4w3foicEudP3DAjdIXVuzUK7O8"
ARCHIVE_SHA256 = "46f6a664d3410f3d8d2d4f42d5afdbbda4bac63467e42779c25a2e59b571000a"
WEIGHTS_SHA256 = "eb1e5ee8b7c8f46f0d3014ac8684069b8ae6f52ddc24d655ef163be5ef962150"
DEFAULT_DESTINATION = Path(__file__).resolve().parents[1] / ".room-proof/models/ESANet"


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    destination = args.destination.resolve()
    if not destination.exists():
        subprocess.run(["git", "clone", REPOSITORY, str(destination)], check=True)
        subprocess.run(["git", "-C", str(destination), "checkout", "--detach", REVISION], check=True)
    revision = subprocess.run(["git", "-C", str(destination), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    if revision != REVISION:
        raise ValueError(f"ESANet source revision differs from pinned {REVISION}: {revision}")
    archive = destination / "nyuv2_r34_NBt1D.tar.gz"
    if not archive.exists():
        if not gdown.download(id=DRIVE_ID, output=str(archive), quiet=False):
            raise RuntimeError("ESANet checkpoint download failed")
    if digest(archive) != ARCHIVE_SHA256:
        raise ValueError("ESANet checkpoint archive SHA-256 mismatch")
    weights = destination / "nyuv2/r34_NBt1D.pth"
    if not weights.exists():
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            if len(members) != 1 or members[0].name != "nyuv2/r34_NBt1D.pth" or not members[0].isfile():
                raise ValueError("unexpected ESANet checkpoint archive contents")
            weights.parent.mkdir(parents=True, exist_ok=True)
            with bundle.extractfile(members[0]) as source, weights.open("wb") as target:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(block)
    if digest(weights) != WEIGHTS_SHA256:
        raise ValueError("ESANet checkpoint SHA-256 mismatch")
    print(f"ESANet source: {REPOSITORY}@{REVISION}")
    print(f"checkpoint: {weights}")
    print(f"checkpoint_sha256: {WEIGHTS_SHA256}")


if __name__ == "__main__":
    main()
