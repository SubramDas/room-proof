"""Reference scoring is separate from inference, with omissions explicitly counted."""
from pathlib import Path
import json,csv,re
import numpy as np
from .io import write_json


def read_measurements(path):
    rooms={};current=None
    # Preserve stable benchmark IDs when the operator makes room names readable.
    known={'kitchen':'room_1','hall':'room_2','connector':'room_3','bedroom':'bedroom'}
    for line in Path(path).read_text().splitlines():
        line=line.strip()
        if not line:continue
        if line.endswith(':'):
            name=line[:-1];match=re.search(r'room_\d+',name);current=match.group(0) if match else known.get(name.lower(),name)
            if current in rooms:raise ValueError(f'Duplicate ground-truth room: {current}')
            rooms[current]={}
        elif ':' in line and current:
            key,value=line.split(':',1);m=re.match(r'\s*([\d.]+)\s*m\s*$',value)
            if m:rooms[current][key.strip()]=float(m.group(1))
    return {'source':str(path),'instrument':'laser_user_reported','instrument_uncertainty_m':None,'rooms':rooms,
            'reference_scope':'partial_room_dimensions_and_room_level_doorway_entries','adjacency':[['room_1','room_2'],['room_2','room_3'],['room_3','bedroom']]}


def score(result,truth,mapping):
    records=[];roomindex={r['id']:r for r in result['rooms']};tier=result['tier']
    for ref_id,pred_id in mapping.items():
        ref=truth['rooms'][ref_id];room=roomindex.get(pred_id)
        # Extent comparison is orientation-independent because the supplied text
        # does not associate length/breadth with physical wall IDs.
        expected=sorted([ref['length'],ref['breadth']]);actual=sorted([room['extent_x'],room['extent_z']],key=lambda m:m['value']) if room else [None,None]
        pairs=[('short_extent',expected[0],actual[0]),('long_extent',expected[1],actual[1]),('ceiling_height',ref['height'],room['ceiling_height'] if room else None)]
        for kind,target,m in pairs:
            value=m['value'] if m else None;error=abs(value-target) if value is not None else None
            limit=.015 if kind=='ceiling_height' else (.08*target if tier=='photos' else .03*target if tier=='video' else None)
            coverage=None if m is None or value is None else m['interval']['lower']<=target<=m['interval']['upper']
            records.append({'reference_room':ref_id,'predicted_room':pred_id,'quantity':kind,'truth_m':target,'prediction_m':value,'absolute_error_m':error,
                'signed_error_m':value-target if value is not None else None,'relative_error':error/target if error is not None else None,
                'nominal_interval_coverage':coverage,'gate_limit_m':limit,'pass':(error<=limit if error is not None else False) if limit is not None else None,
                'comparison_type':'axis_extent_proxy_not_per_wall' if 'extent' in kind else 'height'})
    return {'tier':tier,'capture_id':result['capture_id'],'records':records,'warnings':[
        'Extent proxies are not the full per-wall benchmark; missing official Round 1 gates.',
        'Ground-truth instrument uncertainty is unspecified.',
        'Opening rows lack independent opening IDs/offsets; no complete opening detection score can be claimed.',
        'Calibration dataset is too small/correlated for validated 95% coverage.'],
        'unscored':['opening_detection_and_width_gate','damage_extent_accuracy','concealed_damage_accuracy','scope_accuracy','full_footprint','adjacency_without_explicit_room_mapping']}


def export_scores(scores,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);write_json(out/'metrics.json',scores)
    records=[{'capture_id':s['capture_id'],'tier':s['tier'],**r} for s in scores for r in s['records']]
    if records:
        with (out/'metrics.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=records[0].keys());writer.writeheader();writer.writerows(records)
    lines=['# Measured benchmark results','','These results compare predictions with supplied laser dimensions. Extent comparisons are proxies, not full per-wall scores.','','| Capture / tier | Reference | Quantity | Truth m | Predicted m | Error cm | Gate |','|---|---|---|---:|---:|---:|---|']
    for r in records:
        pred='missing' if r['prediction_m'] is None else f"{r['prediction_m']:.3f}";err='missing' if r['absolute_error_m'] is None else f"{r['absolute_error_m']*100:.2f}";gate='not specified' if r['pass'] is None else ('pass' if r['pass'] else 'FAIL')
        lines.append(f"| {r['capture_id']} / {r['tier']} | {r['reference_room']} | {r['quantity']} | {r['truth_m']:.3f} | {pred} | {err} | {gate} |")
    lines+=['','## Incomplete benchmark evidence','','An independent kitchen repeat and two Magicplan room exports are supplied separately. Full wall correspondence, independent damage extents, official schema/round-one gates and independent interval calibration remain unavailable. The expanded capture has three rooms plus a connector; its automatic segmentation merges hall and kitchen, and the assisted correction is labelled separately. These gaps are not counted as passed gates.']
    (out/'benchmark.md').write_text('\n'.join(lines)+'\n')


def repeatability(first,second):
    b={r['id']:r for r in second['rooms']};items=[]
    for r in first['rooms']:
        if r['id'] not in b:items.append({'room':r['id'],'status':'missing_in_second'});continue
        other=b[r['id']]
        for key in ['extent_x','extent_z','ceiling_height']:
            a=r[key]['value'];v=other[key]['value']
            delta=abs(a-v) if a is not None and v is not None else None
            limit=.01 if key=='ceiling_height' else max(.01,.005*max(a or 0,v or 0))
            items.append({'room':r['id'],'measurement':key,'absolute_delta_m':delta,'limit_m':limit,'pass':delta is not None and delta<=limit})
    return {'tier_match':first['tier']==second['tier'],'records':items,'warning':'Extent proxies only; verify independent capture identities and wall correspondence.'}
