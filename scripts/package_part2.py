"""Hash the Part 2 folder, create its ZIP, and verify every archived member."""
from pathlib import Path
import csv,hashlib,zipfile,argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--part',choices=['part_2','part_3','part_4'],default='part_2');args=parser.parse_args()
folder=ROOT/'submission'/args.part
manifest=folder/'MANIFEST_SHA256.csv'
files=sorted(p for p in folder.rglob('*') if p.is_file() and p!=manifest)
with manifest.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader()
 for p in files:
  h=hashlib.sha256()
  with p.open('rb') as source:
   for block in iter(lambda:source.read(1024*1024),b''):h.update(block)
  w.writerow({'path':str(p.relative_to(folder)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
print('File hashes recorded:',len(files),flush=True)
target=folder.parent/(args.part+'.zip')
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
 for p in files+[manifest]:z.write(p,Path(args.part)/p.relative_to(folder))
print('ZIP written, verifying all entries...',flush=True)
with zipfile.ZipFile(target) as z:
 bad=z.testzip()
 if bad:raise RuntimeError('Archive CRC failure: '+bad)
 assert len(z.infolist())==len(files)+1
h=hashlib.sha256()
with target.open('rb') as f:
 for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
target.with_suffix('.zip.sha256').write_text(h.hexdigest()+'  '+target.name+'\n')
print('Verified ZIP:',target,'bytes:',target.stat().st_size,flush=True)
