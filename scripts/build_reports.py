"""Regenerate benchmark tables, compliance matrix and six-page technical PDF."""
import os,sys,json,textwrap,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
from astra.evaluate import read_measurements,score,export_scores
from astra.io import write_json
from astra.schema import validate
out=ROOT/'reports';out.mkdir(exist_ok=True)
truth=read_measurements(ROOT/'measurements.txt');config=json.loads((ROOT/'configs/benchmark.json').read_text());maps=json.loads((ROOT/'configs/evaluation.json').read_text())['mappings']
scores=[];runs={};timings=[]
for item in config['runs']:
    name=item['id'];folder=ROOT/'runs'/name;path=folder/'result.json'
    if not path.exists():runs[name]={'state':'not_completed','tier':item['tier']};continue
    result=json.loads(path.read_text());validate(result);prov=json.loads((folder/'provenance.json').read_text());runs[name]={'state':'executed','result':result,'provenance':prov,'tier':item['tier']}
    if name in maps:scores.append(score(result,truth,maps[name]))
    elif name=='three_room_video_final':scores.append(score(result,truth,{r:None for r in ['room_1','room_2','room_3']}))
    elif name=='kitchen_video_final':scores.append(score(result,truth,{'room_1':None}))
    timings.append({'run':name,'tier':item['tier'],'seconds':prov['wall_time_seconds'],'max_rss_mb':prov['max_rss_mb'],'device':prov['config']['device'],'code_revision':prov['code_revision']})
supplemental=[('three_room_expanded_lidar','lidar'),('three_room_expanded_assisted','lidar'),('three_room_expanded_photos','photos'),('three_room_expanded_video','video')]
for name,tier in supplemental:
    folder=ROOT/'runs'/name;path=folder/'result.json'
    if not path.exists():continue
    result=json.loads(path.read_text());validate(result)
    prov=json.loads((folder/'provenance.json').read_text()) if (folder/'provenance.json').exists() else None
    runs[name]={'state':'supplemental_assisted' if 'assisted' in name else 'supplemental_executed','result':result,'provenance':prov,'tier':tier}
    if name=='three_room_expanded_assisted':scores.append(score(result,truth,{'room_1':'kitchen','room_2':'hall','room_3':'room_2','bedroom':'bedroom'}))
    if name=='three_room_expanded_photos':scores.append(score(result,truth,{'room_1':'kitchen','room_2':'hall','room_3':'connector','bedroom':'bedroom'}))
    if prov and 'wall_time_seconds' in prov:
        timings.append({'run':name,'tier':tier,'seconds':prov['wall_time_seconds'],'max_rss_mb':prov['max_rss_mb'],'device':prov['config']['device'],'code_revision':prov['code_revision']})
export_scores(scores,out);write_json(out/'timing.json',timings)
with (out/'benchmark.md').open('a') as f:
    f.write('\n## Execution and topology\n\n| Run | Execution | Rooms | Opening candidates | Damage regions | Layout status |\n|---|---|---:|---:|---:|---|\n')
    for name,item in runs.items():
        r=item.get('result',{});q=r.get('layout_quality',{})
        f.write(f"| {name} | {item['state']} | {len(r.get('rooms',[]))} | {len(r.get('openings',[]))} | {len(r.get('damage',[]))} | {q.get('status','not available')} |\n")
    f.write('\nVideo rows with missing predictions indicate unresolved physical room correspondence, not zero-sized rooms. Candidate-room outputs remain available in each run. No dimension-based best-match assignment is used.\n')
    f.write('\n## CPU timing\n\nMeasured wall time includes the selected reconstruction and rendering stages. Some runs shared the laptop concurrently; cache reuse and changing source revisions are disclosed in provenance. These are not isolated hardware speed benchmarks.\n\n| Run | Seconds | Peak process RSS MB | Device |\n|---|---:|---:|---|\n')
    for t in timings:f.write(f"| {t['run']} | {t['seconds']:.1f} | {t['max_rss_mb']:.0f} | {t['device']} |\n")
    f.write('\n## Required gates and evidence\n\n| Gate | Evidence | Status |\n|---|---|---|\n| Wall repeatability | Independent kitchen repeat, sorted extent proxy in Part 2 | Long side fails; matched walls unavailable |\n| Repeated ceiling spread | Kitchen repeat | 3.10 cm; fails 1 cm |\n| Consumer app, two rooms, 70% beat/tie | Part 3 Magicplan PDF exports and comparison | 2/6 shared linear dimensions; fails 70% |\n| Calibrated intervals | No independent calibration/test properties | Not established |\n| Full opening detection and width | Missing unique reference opening IDs and exhaustive counts | Not scoreable completely |\n| Damage metric extents | No measured reference masks/prop dimensions | Not established |\n| Photo footprint + adjacency | Three-room photo output | Physical stitch fails |\n| Three rooms plus connector | New 8,023-frame scan | Raw composition met; automatic segmentation merged hall and kitchen |\n')
# Exact before/after same-room geometry comparison, with predictions retained.
fixscores=[]
for name in ['three_room_lidar','three_room_lidar_after','three_room_photos','three_room_photos_posefix','three_room_photos_final']:
    path=ROOT/'runs'/name/'result.json'
    if path.exists():
        result=json.loads(path.read_text());result['capture_id']=name;fixscores.append(score(result,truth,maps[name]))
export_scores(fixscores,ROOT/'fix_loop/evaluation')
# The authoritative post-mortem is the corrected Part 4 artifact. Preserve its
# actual predictions, regressions and historical-source caveat on regeneration.
(ROOT/'fix_loop/postmortem.md').write_text((ROOT/'submission/part_4/03_comparison/POSTMORTEM.md').read_text())
compliance=[
 ('Route 2 stock capture protocol','docs/CAPTURE_PROTOCOL.md','One-page operator instructions','Written; not independently followed by evaluator'),
 ('Device matrix','docs/DEVICE_MATRIX.md','Hardware/tier table','Written; actual tests limited to supplied device'),
 ('Photos, video, LiDAR input','astra/__main__.py; configs/benchmark.json','Common CLI and declared benchmark runs','Implemented; execution listed in benchmark'),
 ('Full Round 1 JSON','schemas/result.schema.json','Provisional contract and optional official validation','Blocked: official schema/instructions absent'),
 ('Room dimensions/plans','astra/layout.py; runs/*/result.json','Walls, area, height, room/whole-plan exports','Implemented; measured errors and unobserved fields remain'),
 ('Correct stitched property from every tier','astra/quality.py; runs/*/layout_quality','Overlap, connectivity and component diagnostics','Partial: RGB physical stitch can fail'),
 ('Openings ≤2 cm on ≥85%, with misses/phantoms','astra/openings.py; semantics/candidates.json','Ray-supported and visual candidates','Not passed; exhaustive opening truth unavailable'),
 ('Height ≤1.5 cm','reports/metrics.csv','Laser comparison','Failed on current measured rooms'),
 ('Repeatability and repeated height spread','submission/part_2/03_evaluation/kitchen_repeat/','Independent kitchen capture and laser comparison','Height spread 3.10 cm fails; long extent proxy fails; physical walls unmatched'),
 ('Drift correction and ablation','runs/drift_ablation/ablation.json; footprint_comparison.svg','Verified ICP graph and actual on/off footprint','Implemented and executed'),
 ('Photo ±8% / video ±3% wall accuracy','reports/benchmark.md','Extent proxy scores and unmapped failures','Not established; full per-wall correspondence absent'),
 ('Calibrated intervals at every tier','docs/ARCHITECTURE.md; result.json','Explicit provisional ranges and coverage rows','Incomplete: no independent empirical calibration'),
 ('Surface damage classes and metric extent','astra/semantics.py; runs/damage_*','Wall-projected candidates, staging demo','Partial: natural recognition and extent accuracy unvalidated; generalized nonwall association incomplete'),
 ('Concealed flags with rules','astra/semantics.py; result.json','Visible-evidence inspection flags','Implemented as inspection rules; no hidden-damage diagnosis'),
 ('Scope lines keyed to surfaces','astra/semantics.py; result.json','Inspection quantity and rule IDs','Implemented inspection scope; full Round 1 contract unknown'),
 ('Three rooms plus connector benchmark','three_room/; runs/three_room_expanded_assisted/','Bedroom, kitchen, hall, connector raw; automatic and assisted plans','Raw composition met; automatic hall/kitchen merge; assisted result marked'),
 ('Same spaces in all tiers','configs/benchmark.json; runs/three_room_expanded_*','Original and replacement photo/video/LiDAR outputs','Executed; replacement RGB physical stitching fails; video is Stray RGB export'),
 ('Two-room consumer app comparison','submission/part_3/04_comparison/REPORT.md','Magicplan 2026.38.0 kitchen and hall PDF exports; scored table','2/6 linear dimensions, 33.3%; below 70%'),
 ('Fix declaration, before/after, diff','fix_loop/','Measured declarations and reproduction','Shipped fixes; predictions and shortcomings reported'),
 ('Incremental process history','.history; submission/part_5/','Actual development commits and portable bundle','Recorded; bundle refreshed at final packaging'),
 ('Clean install under 15 minutes','scripts/setup.sh; README.md','Pinned environment and downloads','Not verified on clean machine; network-dependent'),
 ('Reproduction bundle','submission/part_2/05_reproduction/; submission/part_4/05_reproduction/','Raw captures, source and historic snapshots; public model fetch','Prepared; clean-machine and exact photo-after replay not verified'),
 ('Technical report ≤6 pages','reports/technical_report.pdf','Six-page PDF','Generated from actual available evidence'),
 ('Unseen live walk-in','README.md; docs/CAPTURE_PROTOCOL.md','Same live CLI','Not tested on evaluator capture')]
text=['# Compliance matrix','','Implementation and successful execution do not imply accuracy-gate compliance. Missing evidence is explicit.','','| Requirement | File path | Artifact | Status |','|---|---|---|---|']
text += ['| '+' | '.join(row)+' |' for row in compliance]
(ROOT/'docs/COMPLIANCE.md').write_text('\n'.join(text)+'\n')
# Six pages, no hidden seventh appendix. Full tables live separately.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
executed=sum(runs[item['id']]['state']=='executed' for item in config['runs'])
pages=[
 ('1. Scope, architecture and output',[
 f'Astra local property reconstruction — 3 October 2026. {executed}/{len(runs)} declared runs have completed at report generation. This is a measured development submission; no blanket gate-pass claim is made.',
 'Route 2 uses Stray Scanner 1.4 on iPhone 15 Pro Max. Laptop: Ubuntu 24, Intel i7-1265U, 64 GB RAM, no GPU. Photos/video are intended for iPhone 15 or newer; other physical devices have not been tested. Kaggle is optional and unvalidated.',
 'LiDAR: validate samples/units -> backproject confident depth -> verified local/loop correction graph -> structural room planes. RGB: select frames/photos -> focal/depth prior -> feature matching and PnP/essential geometry -> relative pose graph -> approximate gravity -> structural layout.',
 'All tiers: surface IDs -> opening/region candidates -> metric projection -> transparent inspection rules and scope -> provisional JSON, room/surface drawings and whole-property plan. Input and model hashes, source provenance, timing and dependency versions accompany each run.',
 'Ground truth is read only by evaluation. The official Round 1 schema is missing; the supplied schema is explicitly provisional. Filtered point fusion and GrabCut replace the planned TSDF and SAM components.'
 ]),
 ('2. Sensor handling, geometry and drift',[
 'Depth is millimetres; poses and output coordinates are metres. Per-frame intrinsics are resized to depth resolution. Stray camera-to-world xyzw poses use OpenCV camera coordinates, with world y up. The plan is x,z after a common yaw alignment.',
 'MP4 sample times preserve variable timing. Decoding disables edit-list trimming to retain recorded HEVC sensor frames. Pose/RGB timing residuals are exported. IMU acceleration norms are near 1, so raw translation is not integrated under a false m/s² assumption.',
 'Local and revisited cloud pairs create trimmed ICP factors only after overlap/residual/motion checks. A robust sparse small-angle correction graph anchors the first camera and penalizes implausible/non-smooth corrections. It is an approximation, not complete SLAM.',
 'The actual 140-frame ablation accepted 41 factors including five loop factors, with maximum translation correction about 8.89 cm. Summed inferred room area changed from 20.8086 to 20.8020 m². The footprint overlay also exposes shape changes. A small area delta does not prove accuracy improvement.',
 'Distance-watershed free-space basins seed structural-plane extraction. High wall observations reduce furniture confusion; local horizontal modes estimate height. Unobserved ceilings remain null. Low coverage, reflective/glass surfaces, cabinets, soffits and non-Manhattan walls can still bias boundaries.'
 ]),
 ('3. RGB models, semantics and scope',[
 'The initial RGB depth prior is Depth Anything V2 Metric Hypersim Small. It executes on CPU but has severe scale bias in the supplied stills. Depth Pro estimates focal length and depth jointly; its actual after-run results are reported separately when complete. No API key or paid inference is used.',
 'Full-precision Depth Pro took about 225.6 seconds including load in a concurrent CPU probe. Dynamic int8 took about 230.5 seconds and changed focal length from 236.6 to 462.2 px on the same input. That variant is excluded from the benchmark configuration; numerical equivalence is not assumed.',
 'Depth-assisted PnP handles some low-parallax feature pairs that defeat essential triangulation. Remaining disconnected components are explicitly schematic. Overlap and adjacency diagnostics must pass before a physical whole-property stitch can be accepted.',
 'Grounding DINO proposals and GrabCut masks are unverified visual evidence. LiDAR openings additionally require wall gaps plus transmitted depth rays and lintel support. Facing opening pairs support room adjacency; detected widths remain uncertain.',
 'Black/brown staging props are assessed only in explicit staged mode. They are not natural damage training examples. Metric wall regions are clipped and unioned; generalized floor/ceiling damage is incomplete. Flags recommend inspection using named rules. Scope items are inspection quantities, not diagnoses or priced repair orders.'
 ]),
 ('4. Benchmark, gates and uncertainty',[
 'The newer scan contains bedroom, kitchen, hall and connector; raw data meets the composition requirement. Automatic LiDAR merges hall and kitchen. The visually assisted four-space plan is labelled. Its photo result has four disconnected rooms and a 4.139 m² overlap; RGB-only video has 22 fragments. Both fail physical stitching.',
 'Laser truth contains room length/breadth/height and room-level doorway entries. Wall identities, exhaustive opening IDs, global outline and damage reference extents are absent. Sorted extents are therefore proxies, not full per-wall scores. Video physical correspondence can remain unresolved and is not chosen to minimize error.',
 'See benchmark.md and metrics.csv for every measured row, including missing predictions. The early LiDAR after run estimated hall height 2.7687 m, kitchen 2.7591 m and corridor 2.1928 m against 2.8, 2.8 and 2.26 m. All miss the 1.5 cm gate. Later results are tabulated separately.',
 'Every measurement includes a nominal 95% engineering interval, explicitly marked uncalibrated. Unknown values and intervals are null. Detector scores and sensor confidence are not calibrated geometric intervals. Nominal coverage on this small correlated set is descriptive only.',
 'The independent kitchen LiDAR repeat has height spread 3.10 cm and fails the 1 cm gate; the long horizontal extent proxy also fails. Magicplan 2026.38.0 exports exist for kitchen and hall; the pipeline wins/ties on 2/6 linear dimensions (33.3%), below 70%. Calibrated intervals still require a held-out set.'
 ]),
 ('5. Fix loop and engineering evidence',[
 'The first declaration targeted the worst measured LiDAR height error available at that time: kitchen error 4.65 cm. It hypothesized that global floor support and free-space partitioning contaminated room measurements. It predicted at most 2 cm kitchen/hall error after local structural-plane extraction.',
 'The shipped plane change substantially improves the kitchen/corridor boundaries and enables ray-supported adjacency. It misses the predicted height improvement; corridor height regresses. This supports the wall-partition diagnosis but leaves sensor/pose/surface-selection height bias unresolved. No laser scale fitting was used.',
 'The photo declaration identified corridor long extent error 232.9% but missed the actual worst short extent error of 448.15%. The fix changes focal/depth, pose and gravity. The actual worst after error is 176.54%; prediction below 100% and one connection both fail. The original declaration remains unchanged.',
 'Part 4 retains original declarations, before/after outputs, input hashes, original-code before reruns and a readable diff. Four historical photo-after source hashes are unrecoverable. A supplemental source-frozen photo after run completes in 101 s with cached depth and matching dimensions, but no adjacency. Supporting standalone kitchen height improves 1.62 to 0.79 cm with multiple settings changed.',
 'Development commits use .history because this coding session mounts .git read-only. A standard Git bundle exports the actual incremental history. Unit/integration checks cover projection units, rigid alignment, gravity, masks, doorway evidence, topology and reference validation. Accuracy still requires physical benchmark evidence.'
 ]),
 ('6. Reproduction, defense and remaining risks',[
 'README supplies one command per tier/capture. setup.sh installs pinned packages and fetch scripts download public models; inference then runs offline. A fresh-machine setup under 15 minutes has not been measured. Download bandwidth and Depth Pro CPU inference are substantial costs.',
 'The Part 2 and 4 bundles contain source, declarations, old and new raw scans, measurements, outputs, manifests and historical evidence. Public model weights are fetched by script; credentials and virtual environments are excluded. Old and replacement scans have separate names to preserve input identity.',
 'The stock capture page asks for slow overlapping views of floor/ceiling junctions, both sides of doorways and a return loop. The photos need parallax and shared doorway detail. Mirrors/glass, glossy or wet-looking finishes, motion blur and low light remain known failure modes, rather than solved claims.',
 'Remaining external evidence: official contract/schema, exhaustive physical wall/opening/damage correspondences, held-out interval calibration, and an unseen evaluator capture. The two-room app exports and an independent kitchen repeat are now present; their gates are not passed. Clean setup under 15 minutes remains unverified.',
 'The delivered output must be read with its warnings: LiDAR geometry is useful but centimetre gates fail; RGB scale/stitching may fail; staged masks do not validate natural damage; concealed flags are inspection prompts. docs/COMPLIANCE.md maps every requirement to its artifact and actual status.'
 ])]
md=['# Technical report (six-page PDF companion)','']
with PdfPages(out/'technical_report.pdf') as pdf:
    for title,paragraphs in pages:
        fig=plt.figure(figsize=(8.27,11.69));fig.text(.085,.945,title,fontsize=17,weight='bold',va='top');y=.89
        for para in paragraphs:
            wrapped=textwrap.fill(para,width=94);lines=wrapped.count('\n')+1
            fig.text(.085,y,wrapped,fontsize=10.5,va='top',linespacing=1.45);y-=lines*.019+.027
        fig.text(.085,.04,'Astra | Development benchmark | See separate raw tables and compliance matrix',fontsize=8,color='#555555');pdf.savefig(fig);plt.close(fig)
        md+=['## '+title,'',*sum(([p,''] for p in paragraphs),[])]
(out/'technical_report.md').write_text('\n'.join(md)+'\n')
print(out/'benchmark.md');print(out/'technical_report.pdf')
