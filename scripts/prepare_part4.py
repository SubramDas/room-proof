"""Package Part 4 with original declarations and measured, qualified fix evidence."""
from pathlib import Path
import subprocess,shutil,json,csv,hashlib,sys,difflib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'submission/part_4';OUT.mkdir(parents=True,exist_ok=True)
def write(p,s):
 p=OUT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.rstrip()+'\n')
def copy(src,dst):
 src=ROOT/src;dst=OUT/dst;dst.parent.mkdir(parents=True,exist_ok=True)
 if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.git'))
 else:shutil.copy2(src,dst)
def git(*args):return subprocess.check_output(['git','--git-dir='+str(ROOT/'.history'),'--work-tree='+str(ROOT),*args],stderr=subprocess.DEVNULL)
for name in ['declaration.md','photo_declaration.md']:copy('fix_loop/'+name,'01_original_declarations/'+name)
write('01_original_declarations/README.md','# Original declarations\n\nBoth original documents are preserved verbatim. They were committed together with initial implementation changes in 2b075a2; repository history alone does not independently establish the precise within-session ordering asserted in their text. The early LiDAR declaration describes a subset, not the worst gate of the complete benchmark. The later photo declaration identifies the largest observed extent error and unresolved stitching. No new successful prediction is retroactively substituted. These original documents exceed one combined page; see the separate one-page retrospective index for navigation, not as a replacement original declaration.')
pairs={'lidar_declared':('three_room_lidar','three_room_lidar_after'),'photos_declared':('three_room_photos','three_room_photos_final'),'kitchen_supporting':('kitchen_baseline','kitchen_lidar_final')}
rows=[];source_audit=[];revs=git('rev-list','--all').decode().split();cache={}
for pair,names in pairs.items():
 for phase,name in zip(['before','after'],names):
  copy('runs/'+name,f'02_runs/{pair}/{phase}')
  prov=json.loads((ROOT/'runs'/name/'provenance.json').read_text());rev=prov['code_revision']
  snap=OUT/f'05_reproduction/snapshots/{pair}_{phase}';snap.mkdir(parents=True,exist_ok=True)
  files=git('ls-tree','-r','--name-only',rev,'astra').decode().splitlines()
  for file in files:
   target=snap/file;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(git('show',rev+':'+file))
  missing=[]
  for file,h in prov.get('source_hashes',{}).items():
   if (file,h) not in cache:
    versions=[(ROOT/file).read_bytes()] if (ROOT/file).exists() else []
    for r in revs:
     try:versions.append(git('show',r+':'+file))
     except subprocess.CalledProcessError:pass
    cache[file,h]=next((b for b in versions if hashlib.sha256(b).hexdigest()==h),None)
   if cache[file,h] is None:missing.append(file)
   else:
    target=snap/file;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(cache[file,h])
  source_audit.append({'pair':pair,'phase':phase,'run':name,'recorded_revision':rev,'hashes_available':bool(prov.get('source_hashes')),'unrecoverable_hash_paths':missing,'snapshot_status':'revision_fallback_not_exact' if missing else 'matched_recorded_hashes' if prov.get('source_hashes') else 'recorded_revision_only'})
  d=json.loads((ROOT/'runs'/name/'result.json').read_text())
  mapping={'room_1':'room_1'} if pair=='kitchen_supporting' else {'room_1':'room_2','room_2':'room_1','room_3':'room_3'} if pair=='lidar_declared' else {'room_1':'room_1','room_2':'room_2','room_3':'room_3'}
  refs={'room_1':(2.3,2.36,2.8),'room_2':(3.3,4.2,2.8),'room_3':(.81,1.67,2.26)}
  for ref,pred in mapping.items():
   room=next(r for r in d['rooms'] if r['id']==pred);ext=sorted([room['extent_x']['value'],room['extent_z']['value']]);truth=refs[ref]
   for key,value,target in zip(['short_extent','long_extent','ceiling_height'],ext+[room['ceiling_height']['value']],truth):
    rows.append({'pair':pair,'phase':phase,'run':name,'reference_room':ref,'measurement':key,'reference_m':target,'prediction_m':value,'absolute_error_cm':100*abs(value-target),'relative_error_percent':100*abs(value-target)/target,'comparison':'height' if key=='ceiling_height' else 'sorted_extent_proxy_not_per_wall'})
  print('Packaged',name,flush=True)
# Exact originals were actually rerun; preserve their independent reproduction evidence.
for n in ['reproduced_original_lidar_before','reproduced_original_photo_before']:copy('runs/'+n,'02_runs/original_reproduction_checks/'+n)
copy('measurements.txt','03_comparison/measurements.txt')
write('05_reproduction/source_audit.json',json.dumps(source_audit,indent=2))
with (OUT/'03_comparison/metrics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write('03_comparison/metrics.json',json.dumps(rows,indent=2))
# Input equality across each declared pair, including every manifest item.
identity=[]
for pair,names in pairs.items():
 a=json.loads((ROOT/'runs'/names[0]/'input_manifest.json').read_text());b=json.loads((ROOT/'runs'/names[1]/'input_manifest.json').read_text())
 aa={r['path']:r['sha256'] for r in a};bb={r['path']:r['sha256'] for r in b}
 identity.append({'pair':pair,'all_manifest_hashes_equal':aa==bb,'before_files':len(a),'after_files':len(b)})
write('03_comparison/input_identity.json',json.dumps(identity,indent=2))
# Readable historical source diff and summary.
write('04_code_changes/baseline_to_latest_committed.diff',git('diff','e3977de','209371d','--','astra','scripts/fetch_models.py').decode())
write('04_code_changes/change_summary.md','''# Shipped changes and attribution

- Room boundaries: use supported structural wall planes instead of relying only on free-space watershed partitions; estimate floor/ceiling from local room support.
- RGB poses: depth-assisted PnP when supported by matched features; gravity alignment from dominant surface normals; explicit disconnected components.
- RGB depth/focal prior: Apple Depth Pro replaces the small Depth Anything model in the completed photo after run.
- Standalone kitchen pair: drift changes from off to on as well as code changes. Its height improvement cannot be attributed to the structural-plane change alone.

The diff is e3977de → 209371d. It includes later changes beyond the first targeted fix and is labelled accordingly. Per-run source recovery and missing historical file versions are recorded in `../05_reproduction/source_audit.json`. A code revision ID by itself does not guarantee a clean working tree at run time.
''')
# Current source for prospective reruns; recorded snapshots for historical attempts.
project=Path('05_reproduction/project')
for name in ['astra','requirements.txt','requirements-models.txt','schemas','models/README.md']:copy(name,project/name)
for name in ['setup.sh','fetch_models.py','fetch_semantic_models.py','check_environment.py']:copy('scripts/'+name,project/'scripts'/name)
for f in (ROOT/'models').glob('*.json'):copy(f.relative_to(ROOT),project/'models'/f.name)
copy('kitchen',project/'kitchen')
# Part 4 targets the earlier 5,351-frame scan. The workspace three_room/ path
# now contains a replacement 8,023-frame scan, so retain the archived original.
original=OUT/project/'three_room'
if not (original/'lidar/odometry.csv').exists():
 archived=ROOT/'submission/part_2/05_reproduction/project/three_room_original'
 if not (archived/'lidar/odometry.csv').exists():raise FileNotFoundError('Historical three-room capture unavailable')
 shutil.copytree(archived,original,dirs_exist_ok=True)
if not (OUT/project/'measurements.txt').exists():copy('measurements.txt',project/'measurements.txt')
write('05_reproduction/README.md','''# Reproduction

Raw kitchen and three_room data are included in project/. Public model weights are fetched by scripts; no private API or credential is needed. Set up from this directory:

```bash
cd project
bash scripts/setup.sh --models
.venv/bin/python scripts/fetch_models.py --depth-pro
.venv/bin/python scripts/check_environment.py
cd ..
bash reproduce_pairs.sh
```

The script runs all three before/after pairs from separate source directories. The stored config controls frame budgets, semantic views and drift settings. Outputs go into reruns/, preserving submitted evidence. CPU photo inference can take a long time. Set up downloads require network access; no clean-install time guarantee is claimed.

**Historical-source limitation:** four photo-after source files have hashes that cannot be recovered from the recorded commits or current files. That snapshot falls back to the recorded revision for those files and is explicitly not an exact reconstruction of the historical source. See source_audit.json. The current source is also included under project/astra for future reruns, but a new current-source run must not be represented as an exact replay of the saved photo-after numbers.

Before LiDAR/photo runs were actually reproduced from original revision e3977de; outputs are included under 02_runs/original_reproduction_checks/. Their reported dimensions match the original before outputs. A future clean-machine rerun of all historical after snapshots has not been verified. No exact historical-source reproduction claim is made for the saved photo-after result. A supplemental current-source replay is included when its run is available.
''')
write('05_reproduction/reproduce_pairs.sh','''#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
REPRO_BASE="$PWD"
PYTHON="$REPRO_BASE/project/.venv/bin/python"
for snapshot in snapshots/*; do
  if [[ ! -e "$snapshot/models" ]]; then ln -s "$REPRO_BASE/project/models" "$snapshot/models"; fi
done
mkdir -p reruns
run_snapshot() {
  local snapshot="$1"
  shift
  (cd "$REPRO_BASE/snapshots/$snapshot"; "$PYTHON" -m astra run "$@")
}
run_snapshot lidar_declared_before --tier lidar --input "$REPRO_BASE/project/three_room/lidar" --output "$REPRO_BASE/reruns/lidar_before" --capture-id three_room --max-frames 140 --semantic-views 12
run_snapshot lidar_declared_after --tier lidar --input "$REPRO_BASE/project/three_room/lidar" --output "$REPRO_BASE/reruns/lidar_after" --capture-id three_room --max-frames 140 --semantic-views 12 --layout-method planes
run_snapshot kitchen_supporting_before --tier lidar --input "$REPRO_BASE/project/kitchen/lidar" --output "$REPRO_BASE/reruns/kitchen_before" --capture-id kitchen --max-frames 100 --semantic-views 8 --single-room --drift off
run_snapshot kitchen_supporting_after --tier lidar --input "$REPRO_BASE/project/kitchen/lidar" --output "$REPRO_BASE/reruns/kitchen_after" --capture-id kitchen_lidar_final --max-frames 100 --semantic-views 8 --single-room --drift on --layout-method planes
run_snapshot photos_declared_before --tier photos --input "$REPRO_BASE/project/three_room" --output "$REPRO_BASE/reruns/photos_before" --capture-id three_room --semantic-views 9
# WARNING: recorded-revision fallback for unrecoverable historical hashes; not exact replay.
run_snapshot photos_declared_after --tier photos --input "$REPRO_BASE/project/three_room" --output "$REPRO_BASE/reruns/photos_after_revision_fallback" --capture-id three_room_photos_final --semantic-views 9 --depth-model depth-pro
''')
write('03_comparison/POSTMORTEM.md','''# Fix-loop results and post-mortem

## 1. Declared LiDAR subset fix

Kitchen height in the three-room scan: before 2.75350 m, after 2.75915 m, laser 2.80000 m. Absolute error improved **4.65 → 4.09 cm** (0.56 cm reduction). Prediction: ≤2 cm. Actual gate: ≤1.5 cm. **Prediction missed; gate still fails.** Hall error increased slightly, about 3.04 → 3.13 cm. Corridor error regressed from 1.46 → 6.72 cm. The boundary change helps extents but does not resolve ceiling bias and can select the wrong horizontal surface.

This early declaration used a LiDAR subset and was not the worst gate across the complete benchmark. The saved targeted after run has no recovered adjacency; later connectivity improvements are separate and must not be attributed to this particular artifact.

## 2. Declared photo reconstruction fix

The original declaration incorrectly identified corridor long extent 5.56 m vs 1.67 m (232.93%) as the worst. Rechecking all six extents shows the true baseline worst is corridor short extent 4.44 m vs 0.81 m, **448.15%**. The original declaration is preserved with this error disclosed. After Depth Pro plus pose/gravity changes, the worst of all six room extents is the corridor short extent 2.24 m vs 0.81 m, **176.54%**. This is a reduction of **271.60 percentage points**, but the below-100% prediction is missed and the ±8% gate still fails.

The originally highlighted corridor long extent improves to 3.20 m, **91.62% error**. Reporting only this dimension would omit the actual worst dimension both before and after. Kitchen long extent improves 7.60 → 2.772 m; hall short extent remains 7.28 m vs 3.30 m. The after output has **zero adjacency links**, three disconnected room components and a reported room overlap of approximately **7.004 m²**. There is no valid stitched whole-property result. The conditional connectivity prediction is not achieved on this capture.

Depth/focal and pose changes address some scale inflation, but sparse overlap, residual scale error and pose failures remain. No surveyed dimensions are fed back into inference. Intervals remain uncalibrated. The historical photo-after source hash gap means exact replay of these numbers is not established.

## 3. Supporting standalone kitchen improvement

Same original kitchen capture; kitchen_reproduce is excluded. Height changes 2.783779 → 2.792080 m against 2.80 m truth: error **1.62 → 0.79 cm**, crossing the 1.5 cm threshold. Floor-area error decreases approximately **24.9% → 9.3%**. This pair combines code changes and drift off → on. It is supporting evidence, not a retroactively declared worst-gate prediction and not proof that the general height gate is solved.

## Rubric assessment

Shipped changes and measured movement are supplied. The original LiDAR/photo before results were rerun successfully. Both declared predictions missed; photo stitching still fails. Full exact historical after-source regeneration is not demonstrated, especially for the original photo after run. No full-mark or fail-to-pass claim is made for the originally declared worst gate. A supplemental source-frozen replay is reported separately; it does not restore unavailable historical source bytes.
''')
write('README.md','''# Part 4 — The fix loop

Read `03_comparison/POSTMORTEM.md` first. This folder reports actual improvements, regressions, prediction misses and reproduction limitations.

- `01_original_declarations/`: original LiDAR and photo declarations, unchanged; retrospective one-page index is separately labelled.
- `02_runs/lidar_declared/{before,after}/`: targeted three-room LiDAR pair.
- `02_runs/photos_declared/{before,after}/`: original photo baseline and newly completed Depth Pro result.
- `02_runs/kitchen_supporting/{before,after}/`: same-capture standalone kitchen improvement; excludes kitchen_reproduce.
- `02_runs/original_reproduction_checks/`: original-code reruns verifying baseline dimensions.
- `03_comparison/`: all dimension errors, original laser reference, input-hash identity checks and post-mortem.
- `04_code_changes/`: readable diff and change summary.
- `05_reproduction/`: raw inputs, historical source snapshots, source-recovery audit, current source, setup/download scripts and rerun commands.

**Result:** measured photo worst extent error improves 448.15% → 176.54% (the original declaration misidentified the worst dimension as 232.93%), but target and stitch gate fail. Declared LiDAR kitchen height improves 4.65 → 4.09 cm and misses its prediction. Supporting standalone kitchen height improves 1.62 → 0.79 cm (local fail → pass), with drift settings also changed.

**Reproduction caveat:** the original before runs were reproduced, but four historical photo-after source hashes cannot be recovered. Its supplied snapshot is a labelled revision fallback, not an exact replay guarantee. A supplemental after run has a source-hash-matched snapshot; this does not restore the historical bytes. Original declaration chronology is preserved, not rewritten to predict observed successes.

Model binaries are not embedded; public fetch scripts are included. There are no private API keys. Consumer-app comparison remains Part 3; complete development history is Part 5.
''')
write('01_original_declarations/Retrospective_Index.md','''# Part 4 declaration index — retrospective

This is a navigation summary written after the runs, not a replacement or backdated fix declaration.

**Original documents:** declaration.md (early LiDAR subset); photo_declaration.md (first complete photo result). Both are preserved unchanged.

**Declared complete-tier failure:** photo whole-property reconstruction. The declaration highlighted corridor long extent error of 232.93% and no adjacency. Retrospective checking finds the true worst extent was the corridor short side: 4.44 m vs 0.81 m, 448.15% error. This declaration error is retained and disclosed.

**Original hypothesis:** focal/depth scale error, weak translation recovery in low-parallax images and incorrect gravity alignment. Evidence was inflated room dimensions and disconnected components.

**Original proposed fix:** depth-assisted PnP, surface-normal gravity alignment, and Apple Depth Pro for depth plus focal estimation. Prediction: worst extent error below 100%; at least one recovered connection if doorway overlap supports it.

**Measured outcome:** worst extent error becomes 176.54%; zero adjacency; prediction and required stitch gate fail. The highlighted long extent improves to 91.62% error; the short extent remains worst, improving 448.15% → 176.54%. See the post-mortem for all errors and source-recovery limitations.

**Separate supporting result:** standalone kitchen height error improves 1.62 → 0.79 cm, but this was not the declared worst-gate prediction and drift settings changed.
''')
replay=ROOT/'runs/three_room_photos_current_replay/result.json'
if replay.exists():
 copy('runs/three_room_photos_current_replay','02_runs/photos_current_source_replay')
 snapshot=OUT/'05_reproduction/snapshots/photos_current_source_replay'
 shutil.copytree(ROOT/'astra',snapshot/'astra',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
 recorded=json.loads((ROOT/'runs/three_room_photos_current_replay/source_manifest_at_start.json').read_text())['files']
 actual={str(p.relative_to(snapshot)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (snapshot/'astra').glob('*.py')}
 matched=actual==recorded
 if not matched:raise RuntimeError('Current photo replay source hashes differ from source at run start')
 before_manifest=json.loads((ROOT/'runs/three_room_photos/input_manifest.json').read_text())
 replay_manifest=json.loads((ROOT/'runs/three_room_photos_current_replay/input_manifest.json').read_text())
 same_inputs={x['path']:x['sha256'] for x in before_manifest}=={x['path']:x['sha256'] for x in replay_manifest}
 if not same_inputs:raise RuntimeError('Photo replay input files differ from baseline')
 audit={'source_hashes_match':True,'input_hashes_match_baseline':True,'input_files':len(before_manifest),'files':len(actual),'result':'02_runs/photos_current_source_replay/result.json','snapshot':'05_reproduction/snapshots/photos_current_source_replay/astra'}
 check=ROOT/'runs/three_room_photos_snapshot_verified/result.json'
 if check.exists():
  copy('runs/three_room_photos_snapshot_verified','02_runs/photos_source_snapshot_check')
  expected=json.loads(replay.read_text())
  observed=json.loads(check.read_text().replace(str(ROOT/'submission/part_4/05_reproduction/project/three_room'),'submission/part_4/05_reproduction/project/three_room'))
  same=expected==observed
  if not same:raise RuntimeError('Source snapshot replay changed result beyond input evidence path spelling')
  check_manifest=json.loads((check.parent/'input_manifest.json').read_text())
  if check_manifest!=replay_manifest:raise RuntimeError('Source snapshot replay input manifest differs')
  audit.update({'separate_snapshot_rerun':'02_runs/photos_source_snapshot_check/result.json','result_equal_after_input_path_normalization':True,'input_manifest_equal':True,'unmodified_result_equal':json.loads(check.read_text())==expected})
 write('05_reproduction/current_photo_replay_audit.json',json.dumps(audit,indent=2))
 replay_result=json.loads(replay.read_text())
 replay_rows=[]
 reference={'room_1':(2.3,2.36,2.8),'room_2':(3.3,4.2,2.8),'room_3':(.81,1.67,2.26)}
 for ref,(short,long,height) in reference.items():
  room=next(r for r in replay_result['rooms'] if r['id']==ref)
  predicted=sorted([room['extent_x']['value'],room['extent_z']['value']])+[room['ceiling_height']['value']]
  for key,value,target in zip(['short_extent','long_extent','ceiling_height'],predicted,[short,long,height]):
   replay_rows.append({'reference_room':ref,'measurement':key,'reference_m':target,'prediction_m':value,'absolute_error_cm':100*abs(value-target),'relative_error_percent':100*abs(value-target)/target})
 with (OUT/'03_comparison/current_photo_replay_metrics.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(replay_rows[0]));w.writeheader();w.writerows(replay_rows)
 with (OUT/'05_reproduction/reproduce_pairs.sh').open('a') as script:
  script.write('\n# Source-frozen supplemental photo after run (exact source hashes match).\nmkdir -p "$REPRO_BASE/reruns/photos_current_source_replay/geometry/depth_cache"\ncp -a "$REPRO_BASE/../02_runs/photos_current_source_replay/geometry/depth_cache/." "$REPRO_BASE/reruns/photos_current_source_replay/geometry/depth_cache/"\nrun_snapshot photos_current_source_replay --tier photos --input "$REPRO_BASE/project/three_room" --output "$REPRO_BASE/reruns/photos_current_source_replay" --capture-id three_room_photos_current_replay --semantic-views 9 --depth-model depth-pro\n')
 with (OUT/'03_comparison/POSTMORTEM.md').open('a') as report:
  report.write('\n## Supplemental source-frozen photo after run\n\nA later photo after run on the same original capture is included under `02_runs/photos_current_source_replay/`. Its exact source files are included under `05_reproduction/snapshots/photos_current_source_replay/`, and all recorded source hashes match the snapshot. The horizontal extents and heights match the earlier saved after output to displayed precision, including the 176.54% worst extent error. It still has zero adjacency links and an approximately 6.782 m² room overlap; the physical stitch fails. This supplements the historically unrecoverable photo-after source; it does not rewrite the original declaration or prove the earlier saved after source can be recovered exactly.\n')
 with (OUT/'README.md').open('a') as readme:
  readme.write('\nA supplemental current-source photo after run and hash-matched source snapshot are included under `02_runs/photos_current_source_replay/` and `05_reproduction/snapshots/photos_current_source_replay/`. See the replay audit and post-mortem.\n')
print('Part 4 assembled',flush=True)
