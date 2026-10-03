"""Download public model assets. Run once from a network-enabled terminal."""
from pathlib import Path
import hashlib, json, tarfile, urllib.request
ROOT = Path(__file__).resolve().parents[1]

def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    print('Downloading', path.name, flush=True)
    tmp = path.with_suffix(path.suffix + '.part')
    with urllib.request.urlopen(url, timeout=90) as response, tmp.open('wb') as out:
        while data := response.read(1024 * 1024):
            out.write(data)
    tmp.replace(path)

def main():
    base=ROOT/'models'; base.mkdir(exist_ok=True)
    lock=base/'depth_source.json'
    if lock.exists():
        rev=json.loads(lock.read_text())['revision']
    else:
        with urllib.request.urlopen('https://api.github.com/repos/DepthAnything/Depth-Anything-V2/commits/main',timeout=30) as r:
            rev=json.load(r)['sha']
        lock.write_text(json.dumps({'revision':rev,'source':'https://github.com/DepthAnything/Depth-Anything-V2'},indent=2))
    archive=base/f'depth-anything-{rev}.tar.gz'
    download(f'https://codeload.github.com/DepthAnything/Depth-Anything-V2/tar.gz/{rev}',archive)
    target=base/'depth-anything-source'
    if not target.exists():
        stage=base/'source-stage';stage.mkdir(exist_ok=True)
        with tarfile.open(archive) as tar:tar.extractall(stage,filter='data')
        next(p for p in stage.iterdir() if p.is_dir()).rename(target)
        stage.rmdir()
    name='depth_anything_v2_metric_hypersim_vits.pth'
    url='https://huggingface.co/depth-anything/Depth-Anything-V2-Metric-Hypersim-Small/resolve/main/'+name
    download(url,base/name)
    manifest={'model':'Depth Anything V2 Metric Hypersim Small','license':'Apache-2.0','source_revision':rev,
              'weights_url':url,'weights_sha256':hashlib.file_digest((base/name).open('rb'),'sha256').hexdigest()}
    (base/'depth_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Metric depth ready:',base/name)
if __name__=='__main__':main()
