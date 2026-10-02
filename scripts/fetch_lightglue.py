"""Fetch pinned public ALIKED/LightGlue source and weights for local matching."""

import hashlib
from pathlib import Path
import subprocess
from urllib.request import urlopen


ROOT = Path('.room-proof/models').resolve()
SOURCE = ROOT/'LightGlue'
REVISION = 'eb42fee2d71449efb0aa5c10549752b5d75384d8'
WEIGHTS = (
    ('aliked-n16.pth',
     'https://github.com/Shiaoming/ALIKED/raw/main/models/aliked-n16.pth',
     '5be8704840ed662d9d8c561bf7279c222092674e7eb05fd0feab94899e9d82f2'),
    ('aliked_lightglue_v0-1_arxiv.pth',
     'https://github.com/cvg/LightGlue/releases/download/v0.1_arxiv/aliked_lightglue.pth',
     'd975e965b105311a6143194852297dff4f02aea5cc2e10cecfed966ca0e22503'),
)


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            sha.update(block)
    return sha.hexdigest()


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        subprocess.run(['git', 'clone', 'https://github.com/cvg/LightGlue.git', str(SOURCE)], check=True)
    subprocess.run(['git', '-C', str(SOURCE), 'checkout', '--detach', REVISION], check=True)
    folder = ROOT/'torch-hub'/'checkpoints'
    folder.mkdir(parents=True, exist_ok=True)
    for name, url, expected in WEIGHTS:
        path = folder/name
        if not path.exists() or digest(path) != expected:
            temporary = path.with_suffix('.download')
            with urlopen(url, timeout=120) as response, temporary.open('wb') as stream:
                for block in iter(lambda: response.read(1024*1024), b''):
                    stream.write(block)
            if digest(temporary) != expected:
                temporary.unlink()
                raise ValueError(f'weight hash mismatch: {name}')
            temporary.replace(path)
        print(f'{name}: {expected}')


if __name__ == '__main__':
    main()
