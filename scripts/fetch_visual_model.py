"""Fetch the optional local ONNX model with a pinned SHA-256 digest."""

import hashlib
from pathlib import Path
import urllib.request


URL = "https://huggingface.co/Xenova/segformer-b0-finetuned-ade-512-512/resolve/main/onnx/model_quantized.onnx"
SHA256 = "9a98d6daf3d926869ab8cc4c2ed7374a2bc23b889bb7ca3b0915d15e3c4756bb"
DESTINATION = Path(__file__).resolve().parents[1] / ".room-proof/models/segformer-b0-ade-quantized.onnx"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.is_file() and digest(DESTINATION) == SHA256:
        print(f"verified existing model: {DESTINATION}")
        return
    temporary = DESTINATION.with_suffix(".download")
    try:
        with urllib.request.urlopen(URL, timeout=60) as response, temporary.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        if digest(temporary) != SHA256:
            raise ValueError("downloaded model SHA-256 mismatch")
        temporary.replace(DESTINATION)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"verified model: {DESTINATION}")


if __name__ == "__main__":
    main()
