"""Fail early on incompatible model libraries, before a long reconstruction."""
import os,sys,importlib.metadata
from pathlib import Path
root=Path(__file__).resolve().parents[1];os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
required={'numpy':'2.2.6','matplotlib':'3.10.6','torch':'2.8.0','torchvision':'0.23.0','transformers':'4.57.1','timm':'1.0.20'}
errors=[]
for name,expected in required.items():
    try:
        actual=importlib.metadata.version(name);print(name,actual)
        if actual.split('+')[0]!=expected:errors.append(f'{name}: tested {expected}, installed {actual}')
    except importlib.metadata.PackageNotFoundError:errors.append(f'{name}: missing')
try:
    import torch,torchvision
    from transformers import AutoProcessor,AutoModelForZeroShotObjectDetection
    print('Model imports valid; CUDA available:',torch.cuda.is_available())
except Exception as e:errors.append(f'Model import failed: {type(e).__name__}: {e}')
if errors:
    print('\n'.join(errors),file=sys.stderr);print('Restore the pinned environment using scripts/setup.sh --models. xFormers is optional and not required for CPU.',file=sys.stderr);sys.exit(1)
print('Tested dependency set verified.')
