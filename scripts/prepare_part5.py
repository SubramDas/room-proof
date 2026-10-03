"""Refresh the Git process evidence after the final source commit.

This script reads only the alternate .history Git metadata used by this workspace.
Remote verification is a separate live SSH check after pushing the branch.
"""
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission/part_5'
OUT.mkdir(parents=True, exist_ok=True)
GIT = ['git', '--git-dir=.history', '--work-tree=.']


def run(*args):
    return subprocess.check_output([*GIT, *args], cwd=ROOT, text=True)


branch = run('branch', '--show-current').strip()
head = run('rev-parse', 'HEAD').strip()
if branch != 'final_implementation':
    raise RuntimeError(f'Unexpected branch: {branch}')
if run('status', '--porcelain').strip():
    raise RuntimeError('Commit source and report changes before sealing the bundle')

run('bundle', 'create', str(OUT / 'development.bundle'), branch)
(OUT / 'branch_head.txt').write_text(head + '\n')
(OUT / 'commit_history.txt').write_text(run('log', '--reverse', '--format=commit %H%nAuthor: %an <%ae>%nAuthorDate: %aI%nCommitDate: %cI%nSubject: %s%n'))
(OUT / 'history_with_stats.txt').write_text(run('log', '--reverse', '--stat', '--format=commit %H%nSubject: %s'))

with tempfile.TemporaryDirectory(prefix='astra-git-verify-') as temp:
    clone = Path(temp) / 'repo'
    subprocess.run(['git', 'clone', '-q', '-b', branch, str(OUT / 'development.bundle'), str(clone)], check=True)
    clone_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=clone, text=True).strip()
    fsck = subprocess.run(['git', 'fsck', '--full', '--no-reflogs'], cwd=clone, capture_output=True, text=True)
    if clone_head != head or fsck.returncode:
        raise RuntimeError('Bundle clone or object verification failed: ' + fsck.stdout + fsck.stderr)

(OUT / 'bundle_verification.json').write_text(json.dumps({
    'branch': branch, 'head': head, 'commit_count': int(run('rev-list', '--count', 'HEAD').strip()),
    'clone_head_matches': True, 'git_fsck_full': 'passed', 'working_tree_clean_at_bundle_time': True,
}, indent=2) + '\n')
(OUT / 'README.md').write_text(f'''# Part 5 — Process evidence

Repository: git@github.com:SubramDas/room-proof.git  
Branch: `{branch}`  
Submitted head: `{head}`

`development.bundle` contains the incremental Git branch. `commit_history.txt`
and `history_with_stats.txt` preserve actual author, dates, messages and changed
files. `bundle_verification.json` records an offline clone and full object check.
`PROCESS_EVIDENCE.md` discloses the alternate metadata and automated identity.

```bash
git clone -b {branch} development.bundle room-proof
cd room-proof
git log --reverse --oneline
```

Raw captures and model binaries are separate submission artifacts. The bundle
only tracks source and selected small reports. Remote state is recorded in
`remote_verification.json` after an SSH verification; do not infer it from the
local bundle alone.
''')

# The live remote result may be refreshed later by the orchestration step.
remote = OUT / 'remote_verification.json'
if remote.exists():
    old = json.loads(remote.read_text())
    if old.get('remote_head') != head:
        remote.write_text(json.dumps({'remote': 'git@github.com:SubramDas/room-proof.git',
                                      'branch': branch, 'local_head': head,
                                      'remote_head': None, 'status': 'pending_remote_check'}, indent=2) + '\n')

files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
(OUT / 'SHA256SUMS').write_text(''.join(
    f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in files))
target = OUT.parent / 'part_5.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
    for p in [*files, OUT / 'SHA256SUMS']:
        archive.write(p, Path('part_5') / p.name)
with zipfile.ZipFile(target) as archive:
    if archive.testzip():
        raise RuntimeError('Part 5 ZIP CRC failure')
print('Part 5 bundle and ZIP verified:', head)
