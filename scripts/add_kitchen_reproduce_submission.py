"""Add the user's new kitchen capture to an existing Part 2 snapshot."""
from pathlib import Path
import argparse,csv,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from astra.schema import validate
from astra.evaluate import read_measurements,score,export_scores
p=argparse.ArgumentParser();p.add_argument('--same-kitchen-confirmed',action='store_true');a=p.parse_args()
OUT=ROOT/'submission/part_2';src=ROOT/'runs/kitchen_reproduce';dst=OUT/'02_outputs/kitchen_reproduce/lidar'
d=json.loads((src/'result.json').read_text());validate(d)
prov=json.loads((src/'provenance.json').read_text());raw=Path(prov['input_root'])
manifest=json.loads((src/'input_manifest.json').read_text())
rawdst=OUT/'05_reproduction/project/kitchen_reproduce/lidar'
shutil.copytree(src,dst,dirs_exist_ok=True)
rawdst.mkdir(parents=True,exist_ok=True)
# Only copy declared capture files; never sweep arbitrary Downloads contents.
for item in manifest:
 rel=Path(item['path']);assert not rel.is_absolute() and '..' not in rel.parts
 f=raw/rel;dest=rawdst/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==item['sha256'],str(f)
 shutil.copy2(f,dest)
print('Verified and copied raw manifest entries:',len(manifest),flush=True)
base=json.loads((ROOT/'runs/kitchen_lidar_final/result.json').read_text())
first=base['rooms'][0];second=d['rooms'][0]
oldm=json.loads((ROOT/'runs/kitchen_lidar_final/input_manifest.json').read_text())
video=lambda m:next(x['sha256'] for x in m if x['path']=='rgb.mp4')
assert video(oldm)!=video(manifest)
before=sorted([first['extent_x']['value'],first['extent_z']['value']]);after=sorted([second['extent_x']['value'],second['extent_z']['value']])
records=[]
for key,x,y in [('short_extent',before[0],after[0]),('long_extent',before[1],after[1]),('ceiling_height',first['ceiling_height']['value'],second['ceiling_height']['value'])]:
 limit=.01 if key=='ceiling_height' else max(.01,.005*x)
 records.append({'measurement':key,'first_m':x,'second_m':y,'absolute_delta_m':abs(y-x),'limit_m':limit,'within_proxy_limit':abs(y-x)<=limit,'comparison':'height' if key=='ceiling_height' else 'sorted_extent_proxy_not_matched_wall'})
evaldir=OUT/'03_evaluation/kitchen_repeat';evaldir.mkdir(parents=True,exist_ok=True)
status='same kitchen and laser dimensions confirmed by operator' if a.same_kitchen_confirmed else 'same physical kitchen and laser dimensions await operator confirmation'
report={'status':status,'first_capture':'kitchen_lidar_final','second_capture':'kitchen_reproduce','different_video_hashes':True,'reference_length_for_relative_limit':'first capture','records':records,'full_per_wall_gate':'not established: matched physical wall IDs absent','source_caveat':'Saved outputs may reflect different source snapshots; compare provenance before attributing differences solely to capture.'}
(evaldir/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
with (evaldir/'comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
lines=['# Kitchen repeat capture comparison','',status+'.','','Two distinct raw video hashes are preserved. Sorted room extents are proxies; no complete per-wall repeatability pass is claimed. Limits use max(1 cm, 0.5% of the first measurement); repeated height uses 1 cm.','','| Measurement | First m | New m | Difference cm | Limit cm | Proxy outcome |','|---|---:|---:|---:|---:|---|']
for r in records:lines.append(f"| {r['measurement']} | {r['first_m']:.4f} | {r['second_m']:.4f} | {100*r['absolute_delta_m']:.2f} | {100*r['limit_m']:.2f} | {'within limit' if r['within_proxy_limit'] else 'FAIL'} |")
lines+=['','The longer extent and ceiling height vary beyond their limits. Physical wall correspondence is still needed for the full wall repeatability gate. Inspect both provenance files: saved-run differences are not a controlled same-source repeatability experiment.']
if a.same_kitchen_confirmed:
 export_scores([score(d,read_measurements(ROOT/'measurements.txt'),{'room_1':'room_1'})],evaldir/'laser_comparison')
 lines+=['','Against the confirmed 2.80 m laser height, the new estimate is 3.89 cm low, outside the 1.5 cm height gate. The 3.10 cm between-run height spread also exceeds 1 cm. This is evidence of both error and variation in these outputs; it does not isolate the cause.']
(evaldir/'README.md').write_text('\n'.join(lines)+'\n')
command='.venv/bin/python -m astra run --tier lidar --input kitchen_reproduce/lidar --output reruns/kitchen_reproduce --capture-id kitchen_reproduce --single-room --max-frames 100 --semantic-views 8'
(dst/'README.md').write_text('# Kitchen reproduction run\n\nUser-provided new capture; complete_with_limitations. Original logs, source/config provenance, plans and JSON are preserved. Raw LiDAR files are included under `05_reproduction/project/kitchen_reproduce/lidar/` and were verified against the run input manifest. This addition does not include or claim inference over accompanying new photos.\n\n'+status+'.\n\nRun from `05_reproduction/project`:\n\n```bash\n'+command+'\n```\n')
def upsert_csv(path,new,key):
 rows=list(csv.DictReader(path.open()));fields=list(rows[0]) if rows else list(new)
 rows=[r for r in rows if r.get(key)!=new[key]];rows.append(new)
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
upsert_csv(OUT/'03_evaluation/execution.csv',{'run':'kitchen_reproduce','dataset':'kitchen_reproduce','tier':'lidar','status':'completed_with_limitations','rooms':len(d['rooms']),'opening_candidates':len(d['openings']),'damage_candidates':len(d['damage']),'output_folder':'02_outputs/kitchen_reproduce/lidar'},'run')
for r in d['rooms']:upsert_csv(OUT/'03_evaluation/room_dimensions.csv',{'run':'kitchen_reproduce','tier':'lidar','room_id':r['id'],**{k:r[k]['value'] for k in ['extent_x','extent_z','ceiling_height','floor_area']}},'run')
timing=OUT/'03_evaluation/timing.csv'
upsert_csv(timing,{'output_folder':'02_outputs/kitchen_reproduce/lidar','runtime_seconds':json.loads((src/'run_status.json').read_text())['runtime_seconds'],'peak_rss_mb':prov.get('max_rss_mb'),'timing_context':'user-run reproduction; see provenance'},'output_folder')
vpath=OUT/'03_evaluation/schema_validation.json';v=json.loads(vpath.read_text());v=[r for r in v if r['run']!='kitchen_reproduce'];v.append({'run':'kitchen_reproduce','schema':'astra.provisional.v1','validation':'passed','official_schema_validation':'unavailable'});vpath.write_text(json.dumps(v,indent=2)+'\n')
for name in ['README.md','00_REQUIREMENTS_AND_STATUS.md','03_evaluation/UNAVAILABLE_EVIDENCE.md']:
 path=OUT/name;text=path.read_text()
 text=text.replace('Independent repeat scans deferred; no repeatability score.', 'New kitchen LiDAR capture added; see kitchen_repeat/README.md for confirmation status, proxy differences and remaining wall correspondence requirement.')
 text=text.replace('Not measured; a repeat from identical files is not an independent capture.', 'New kitchen output height differs by 3.10 cm; see kitchen_repeat/README.md. Same-room confirmation and source consistency qualify interpretation.')
 text=text.replace('Independent repeat scans deferred', 'Kitchen repeat candidate added')
 text=text.replace('Reproduction', 'Reproduction')
 marker='\n## Kitchen reproduction update\n'
 if marker in text:text=text.split(marker)[0]
 text+=marker+'\nAdded `02_outputs/kitchen_reproduce/lidar/` and its verified raw LiDAR input. See `03_evaluation/kitchen_repeat/README.md` for the updated repeat evidence. '+status+'. Earlier deferred-repeat statements describe the original snapshot and are superseded by this update. This supplemental run does not complete the two missing photo benchmarks.\n'
 path.write_text(text)
commands=OUT/'05_reproduction/COMMANDS.md';text=commands.read_text();marker='\n## New kitchen reproduction\n'
if marker in text:text=text.split(marker)[0]
commands.write_text(text+marker+'\nRun from `05_reproduction/project/`:\n\n```bash\n'+command+'\n```\n')
print('Added new kitchen output, raw data, execution/measurement/timing/schema rows, comparison and commands.',flush=True)
