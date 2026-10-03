"""Create a single submission ZIP from the five verified part archives.

Nested archives are stored once, without another copy of raw captures.
"""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
entries = {
    'Part_1_Capture_Routes_and_Input_Tiers.zip': OUT / 'Part_1_Capture_Routes_and_Input_Tiers.zip',
    'part_2.zip': OUT / 'part_2.zip',
    'part_3.zip': OUT / 'part_3.zip',
    'part_4.zip': OUT / 'part_4.zip',
    'part_5.zip': OUT / 'part_5.zip',
    'Applied_AI_Case_Study.pdf': ROOT / 'Applied_AI_Case_Study.pdf',
    'COMPLIANCE.md': ROOT / 'docs/COMPLIANCE.md',
    'benchmark.md': ROOT / 'reports/benchmark.md',
    'technical_report.pdf': ROOT / 'reports/technical_report.pdf',
    'technical_report.md': ROOT / 'reports/technical_report.md',
    'SUBMISSION_INDEX.md': ROOT / 'docs/SUBMISSION_INDEX.md',
}
for name, path in entries.items():
    if not path.is_file():
        raise FileNotFoundError(name)
    if path.suffix == '.zip':
        with zipfile.ZipFile(path) as nested:
            if nested.testzip():
                raise RuntimeError(f'Bad nested ZIP: {name}')
manifest=[]
for name,path in entries.items():
    h=hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):
            h.update(chunk)
    manifest.append({'file': name, 'bytes': path.stat().st_size, 'sha256': h.hexdigest()})
(OUT / 'FINAL_MANIFEST.json').write_text(json.dumps({'files': manifest}, indent=2) + '\n')
readme='''# Astra case study — final submission index

Unpack the top-level ZIP, then unpack each numbered part archive. Part 2 contains
raw benchmark captures and output-contract results. Part 4 contains original
before/after raw data and source snapshots. The same source capture appears in
both where the fix-loop evidence requires it; the top-level archive includes
each part ZIP exactly once.

1. Part 1: one-page Stray Scanner 1.4 capture protocol and device matrix.
2. Part 2: output contract, all declared benchmark runs, independent kitchen
   repeat, old and expanded raw scans, expanded automatic/assisted outputs,
   measured scores, drift ablation and reproduction commands.
3. Part 3: Magicplan kitchen/hall original PDFs, scored table and reproducible
   arithmetic. The 70% threshold is not met.
4. Part 4: unchanged original declarations, before/after runs, code diff,
   source audit and honest post-mortem. Exact historical photo-after replay is
   not fully proven.
5. Part 5: actual incremental Git bundle, commit history and verification.

Read COMPLIANCE.md and the six-page technical_report.pdf before scoring.
benchmark.md records measured failures and missing correspondence. The official
Round 1 schema was not supplied; result JSON uses astra.provisional.v1.
Public model weights are fetched by scripts in Part 2/4. No private API key,
Kaggle credential or hosted inference is required. Clean installation in under
15 minutes and the evaluator's unseen live capture remain unverified.

FINAL_MANIFEST.json records SHA-256 and byte size for each top-level file.
'''
(OUT / 'FINAL_README.md').write_text(readme)
target=OUT/'Astra_Final_Submission.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
    for name,path in entries.items():
        archive.write(path,name)
    archive.write(OUT/'FINAL_README.md','README.md')
    archive.write(OUT/'FINAL_MANIFEST.json','FINAL_MANIFEST.json')
with zipfile.ZipFile(target) as archive:
    if archive.testzip():raise RuntimeError('Final ZIP CRC failure')
    if len(archive.infolist())!=len(entries)+2:raise RuntimeError('Wrong archive file count')
h=hashlib.sha256()
with target.open('rb') as source:
    for chunk in iter(lambda:source.read(1024*1024),b''):h.update(chunk)
(OUT/'Astra_Final_Submission.zip.sha256').write_text(h.hexdigest()+'  '+target.name+'\n')
print('Final ZIP verified:',target,'bytes:',target.stat().st_size)
