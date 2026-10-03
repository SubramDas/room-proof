"""Build a local allowlisted reproduction archive; never includes credentials."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--include-models',action='store_true');args=p.parse_args()
out=ROOT/'submission';out.mkdir(exist_ok=True)
subprocess.run(['git','--git-dir=.history','--work-tree=.','bundle','create',str(out/'development.bundle'),'--all'],cwd=ROOT,check=True)
roots=['README.md','IMPLEMENTATION_PLAN.md','Applied_AI_Case_Study.pdf','measurements.txt','requirements.txt','requirements-models.txt','astra','scripts','tests','configs','schemas','docs','reports','benchmarks','fix_loop','runs','kitchen','three_room','Crack_water','single_room','single_scan_floor_only','single_scan_with_ceiling','submission/development.bundle']
files=[]
for name in roots:
    path=ROOT/name
    if path.is_file():files.append(path)
    elif path.is_dir():files.extend(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.is_symlink())
models=ROOT/'models'
files.extend(p for p in models.iterdir() if p.is_file() and p.suffix in ['.json','.md'])
if args.include_models:
    for name in ['depth_anything_v2_metric_hypersim_vits.pth','depth_pro.pt','depth-anything-source','depth-pro-source','grounding-dino-tiny']:
        path=models/name
        if path.is_file():files.append(path)
        elif path.is_dir():files.extend(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.cache' not in p.parts)
# Detector cache accelerates exact replay, with a live inference path retained.
cache=ROOT/'.cache/detections'
if cache.exists():files.extend(cache.glob('*.json'))
files=sorted(set(files));manifest=[]
for f in files:
    with f.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    manifest.append({'path':str(f.relative_to(ROOT)),'bytes':f.stat().st_size,'sha256':digest})
mp=out/'MANIFEST.json';mp.write_text(json.dumps({'models_included':args.include_models,'files':manifest},indent=2)+'\n')
archive=out/'astra_reproduction.tar'
with tarfile.open(archive,'w') as tar:
    for f in files+[mp]:tar.add(f,arcname=str(Path('Astra_Project')/f.relative_to(ROOT)),recursive=False)
print(archive,archive.stat().st_size,'bytes')
