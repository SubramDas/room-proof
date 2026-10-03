"""Package the two-room magicplan comparison with explicit proxy limitations."""
from pathlib import Path
import shutil,json,csv,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'submission/part_3';OUT.mkdir(parents=True,exist_ok=True)
def write(path,text):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.rstrip()+'\n')
appdir=OUT/'01_magicplan';appdir.mkdir(exist_ok=True)
for room in ['Kitchen','Hall']:
 name=f'MagicPlan_{room}.pdf';shutil.copy2(ROOT/name,appdir/name)
 subprocess.run(['pdftotext','-layout',str(appdir/name),str(appdir/(room.lower()+'_extracted_text.txt'))],check=True)
# Preserve the earlier generic text filename as the kitchen transcription.
shutil.copy2(appdir/'kitchen_extracted_text.txt',appdir/'extracted_text.txt')
ref=OUT/'03_reference';ref.mkdir(exist_ok=True);shutil.copy2(ROOT/'measurements.txt',ref/'measurements.txt')
specs=[('kitchen','kitchen_lidar_final','room_1',(2.3,2.36,2.8),(2.37,2.40,2.79,5.69,9.54)),('hall','three_room_lidar_final','room_1',(3.3,4.2,2.8),(3.30,4.24,2.83,13.99,15.08))]
rows=[]
for room,run,rid,truth,app in specs:
 source=ROOT/'runs'/run;target=OUT/'02_pipeline'/run;shutil.copytree(source,target,dirs_exist_ok=True)
 d=json.loads((source/'result.json').read_text());r=next(r for r in d['rooms'] if r['id']==rid);ext=sorted([r['extent_x']['value'],r['extent_z']['value']])
 items=[('short_extent','m',truth[0],ext[0],app[0],'linear_extent_proxy'),('long_extent','m',truth[1],ext[1],app[1],'linear_extent_proxy'),('ceiling_height','m',truth[2],r['ceiling_height']['value'],app[2],'linear'),('floor_area','m2',truth[0]*truth[1],r['floor_area']['value'],app[3],'derived_reference'),('perimeter','m',2*(truth[0]+truth[1]),sum(w['length']['value'] for w in r['walls']),app[4],'derived_reference')]
 for name,unit,reference,pred,estimate,kind in items:
  pe=abs(pred-reference);ae=abs(estimate-reference)
  rows.append({'room':room,'measurement':name,'unit':unit,'reference':reference,'pipeline':pred,'magicplan':estimate,'pipeline_absolute_error':pe,'magicplan_absolute_error':ae,'beat_or_tie':pe<=ae+1e-9,'comparison_type':kind,'pipeline_run':run,'pipeline_room_id':rid,'app_source':f'MagicPlan_{room.title()}.pdf page 3'})
folder=OUT/'04_comparison';folder.mkdir(exist_ok=True)
with (folder/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def score(group):
 n=sum(r['beat_or_tie'] for r in group);return {'wins':n,'count':len(group),'fraction':n/len(group)}
linear=[r for r in rows if r['comparison_type']!='derived_reference'];primary=score(linear);allscore=score(rows)
summary={'app':'magicplan','app_version':'2026.38.0','measurement_method':'automatically measured; operator reported','rooms_required':2,'rooms_with_exports':2,'pipeline_selection':{'kitchen':'original declared standalone kitchen_lidar_final','hall':'three_room_lidar_final room_1, corresponding to laser room_2'},'linear_proxy_beat_or_tie':primary,'including_derived_quantities':allscore,'required_fraction':.7,'provisional_linear_gate_pass':primary['fraction']>=.7,'part3_status':'two_room_exports_available; reported proxy score below target; exhaustive wall/opening correspondence incomplete','official_gate_pass':None,'rows':rows}
write('04_comparison/score.json',json.dumps(summary,indent=2))
lines=['# Kitchen and hall: pipeline vs magicplan','','magicplan 2026.38.0; automatically measured dimensions per operator. Original exports preserved. Kitchen uses kitchen_lidar_final; hall uses room_1 of three_room_lidar_final (laser reference room_2). This retains the original kitchen comparison and does not substitute the repeat scan after seeing app performance.','','| Room | Measurement | Unit | Laser reference | Pipeline | Magicplan | Pipeline error | Magicplan error | Beat/tie? |','|---|---|---|---:|---:|---:|---:|---:|---|']
for x in rows:lines.append(f"| {x['room']} | {x['measurement']} | {x['unit']} | {x['reference']:.4f} | {x['pipeline']:.4f} | {x['magicplan']:.4f} | {x['pipeline_absolute_error']:.4f} | {x['magicplan_absolute_error']:.4f} | {'Yes' if x['beat_or_tie'] else 'No'} |")
lines+=['','**Linear room measurements: 2/6 = 33.3% beat/tie. Including area and perimeter: 4/10 = 40.0%.** Both are below 70%. Both required room exports are now supplied; this remains a provisional extent/height comparison, not a complete matched-wall/opening score.','','## Scoring and correspondence','','- Absolute error is |estimate − laser reference|. Beat/tie uses pipeline error ≤ app error with 1e-9 numerical tolerance only.','- Horizontal dimensions are sorted short/long because physical wall IDs are absent in the laser notes. This is an extent proxy, not proof of physical wall correspondence.','- Height is compared directly. Area and perimeter references assume rectangular rooms and are derived from the supplied laser extents; they are reported separately to avoid padding the primary linear denominator.','- App values are rounded to 0.01 m / 0.01 m²; hidden precision and laser instrument uncertainty are unknown. In particular the height win/loss differences are smaller than app display resolution. Scores are point-estimate comparisons at exported precision, not statistical significance claims.','- In the three-room pipeline output room_1 is hall, room_2 is kitchen, room_3 is corridor. This physical mapping was recorded before app comparison.','- No app measurements or laser dimensions are used to calibrate pipeline inference.','','## Hall export discrepancy','','The cover and property header show 13.98 m², while the Hall room label and page-3 room summary show 13.99 m². Use **13.99 m²** for the per-room comparison and retain the discrepancy. Using 13.98 m² also gives a hall area win for our pipeline, so the aggregate count is unchanged. Do not silently replace either value.','','## Remaining unscored dimensions','','| Quantity | App evidence | Required correspondence/evidence |','|---|---|---|','| Kitchen opening width | 0.87 m left-wall opening | Match a specific pipeline candidate to the physical laser doorway (0.88 m). |','| Hall openings | Plan labels include 0.85 m, 0.84 m and 0.95 m openings | Identify each physical opening, its connected room and laser width; one room-level 0.88 m entry is insufficient. |','| Doorway heights | Not in either PDF | App detail export and matched pipeline opening. |','| Wall segments / window spans | Kitchen 1.53/1.64/0.69 m and hall 1.63/0.70/1.37/2.04 m labels | Separate full walls from openings/segments and supply matching reference measurements. |','','All candidates remain in the submitted pipeline JSON. No closest-dimension matching is used to pick a favourable opening. The 70% full comparison target is not claimed passed.']
write('04_comparison/REPORT.md','\n'.join(lines))
write('01_magicplan/METADATA.md','# Consumer app exports\n\nApp: magicplan. Version: 2026.38.0 (operator confirmed). Dimensions: automatically measured (operator confirmed). Capture hardware/mode is not independently recorded in these PDFs. PDF producer Skia/PDF m103 is not the app version. Both exports print 3 October 2026 and each contains one room across three pages.\n\nKitchen page 3: 2.37 × 2.40 m; height 2.79 m; area 5.69 m²; perimeter 9.54 m.\n\nHall page 3: 3.30 × 4.24 m; height 2.83 m; room area 13.99 m²; perimeter 15.08 m. Hall property summary shows 13.98 m²; both values are retained in the originals and discrepancy is documented in the report.')
write('README.md','''# Part 3 — Two-room comparison against magicplan

Both required consumer-app room exports are now included: kitchen and hall. App version is 2026.38.0; operator reports automatically measured dimensions.

## Contents

- `01_magicplan/`: original PDFs, extracted text and metadata.
- `02_pipeline/`: original kitchen LiDAR output and three-room LiDAR output containing the hall, with JSON, plans, diagnostics and provenance.
- `03_reference/`: supplied laser measurements.
- `04_comparison/REPORT.md`, `comparison.csv`, `score.json`, `comparison.pdf`: combined dimension-by-dimension comparison, scoring and limitations.
- `05_reproduce_comparison.py`: verifies source-derived values and recomputes errors/counts.

**Result:** 2/6 shared linear measurements beat/tie (33.3%). Including derived area/perimeter, 4/10 (40%). Neither reaches 70%. The kitchen height and hall longer extent are the two linear wins. Physical wall/opening correspondences remain incomplete, so these are provisional extent/height scores rather than the exhaustive gate.

The hall room area is 13.99 m² in its room summary, but the property summary says 13.98 m². The per-room comparison uses 13.99 m² and discloses this discrepancy.

## Remaining work

Match physical wall/opening IDs across app, pipeline and laser; obtain missing opening widths/heights and segment references where necessary. Optional capture-mode/device details can complete the provenance record. Both PDFs and the app version are already available. Improving the score requires genuine pipeline accuracy improvements; no favourable run substitution is performed.

Raw inputs and pipeline rerun commands are in Part 2. Run `python3 05_reproduce_comparison.py` in this folder to verify the submitted comparison arithmetic.
''')
write('05_reproduce_comparison.py','''from pathlib import Path
import csv,json
root=Path(__file__).resolve().parent
rows=list(csv.DictReader((root/'04_comparison/comparison.csv').open()))
for r in rows:
    d=json.loads((root/'02_pipeline'/r['pipeline_run']/'result.json').read_text())
    room=next(x for x in d['rooms'] if x['id']==r['pipeline_room_id'])
    ext=sorted([room['extent_x']['value'],room['extent_z']['value']])
    actual={'short_extent':ext[0],'long_extent':ext[1],'ceiling_height':room['ceiling_height']['value'],'floor_area':room['floor_area']['value'],'perimeter':sum(w['length']['value'] for w in room['walls'])}[r['measurement']]
    assert abs(actual-float(r['pipeline']))<1e-9
    pe=abs(actual-float(r['reference']));ae=abs(float(r['magicplan'])-float(r['reference']))
    assert abs(pe-float(r['pipeline_absolute_error']))<1e-9
    assert abs(ae-float(r['magicplan_absolute_error']))<1e-9
    assert (pe<=ae+1e-9)==(r['beat_or_tie']=='True')
linear=[r for r in rows if r['comparison_type']!='derived_reference']
for label,group in [('linear proxies',linear),('including derived quantities',rows)]:
    wins=sum(r['beat_or_tie']=='True' for r in group)
    print(label,wins,'/',len(group),'=',round(100*wins/len(group),2),'%')
assert len(set(r['room'] for r in rows))==2
print('Two rooms included; proxy scores below 70%; exhaustive wall/opening correspondence incomplete.')
''')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig=plt.figure(figsize=(11.6929,8.2677));fig.text(.045,.94,'Part 3 | Kitchen and hall vs magicplan',fontsize=18,weight='bold')
fig.text(.045,.89,'magicplan 2026.38.0 | Automatically measured | Both room exports included',fontsize=11)
ax=fig.add_axes([.045,.34,.91,.50]);ax.axis('off')
labels=['Room / measurement','Unit','Reference','Pipeline','Magicplan','Our error','App error','Beat/tie']
data=[[r['room']+' / '+r['measurement'],r['unit'],*[f"{r[k]:.4f}" for k in ['reference','pipeline','magicplan','pipeline_absolute_error','magicplan_absolute_error']], 'Yes' if r['beat_or_tie'] else 'No'] for r in rows]
t=ax.table(cellText=data,colLabels=labels,loc='center',cellLoc='center',colWidths=[.25,.05,.115,.115,.115,.115,.115,.085]);t.auto_set_font_size(False);t.set_fontsize(9);t.scale(1,1.75)
fig.text(.045,.28,'Linear measurements: 2/6 (33.3%). Including area/perimeter: 4/10 (40%). Target: 70%.',fontsize=12,weight='bold')
fig.text(.045,.22,'Horizontal extents are proxies, not matched walls. Area/perimeter references assume rectangular rooms.\nApp display rounding limits interpretation of small error differences. Opening correspondence remains incomplete.\nHall room area is 13.99 m²; the property summary says 13.98 m². Per-room value used; outcome unchanged.\nSources: both MagicPlan PDFs page 3, packaged LiDAR JSON and laser reference. See REPORT.md for details.',fontsize=10,linespacing=1.7,va='top')
fig.savefig(folder/'comparison.pdf');plt.close(fig)
print('Part 3 updated:',primary,allscore)
