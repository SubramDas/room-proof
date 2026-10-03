from pathlib import Path
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
