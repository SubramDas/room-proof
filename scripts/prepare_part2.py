"""Build an honest Part 2 evidence snapshot from saved outputs and original data."""
from pathlib import Path
import csv, hashlib, json, shutil, sys, datetime
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astra.schema import validate
from astra.evaluate import read_measurements, score, export_scores
OUT=ROOT/'submission/part_2'
OUT.mkdir(parents=True,exist_ok=True)
def write(path,text):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.rstrip()+'\n')
def copy(src,dst):
 src=ROOT/src;dst=OUT/dst
 dst.parent.mkdir(parents=True,exist_ok=True)
 if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.git','.DS_Store'))
 else:shutil.copy2(src,dst)
def table(path,rows):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
config=json.loads((ROOT/'configs/benchmark.json').read_text())
mappings=json.loads((ROOT/'configs/evaluation.json').read_text())['mappings']
truth=read_measurements(ROOT/'measurements.txt')
rows=[];dims=[];damage=[];scores=[];commands=[];validation=[]
for run in config['runs']:
 name=run['id'];src=ROOT/'runs'/name
 dataset='three_room' if name.startswith('three_room') else 'kitchen' if name.startswith('kitchen') else 'Crack_water' if name.startswith('damage') else name
 dest=Path('02_outputs')/dataset/run['tier']
 if (src/'result.json').exists():
  copy(Path('runs')/name,dest)
  stale=OUT/dest/'STATUS.md'
  if stale.exists():stale.unlink()
  result=json.loads((src/'result.json').read_text());validate(result)
  validation.append({'run':name,'schema':'astra.provisional.v1','validation':'passed','official_schema_validation':'unavailable'})
  state='completed_with_limitations'
  for r in result['rooms']:
   dims.append({'run':name,'tier':run['tier'],'room_id':r['id'],**{k:r.get(k,{}).get('value') for k in ['extent_x','extent_z','ceiling_height','floor_area']}})
  for d in result['damage']:
   damage.append({'run':name,'damage_id':d['id'],'class':d['class'],'surface_id':d['surface_id'],'status':d['status'],**{k:d.get(k,{}).get('value') for k in ['extent_width','extent_height','area']}})
  if name in mappings:scores.append(score(result,truth,mappings[name]))
  elif dataset in ['kitchen','three_room']:
   refs=['room_1'] if dataset=='kitchen' else ['room_1','room_2','room_3']
   scores.append(score(result,truth,{r:'UNRESOLVED_'+r for r in refs}))
  count=len(result['rooms']);openings=len(result['openings']);damages=len(result['damage'])
 else:
  state='incomplete_no_result';count=openings=damages=None
  write(dest/'STATUS.md',f'# Incomplete run: {name}\n\nNo completed result.json existed at packaging time. Any saved running status is not evidence of completion. No measurements or success claims are supplied for this entry.\n\nResume using the command in 05_reproduction/COMMANDS.md.')
  for f in ['run_status.json','progress.log','source_manifest_at_start.json']:
   if (src/f).exists():copy(Path('runs')/name/f,dest/('snapshot_'+f))
 rows.append({'run':name,'dataset':dataset,'tier':run['tier'],'status':state,'rooms':count,'opening_candidates':openings,'damage_candidates':damages,'output_folder':str(dest)})
 cmd=['.venv/bin/python','-m','astra','run','--capture-id',name,'--output','reruns/'+name]
 for key,val in run.items():
  if key=='id':continue
  if key=='input' and name.startswith('three_room'):
   val=str(val).replace('three_room/','three_room_original/',1) if str(val).startswith('three_room/') else 'three_room_original'
  if isinstance(val,bool):
   if val:cmd.append('--'+key.replace('_','-'))
  else:cmd+=['--'+key.replace('_','-'),str(val)]
 commands.append('### '+name+'\n\n```bash\n'+' '.join(cmd)+'\n```')
 print('Collected',name,state,flush=True)
# Preserve the later damage run separately; do not silently replace declared benchmark.
copy('runs/damage_lidar_verified','02_outputs/Crack_water/lidar_later_candidate')
validate(json.loads((ROOT/'runs/damage_lidar_verified/result.json').read_text()))
write('02_outputs/Crack_water/lidar_later_candidate/README.md','# Later damage candidate\n\nRun ID: damage_lidar_verified. The word verified in the historical directory name does not mean detections or metric extents are independently verified. This later run used 16 semantic views and foreground filtering. It is supplemental to the declared 10-view benchmark, not a silent replacement. Three staged candidates remain; surface assignment and false positives require checking.\n\nRerun from 05_reproduction/project:\n\n```bash\n.venv/bin/python -m astra run --tier lidar --input Crack_water/lidar --output reruns/damage_lidar_verified --capture-id damage_lidar_verified --max-frames 90 --semantic-views 16 --single-room --staged-damage\n```')
copy('runs/drift_ablation','04_drift_ablation')
copy('measurements.txt','01_reference/measurements.txt')
copy('benchmarks/reference_notes.md','01_reference/reference_notes.md')
copy('reports/data_audit.json','01_reference/data_audit.json');copy('reports/data_audit.md','01_reference/data_audit.md')
copy('configs/evaluation.json','01_reference/evaluation_mapping.json')
# A self-contained runnable layout retains raw-input paths used by the commands.
project=Path('05_reproduction/project')
for src in ['astra','schemas','configs','requirements.txt','requirements-models.txt','README.md','measurements.txt']:
 copy(src,project/src)
for name in ['setup.sh','fetch_models.py','fetch_semantic_models.py','check_environment.py','run_benchmarks.py','drift_ablation.py']:
 copy(Path('scripts')/name,project/'scripts'/name)
copy('scripts/refine_lidar_segments.py',project/'scripts/refine_lidar_segments.py')
for f in (ROOT/'models').glob('*'):
 if f.is_file() and f.suffix in ['.json','.md']:copy(f.relative_to(ROOT),project/'models'/f.name)
for name in ['kitchen','three_room','Crack_water','single_room','single_scan_floor_only','single_scan_with_ceiling']:
 print('Copying original data:',name,flush=True);copy(name,project/name)
# The declared 2026-10-03 baseline used an earlier scan. Its raw copy is retained
# in Part 4; never pair that old result with the replacement scan at three_room/.
old_scan=ROOT/'submission/part_4/05_reproduction/project/three_room'
if not (old_scan/'lidar/odometry.csv').exists():raise FileNotFoundError('Old three-room raw capture is required for reproduction')
shutil.copytree(old_scan,OUT/project/'three_room_original',dirs_exist_ok=True)
# The new 8,023-frame scan is supplemental and both automatic and assisted layouts
# are preserved. The assisted result uses visual frame ranges, not reference sizes.
for run_name,dest_name in [('three_room_expanded_lidar','lidar_automatic'),('three_room_expanded_assisted','lidar_assisted')]:
 copy(Path('runs')/run_name,Path('02_outputs/three_room_expanded')/dest_name)
 validate(json.loads((ROOT/'runs'/run_name/'result.json').read_text()))
 validation.append({'run':run_name,'schema':'astra.provisional.v1','validation':'passed','official_schema_validation':'unavailable'})
 result=json.loads((ROOT/'runs'/run_name/'result.json').read_text())
 rows.append({'run':run_name,'dataset':'three_room_expanded','tier':'lidar','status':'supplemental_assisted' if 'assisted' in run_name else 'supplemental_automatic','rooms':len(result['rooms']),'opening_candidates':len(result['openings']),'damage_candidates':len(result['damage']),'output_folder':str(Path('02_outputs/three_room_expanded')/dest_name)})
 for room in result['rooms']:
  dims.append({'run':run_name,'tier':'lidar','room_id':room['id'],**{k:room.get(k,{}).get('value') for k in ['extent_x','extent_z','ceiling_height','floor_area']}})
 if 'assisted' in run_name:
  scores.append(score(result,truth,{'room_1':'kitchen','room_2':'hall','room_3':'room_2','bedroom':'bedroom'}))
for run_name,tier in [('three_room_expanded_photos','photos'),('three_room_expanded_video','video')]:
 path=ROOT/'runs'/run_name/'result.json'
 if not path.exists():continue
 result=json.loads(path.read_text());validate(result)
 validation.append({'run':run_name,'schema':'astra.provisional.v1','validation':'passed','official_schema_validation':'unavailable'})
 dest=Path('02_outputs/three_room_expanded')/tier
 copy(Path('runs')/run_name,dest)
 rows.append({'run':run_name,'dataset':'three_room_expanded','tier':tier,'status':'supplemental_completed_with_limitations','rooms':len(result['rooms']),'opening_candidates':len(result['openings']),'damage_candidates':len(result['damage']),'output_folder':str(dest)})
 for room in result['rooms']:
  dims.append({'run':run_name,'tier':tier,'room_id':room['id'],**{k:room.get(k,{}).get('value') for k in ['extent_x','extent_z','ceiling_height','floor_area']}})
 if tier=='photos':scores.append(score(result,truth,{'room_1':'kitchen','room_2':'hall','room_3':'connector','bedroom':'bedroom'}))
export_scores(scores,OUT/'03_evaluation/measured_scores')
table('03_evaluation/execution.csv',rows);table('03_evaluation/room_dimensions.csv',dims)
if damage:table('03_evaluation/damage_candidates.csv',damage)
write('03_evaluation/schema_validation.json',json.dumps(validation,indent=2))
copy('docs/THREE_ROOM_EXPANDED_RESULTS.md','02_outputs/three_room_expanded/RESULTS.md')
write('05_reproduction/INPUT_VERSIONS.md','''# Scan identity and commands

`three_room_original/` is the earlier 5,351-frame property scan used by declared
`three_room_*_final` outputs and the Part 4 fix loop. `three_room/` is the later
8,023-frame scan with the bedroom and renamed photo folders. The replacement
scan is **not** the raw input for earlier saved outputs.

To reproduce an earlier result, replace `three_room` in its listed input path
with `three_room_original`. The archived run's `input_manifest.json` is the
authority for input identity. The current source has evolved; exact historical
numbers are not guaranteed from current source. Part 4 contains historical
source snapshots and its documented replay limitations.

New scan, automatic:

```bash
.venv/bin/python -m astra run --tier lidar --input three_room/lidar --output reruns/three_room_expanded_lidar --max-frames 240 --semantic-views 12 --capture-id three_room_expanded
```

New scan, visually assisted four-space layout:

```bash
.venv/bin/python scripts/refine_lidar_segments.py --source reruns/three_room_expanded_lidar --segments configs/three_room_expanded_segments.json --output reruns/three_room_expanded_assisted
```

New scan RGB-only tiers:

```bash
.venv/bin/python -m astra run --tier photos --input three_room --output reruns/three_room_expanded_photos --depth-model depth-pro --semantic-views 9 --capture-id three_room_expanded_photos
.venv/bin/python -m astra run --tier video --input three_room/lidar/rgb.mp4 --output reruns/three_room_expanded_video --rotation 90 --max-frames 64 --semantic-views 8 --depth-model small --capture-id three_room_expanded_video
```

The assisted room frame ranges are disclosed in the config and the result.
''')
identity=[]
identity_cases=[
 ('three_room_lidar_final',OUT/project/'three_room_original/lidar'),
 ('three_room_photos_final',OUT/project/'three_room_original'),
 ('three_room_video_final',OUT/project/'three_room_original/lidar'),
 ('three_room_expanded_lidar',OUT/project/'three_room/lidar')]
for run_name,raw_base in [('three_room_expanded_photos',OUT/project/'three_room'),('three_room_expanded_video',OUT/project/'three_room/lidar')]:
 if (ROOT/'runs'/run_name/'input_manifest.json').exists():identity_cases.append((run_name,raw_base))
for run_name,raw_base in identity_cases:
 expected=json.loads((ROOT/'runs'/run_name/'input_manifest.json').read_text())
 missing=[];mismatch=[]
 for row in expected:
  p=raw_base/row['path']
  if not p.is_file():missing.append(row['path']);continue
  if p.stat().st_size!=row['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:mismatch.append(row['path'])
 identity.append({'run':run_name,'raw_root':str(raw_base.relative_to(OUT)),
                  'manifest_items':len(expected),'all_hashes_match':not missing and not mismatch,
                  'missing':missing,'mismatch':mismatch})
 if missing or mismatch:raise RuntimeError(f'Input mismatch for {run_name}: {len(missing)} missing, {len(mismatch)} changed')
write('05_reproduction/input_identity_audit.json',json.dumps(identity,indent=2))
write('05_reproduction/COMMANDS.md','# Setup and one command per capture\n\nRun these commands from `05_reproduction/project/`. Python 3.12 and network access for public dependencies/models are required. CPU inference is supported; no API key or Kaggle credential is required.\n\n```bash\nbash scripts/setup.sh --models\n.venv/bin/python scripts/fetch_models.py --depth-pro\n.venv/bin/python scripts/check_environment.py\n```\n\nDownloads can be several GB. Clean setup under 15 minutes has not been verified. The archive includes raw captures and current source but excludes installed environments and model weight binaries; public download scripts and model manifests are included.\n\nSaved outputs retain their original provenance. Current-source reruns may differ from earlier outputs because source evolved; exact historical numerical reproduction is not claimed by this Part 2 snapshot. Output caches have been preserved within completed run folders but are not automatically installed into reruns. Timings from cached or concurrent runs are not cold-run benchmarks.\n\n'+ '\n\n'.join(commands)+'\n\n## Drift ablation\n\n```bash\n.venv/bin/python scripts/drift_ablation.py --input three_room/lidar --max-frames 140 --output reruns/drift_ablation\n```\n\n## Validate a saved result\n\n```bash\n.venv/bin/python -m astra validate ../../02_outputs/three_room/lidar/result.json\n```\n\nThis validates the provisional schema and internal invariants, not geometry accuracy or the missing official schema.')
write('03_evaluation/UNAVAILABLE_EVIDENCE.md','''# Evidence that is not established

| Requirement | Status / reason |
|---|---|
| Exhaustive opening score, including misses/phantoms | Room-level doorway values supplied, but no exhaustive opening IDs, counts, wall offsets or reference correspondences. Candidates are not scored as correct detections. |
| Per-wall ±8% photo / ±3% video accuracy | Current table uses sorted horizontal extent proxies, not corresponding physical walls. RGB geometry failures remain. |
| Repeatability ≤1 cm or 0.5% per wall | Independent kitchen repeat supplied and extent proxies scored; physical wall correspondence is missing and the long extent proxy fails. |
| Repeated height spread ≤1 cm | Kitchen repeat spread is 3.10 cm, so this gate fails. |
| Empirical interval calibration at each tier | No independent calibration and test scenes; engineering intervals only. |
| Damage class and extent accuracy | Staged black/brown props; no independent measured masks/prop extents; natural damage recognition unvalidated. |
| Complete Round 1 contract / published schema | Not supplied; local provisional schema only. |
| Three rooms plus connector | The newer raw scan contains bedroom, kitchen, hall and connector; automatic LiDAR extraction merged hall and kitchen. A visually assisted four-space output is supplied separately. |
| Complete three-room and damage photo results | Earlier capture photo runs are complete, but physical multi-room stitching fails. The replacement photo result, if completed, is listed separately in execution.csv and must be assessed on its own stitch diagnostics. |
| Full geometry/height truth for evaluator samples | Not supplied; execution evidence only. |

The one standalone kitchen LiDAR height result is within 1.5 cm of its reference; all three heights in the earlier multi-room LiDAR result exceed 1.5 cm error. This is not an overall height-gate pass. No confidence-interval calibration, opening gate, or whole-property RGB gate is claimed as passed.
''')
write('04_drift_ablation/README.md','''# Drift accountability

The pipeline adds accepted local and loop ICP constraints to a pose correction graph; it does not use all recorded poses unchanged. `ablation.json` records accepted constraints and corrections. `footprint_comparison.png` / `.svg` overlay the same scan with correction off and on. `off/` and `on/` contain layouts, point clouds, correction diagnostics and input QA.

Observed summed room area: off 20.808618 m², on 20.802035 m² (change −0.006583 m²). Maximum translation correction was approximately 8.89 cm. Summed room area is not necessarily the property union footprint. This ablation shows the algorithm changes the reconstruction; it does not prove improved ground-truth accuracy and is not a repeatability test.

Rerun instructions are in `../05_reproduction/COMMANDS.md`.
''')
write('00_REQUIREMENTS_AND_STATUS.md','''# Part 2 requirements → evidence → status

Source: Applied_AI_Case_Study.pdf, Part 2, printed pages 1–2. Later consumer-app comparison and fix-loop requirements belong to Parts 3 and 4.

| Required submission | Included evidence | Status |
|---|---|---|
| Per-room dimensioned walls, ceiling height, floor area, openings | `02_outputs/<dataset>/<tier>/result.json`, `rooms/`, `plan.pdf`, `report.html` | Present for completed runs; incomplete observations and inaccurate candidates remain. |
| Stitched property with correct adjacency, every tier | Results' adjacency/layout_quality and whole-property plans | Three-room LiDAR connected; RGB physical stitching unresolved. No all-tier pass. |
| Per-surface damage classes and metric extent | Result damage arrays, `surfaces/`, `semantics/overlays/` | Staged demonstration; false positives, extent and assignment accuracy unvalidated; general nonwall association incomplete. |
| Concealed flags and fired rules | Result concealed_damage_flags | Implemented inspection rules; staged results have no concealed flags. Not proof of absent hidden damage. |
| Scope lines keyed to surfaces | Result scope_items | Provisional inspection scope. Official Round 1 scope unknown. |
| Confidence interval for every measurement | Measurement interval objects in JSON | Engineering ranges, not empirically calibrated. Unobserved values are null. |
| Published-schema JSON | `05_reproduction/project/schemas/result.schema.json`; validation table | Provisional local schema passes for packaged results; official schema unavailable. |
| One command per capture and rendered plan | `05_reproduction/COMMANDS.md`; each completed output folder | Included. Missing-run entries have status documents only. |
| ≥3 rooms plus connector | Raw `three_room/`, earlier `three_room_original/`, expanded LiDAR outputs | Raw composition now present; automatic segmentation merges hall and kitchen. Assisted four-space output supplied. |
| Furnished room, staged damage in two classes | Raw `Crack_water/` and outputs | Black crack/brown waterlogging staging supplied; recognition accuracy unvalidated. |
| Same spaces at all three tiers | Raw folders and execution.csv | Earlier benchmark tiers completed; new four-space capture has LiDAR and photos, but no separate completed photo/video reconstruction. |
| Independent repeats and laser/tape ground truth on everything | `01_reference/measurements.txt`; kitchen_repeat; unavailable-evidence table | Independent kitchen repeat supplied. Partial laser room/doorway measurements; exhaustive surface/opening/damage truth absent. |
| Openings ≤2 cm on ≥85%, misses/phantoms included | Candidate outputs; unavailable-evidence table | Not established; false candidates remain and exhaustive truth absent. |
| Height ≤1.5 cm; repeated spread ≤1 cm | `03_evaluation/measured_scores/`; kitchen_repeat | Multi-room LiDAR height gate failed; kitchen repeat height spread 3.10 cm fails. |
| Repeat wall agreement ≤1 cm or 0.5% | kitchen_repeat; unavailable-evidence table | Extent proxy long side fails; full physical wall matching unavailable. |
| Actual drift correction and on/off footprint | `04_drift_ablation/` | Executed and supplied; accuracy improvement not demonstrated. |
| Photo footprint ±8%, correct adjacency, no overlaps | Plans/layout diagnostics | Not established. |
| Photo walls ±8%; video walls ±3%; calibrated intervals | Proxy measurement table and raw results | Full gates not established; interval calibration incomplete. |

Successful execution or JSON validation is not a geometry-accuracy pass. No missing result is replaced by a fabricated output.
''')
write('README.md',f'''# Part 2 — Output contract and accuracy gates

This is an evidence snapshot, not a claim that all Part 2 gates passed.

## Start here

1. Read `00_REQUIREMENTS_AND_STATUS.md` for the PDF requirements and artifact locations.
2. Open `02_outputs/three_room_expanded/lidar_automatic/plan.pdf` and `lidar_assisted/plan.pdf` for the new four-space capture. `02_outputs/three_room/lidar/` is the earlier scan.
3. Open `02_outputs/Crack_water/lidar_later_candidate/report.html` for the later staged-damage example; the declared benchmark is separately preserved in `lidar/`.
4. Read `03_evaluation/measured_scores/benchmark.md`, `execution.csv` and `UNAVAILABLE_EVIDENCE.md`.
5. View `04_drift_ablation/footprint_comparison.png` and its README.
6. Use `05_reproduction/COMMANDS.md` and `INPUT_VERSIONS.md` to set up and rerun the matching capture.

## Folder contents

- `01_reference/`: updated laser measurements, room mapping, input audit and dataset discrepancies.
- `02_outputs/`: per-dataset/per-tier saved JSON, plans, room/surface renders, image overlays, diagnostic data, logs and provenance. Incomplete runs have explicit status files.
- `03_evaluation/`: refreshed measurements, execution inventory, dimensions/damage CSVs, schema validation and missing evidence.
- `04_drift_ablation/`: drift on/off layouts and footprint comparison.
- `05_reproduction/project/`: earlier raw `three_room_original/`, replacement raw `three_room/`, other original captures, runnable current source, schema, configs and public model-download scripts.
- `MANIFEST_SHA256.csv`: path, byte size and SHA-256 for every other file in this folder.

**Completed declared benchmark outputs:** {sum(r['status']=='completed_with_limitations' for r in rows)}/{len(rows)}. A separate later damage LiDAR run and the new bedroom scan are supplemental. The earlier and replacement scan raw files are kept under distinct names. The evaluator sample scans are extra execution evidence, not independently measured benchmark passes.

**Known limits:** RGB stitching and scale errors; multi-room ceiling errors; opening false positives; unverified damage extents; uncalibrated intervals; missing official schema; failed kitchen height repeatability; automatic room merge on the new scan. See the checklist for details.

This section includes raw inputs, but downloadable weights are not embedded. Full historical regeneration, fix-loop history, consumer-app comparison and the final six-page technical report belong in the corresponding project deliverables. No keys, tokens or local virtual environment are included.

Snapshot time (UTC): {datetime.datetime.now(datetime.timezone.utc).isoformat()}
''')
timings=[]
for row in rows:
 p=OUT/row['output_folder']/'provenance.json'
 if p.exists():
  d=json.loads(p.read_text())
  timings.append({'run':row['run'],'runtime_seconds':json.loads((p.parent/'run_status.json').read_text()).get('runtime_seconds'), 'peak_rss_mb':d.get('max_rss_mb'),'timing_context':'saved run; caching/concurrent execution may apply'})
if timings:table('03_evaluation/timing.csv',timings)
print('Hashing submission files',flush=True)
manifest=[]
for p in sorted(OUT.rglob('*')):
 if not p.is_file() or p.name=='MANIFEST_SHA256.csv':continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 manifest.append({'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
table('MANIFEST_SHA256.csv',manifest)
print('Part 2 ready:',OUT,'files:',len(manifest),'bytes:',sum(r['bytes'] for r in manifest),flush=True)
