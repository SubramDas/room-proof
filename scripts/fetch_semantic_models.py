"""Fetch the public Grounding DINO tiny model once, for offline runtime."""
from pathlib import Path
from huggingface_hub import snapshot_download
root=Path(__file__).resolve().parents[1]
snapshot_download('IDEA-Research/grounding-dino-tiny',local_dir=root/'models/grounding-dino-tiny',allow_patterns=['*.json','*.txt','*.safetensors','README.md'])
print('Grounding DINO ready')
