"""Provisional public contract; official evaluator schema was not supplied."""
from pathlib import Path
import json
import jsonschema

SCHEMA={
 '$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://astra.local/schema/result-v1',
 'type':'object','required':['schema_version','capture_id','tier','status','rooms','surfaces','openings','adjacency','damage','concealed_damage_flags','scope_items','warnings'],
 'properties':{
  'schema_version':{'const':'astra.provisional.v1'},'capture_id':{'type':'string'},'tier':{'enum':['lidar','video','photos']},'status':{'type':'string'},
  'rooms':{'type':'array','items':{'type':'object','required':['id','polygon','walls','ceiling_height','floor_area'],'properties':{'id':{'type':'string'},'polygon':{'type':'array','minItems':3,'items':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'number'}}},'ceiling_height':{'$ref':'#/$defs/measurement'},'floor_area':{'$ref':'#/$defs/measurement'}}}},
  'surfaces':{'type':'array'},'openings':{'type':'array'},'adjacency':{'type':'array'},'damage':{'type':'array'},'concealed_damage_flags':{'type':'array'},'scope_items':{'type':'array'},'warnings':{'type':'array','items':{'type':'string'}}},
 '$defs':{'measurement':{'type':'object','required':['value','unit','interval','status','method'],'properties':{'value':{'type':['number','null']},'unit':{'enum':['m','m2','count']},'interval':{'type':'object','required':['level','lower','upper','calibration_status'],'properties':{'level':{'type':'number','exclusiveMinimum':0,'exclusiveMaximum':1},'lower':{'type':['number','null']},'upper':{'type':['number','null']},'calibration_status':{'type':'string'}}}}}}
}


def validate(result,official=None):
    jsonschema.validate(result,SCHEMA)
    if official:jsonschema.validate(result,json.loads(Path(official).read_text()))
    ids=[s['id'] for s in result['surfaces']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate surface IDs')
    for kind in ['openings','damage','scope_items','concealed_damage_flags']:
        for item in result[kind]:
            if item['surface_id'] not in ids:raise ValueError(f'Orphan {kind} surface reference')
    def check(o):
        if isinstance(o,dict):
            if 'value' in o and 'interval' in o:
                v=o['value'];iv=o['interval']
                if v is not None and (iv['lower'] is None or iv['upper'] is None or not iv['lower']<=v<=iv['upper']):raise ValueError('Invalid measurement interval')
            for v in o.values():check(v)
        elif isinstance(o,list):
            for v in o:check(v)
    check(result)
