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
    room_ids=[r['id'] for r in result['rooms']]
    if len(room_ids)!=len(set(room_ids)):raise ValueError('Duplicate room IDs')
    surface_map={s['id']:s for s in result['surfaces']}
    for surface in result['surfaces']:
        if surface['room_id'] not in room_ids:raise ValueError('Orphan surface room reference')
    for kind in ['openings','damage','scope_items','concealed_damage_flags']:
        item_ids=[x['id'] for x in result[kind]]
        if len(item_ids)!=len(set(item_ids)):raise ValueError(f'Duplicate {kind} IDs')
        for x in result[kind]:
            if 'room_id' in x and x['room_id']!=surface_map[x['surface_id']]['room_id']:raise ValueError('Room/surface association mismatch')
    opening_ids={x['id'] for x in result['openings']};damage_ids={x['id'] for x in result['damage']}
    for edge in result['adjacency']:
        if not set(edge['rooms'])<=set(room_ids) or not set(edge['opening_ids'])<=opening_ids:raise ValueError('Orphan adjacency reference')
    for surface in result['surfaces']:
        if not set(surface['damage_ids'])<=damage_ids:raise ValueError('Orphan surface damage reference')
    for kind in ['scope_items','concealed_damage_flags']:
        if any(x['damage_id'] not in damage_ids for x in result[kind]):raise ValueError('Orphan damage reference')
    def check(o):
        if isinstance(o,dict):
            if 'value' in o and 'interval' in o:
                v=o['value'];iv=o['interval']
                if v is not None and (iv['lower'] is None or iv['upper'] is None or not iv['lower']<=v<=iv['upper']):raise ValueError('Invalid measurement interval')
            for v in o.values():check(v)
        elif isinstance(o,list):
            for v in o:check(v)
    check(result)

# The local contract is deliberately explicit; an official schema can be supplied
# as a second validation layer, without pretending these two contracts are equal.
SCHEMA['$defs'].update({
 'point':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'number'}},
 'wall':{'type':'object','required':['surface_id','start','end','length'],
         'properties':{'surface_id':{'type':'string'},'start':{'$ref':'#/$defs/point'},'end':{'$ref':'#/$defs/point'},'length':{'$ref':'#/$defs/measurement'}}},
 'surface':{'type':'object','required':['id','room_id','kind','gross_area','visibility','damage_ids'],
            'properties':{'id':{'type':'string'},'room_id':{'type':'string'},'kind':{'enum':['wall','floor','ceiling']},'gross_area':{'$ref':'#/$defs/measurement'},'damage_ids':{'type':'array','items':{'type':'string'}}}},
 'opening':{'type':'object','required':['id','surface_id','room_id','kind','width','height','status','evidence','surface_uv_bounds'],
            'properties':{'id':{'type':'string'},'surface_id':{'type':'string'},'room_id':{'type':'string'},'kind':{'enum':['doorway','window']},'width':{'$ref':'#/$defs/measurement'},'height':{'$ref':'#/$defs/measurement'},'evidence':{'type':'array','items':{'type':'string'}}}},
 'damage':{'type':'object','required':['id','surface_id','room_id','class','area','extent_width','extent_height','surface_polygon','status','evidence'],
           'properties':{'area':{'$ref':'#/$defs/measurement'},'extent_width':{'$ref':'#/$defs/measurement'},'extent_height':{'$ref':'#/$defs/measurement'},'class':{'enum':['crack','water_logging/floods']},'surface_polygon':{'type':'array','minItems':3,'items':{'$ref':'#/$defs/point'}}}},
 'adjacency':{'type':'object','required':['rooms','opening_ids','status'],'properties':{'rooms':{'type':'array','minItems':2,'maxItems':2,'uniqueItems':True,'items':{'type':'string'}},'opening_ids':{'type':'array','minItems':2,'items':{'type':'string'}}}},
 'scope':{'type':'object','required':['id','surface_id','damage_id','action','quantity','rule','provisional'],'properties':{'quantity':{'$ref':'#/$defs/measurement'}}},
 'flag':{'type':'object','required':['id','surface_id','damage_id','rule','rule_inputs','message','status','evidence']}
})
for name,definition in [('surfaces','surface'),('openings','opening'),('damage','damage'),('adjacency','adjacency'),('scope_items','scope'),('concealed_damage_flags','flag')]:
    SCHEMA['properties'][name]={'type':'array','items':{'$ref':f'#/$defs/{definition}'}}
SCHEMA['properties']['rooms']['items']['properties']['walls']={'type':'array','minItems':3,'items':{'$ref':'#/$defs/wall'}}
