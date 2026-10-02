"""Conservative common contract, validation, and SVG rendering."""

import html
import json
import math
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / 'schema/property_plan.schema.json'


def unknown(unit, refs=()):
    return {'value': None, 'unit': unit, 'interval': {'lower': None, 'upper': None, 'coverage': 0.9, 'method': 'unbounded; no calibrated estimate'}, 'status': 'unresolved', 'source_refs': list(refs)}


def _provisional(value, unit, refs):
    return {'value': round(value, 4), 'unit': unit,
            'interval': {'lower': None, 'upper': None, 'coverage': .9,
                         'method': 'unbounded; provisional LiDAR fit without held-out calibration'},
            'status': 'inferred', 'source_refs': list(refs)}


def _apply_lidar_room_fit(plan, index, fit):
    if fit['status'] != 'inferred':
        return
    room = plan['rooms'][0]
    frames = {frame['frame_id']: frame for frame in index['frames']}
    def refs(frame_ids):
        return sorted({ref for frame_id in frame_ids
                       for ref in (frames[frame_id]['depth']['source_ref'], frames[frame_id]['pose_source_ref'])})
    boundary = fit['boundary_xz_m']
    height = fit['ceiling_height_m']
    floor_refs = refs(fit['floor']['frame_ids'])
    ceiling_refs = refs(fit['ceiling']['frame_ids'])
    wall_evidence = [fit['walls'][1][0], fit['walls'][0][1],
                     fit['walls'][1][1], fit['walls'][0][0]]
    slug = room['id'].removeprefix('room-')
    surfaces = []
    for number, evidence in enumerate(wall_evidence):
        line = [boundary[number], boundary[(number+1) % 4]]
        length = math.dist(*line)
        wall_refs = refs(evidence['frame_ids'])
        surfaces.append({'id': f'surf-{slug}-wall-{number+1}', 'kind': 'wall',
                         'status': 'inferred', 'line': line,
                         'length': _provisional(length, 'm', wall_refs),
                         'area': _provisional(length*height, 'm2', wall_refs),
                         'source_refs': wall_refs})
    area = fit['area_m2']
    surfaces.extend([
        {'id': f'surf-{slug}-floor-1', 'kind': 'floor', 'status': 'inferred',
         'area': _provisional(area, 'm2', floor_refs), 'source_refs': floor_refs},
        {'id': f'surf-{slug}-ceiling-1', 'kind': 'ceiling', 'status': 'inferred',
         'area': _provisional(area, 'm2', ceiling_refs), 'source_refs': ceiling_refs}])
    openings = []
    for number, candidate in enumerate(fit.get('opening_gap_candidates', []), 1):
        gap_refs = refs(candidate['frame_ids'])
        openings.append({'id': f'opening-{slug}-candidate-{number}', 'kind': 'door',
                         'surface_id': surfaces[candidate['wall_index']]['id'],
                         'status': 'unresolved',
                         'width': _provisional(candidate['width_m'], 'm', gap_refs),
                         'height': unknown('m', gap_refs),
                         'offset_along_wall': _provisional(candidate['offset_along_wall_m'], 'm', gap_refs),
                         'source_refs': gap_refs})
    room.update({'status': 'inferred', 'boundary': boundary,
                 'floor_area': _provisional(area, 'm2', floor_refs),
                 'ceiling_height': _provisional(height, 'm', floor_refs+ceiling_refs),
                 'surfaces': surfaces, 'openings': openings,
                 'source_refs': sorted(set(room['source_refs']+floor_refs+ceiling_refs))})
    plan['plan'].update({'status': 'inferred', 'footprint': boundary,
                         'floor_area': _provisional(area, 'm2', floor_refs)})


def build_plan(args, run_id, index, warnings, geometry=None, candidates=None):
    refs = [frame['source_ref'] for frame in index['frames'] if 'source_ref' in frame]
    if args.tier == 'lidar':
        refs = [index['rgb_source_ref'], index['odometry_source_ref'], index['camera_matrix_source_ref']]
    room_ids = index['room_ids'] if args.tier == 'photo' else [args.room_id or 'room-unresolved-1']
    rooms = []
    for room_id in room_ids:
        room_refs = [frame['source_ref'] for frame in index['frames'] if frame.get('room_id') == room_id] if args.tier == 'photo' else refs
        slug = room_id.removeprefix('room-')
        rooms.append({'id': room_id, 'name': slug.replace('-', ' ').title(), 'floor_id': None, 'kind': args.room_kind if args.tier != 'photo' else 'room', 'status': 'unresolved', 'boundary': None, 'floor_area': unknown('m2', room_refs), 'ceiling_height': unknown('m', room_refs), 'surfaces': [
            {'id': f'surf-{slug}-wall-1', 'kind': 'wall', 'status': 'unresolved', 'line': [[0, 0], [0, 0]], 'length': unknown('m', room_refs), 'area': unknown('m2', room_refs), 'source_refs': room_refs},
            {'id': f'surf-{slug}-floor-1', 'kind': 'floor', 'status': 'unresolved', 'area': unknown('m2', room_refs), 'source_refs': room_refs},
            {'id': f'surf-{slug}-ceiling-1', 'kind': 'ceiling', 'status': 'unresolved', 'area': unknown('m2', room_refs), 'source_refs': room_refs}], 'openings': [], 'source_refs': room_refs})
    ambiguities = ([{'room_ids': room_ids,
                     'reason': 'No verified doorway correspondence or geometric placement; multiple layouts remain possible.',
                     'source_refs': refs}] if args.tier == 'photo' and len(room_ids) > 1 else [])
    plan = {'schema_version': '0.1.0', 'property_id': args.property_id, 'run_id': run_id, 'capture': {'capture_id': args.capture_id, 'tier': args.tier, 'device_model': args.device_model, 'ios_version': args.ios_version, 'capture_app': args.capture_app, 'capture_app_version': args.capture_app_version, 'source_refs': refs}, 'coordinate_system': {'unit': 'm', 'origin': 'capture_local', 'x_axis': 'right_on_plan', 'y_axis': 'up_on_plan'}, 'plan': {'status': 'unresolved', 'footprint': None, 'floor_area': unknown('m2', refs), 'rendered_plan_path': 'property_plan.svg'}, 'rooms': rooms, 'adjacency': [], 'placement_ambiguities': ambiguities, 'damage_regions': [], 'concealed_damage_flags': [], 'scope_items': [], 'warnings': list(warnings)}
    if args.tier == 'lidar' and geometry is not None:
        _apply_lidar_room_fit(plan, index, geometry['room_fit'])
    if candidates is not None and candidates['status'] == 'proposals_only':
        counts = {kind: sum(item['class'] == kind for item in candidates['candidates'])
                  for kind in ('wall', 'floor', 'ceiling', 'door', 'window')}
        plan['warnings'].append(
            'Visual model proposals: ' + ', '.join(f'{count} {kind}' for kind, count in counts.items())
            + '; see visual_candidates.json. Openings and room connections are unverified.')
    if plan['plan']['status'] == 'unresolved':
        plan['warnings'].append('Geometry, openings, damage, and room placement have not been inferred. Capture coverage does not establish absence of damage.')
    else:
        plan['warnings'].append('Provisional LiDAR room layout; dimensions are not calibrated. Opening candidates are unverified; damage remains unresolved.')
    return plan


def _schema_errors(value, schema, definitions, location='$'):
    if '$ref' in schema:
        return _schema_errors(value, definitions[schema['$ref'].split('/')[-1]], definitions, location)
    if 'anyOf' in schema:
        if not any(not _schema_errors(value, item, definitions, location) for item in schema['anyOf']):
            return [f'{location}: matches no allowed schema']
        return []
    errors = []
    if 'const' in schema and value != schema['const']:
        errors.append(f'{location}: expected {schema["const"]!r}')
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{location}: value outside enum')
    types = schema.get('type')
    if types:
        types = types if isinstance(types, list) else [types]
        checks = {'object': lambda x: isinstance(x, dict), 'array': lambda x: isinstance(x, list), 'string': lambda x: isinstance(x, str), 'number': lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x), 'null': lambda x: x is None}
        if not any(checks[k](value) for k in types):
            return errors + [f'{location}: expected {types}']
    if isinstance(value, dict):
        if 'const' in schema.get('properties', {}).get('kind', {}) and 'kind' not in value:
            errors.append(f'{location}: missing kind')
        for key in schema.get('required', []):
            if key not in value:
                errors.append(f'{location}: missing {key}')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            errors.extend(f'{location}: unexpected {key}' for key in value if key not in props)
        for key, child in props.items():
            if key in value:
                errors.extend(_schema_errors(value[key], child, definitions, f'{location}.{key}'))
        for clause in schema.get('allOf', []):
            condition = clause.get('if', {}).get('properties', {})
            if condition and all(value.get(key) == spec.get('const') for key, spec in condition.items()):
                errors.extend(_schema_errors(value, clause['then'], definitions, location))
            elif 'properties' in clause:
                errors.extend(_schema_errors(value, clause, definitions, location))
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            errors.append(f'{location}: too few items')
        prefix = schema.get('prefixItems', [])
        if schema.get('items') is False and len(value) != len(prefix):
            errors.append(f'{location}: expected {len(prefix)} items')
        for i, item in enumerate(value):
            child = prefix[i] if i < len(prefix) else schema.get('items')
            if isinstance(child, dict):
                errors.extend(_schema_errors(item, child, definitions, f'{location}[{i}]'))
        if 'contains' in schema and not any(not _schema_errors(item, schema['contains'], definitions) for item in value):
            errors.append(f'{location}: missing required item kind')
    if isinstance(value, str) and len(value) < schema.get('minLength', 0):
        errors.append(f'{location}: string too short')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        for key, op in [('minimum', lambda a, b: a < b), ('maximum', lambda a, b: a > b), ('exclusiveMinimum', lambda a, b: a <= b), ('exclusiveMaximum', lambda a, b: a >= b)]:
            if key in schema and op(value, schema[key]):
                errors.append(f'{location}: violates {key}')
    return errors


def validate(plan):
    schema = json.loads(SCHEMA.read_text())
    errors = _schema_errors(plan, schema, schema['$defs'])
    ids = set()
    for collection in ('rooms', 'damage_regions', 'concealed_damage_flags', 'scope_items'):
        for item in plan.get(collection, []):
            if item['id'] in ids:
                errors.append(f'duplicate ID: {item["id"]}')
            ids.add(item['id'])
    room_ids = {room['id'] for room in plan.get('rooms', [])}
    surfaces = {}
    openings = set()
    for room in plan.get('rooms', []):
        for surface in room.get('surfaces', []):
            if surface['id'] in ids:
                errors.append(f'duplicate ID: {surface["id"]}')
            ids.add(surface['id']); surfaces[surface['id']] = room['id']
        for opening in room.get('openings', []):
            if opening['id'] in ids:
                errors.append(f'duplicate ID: {opening["id"]}')
            ids.add(opening['id']); openings.add(opening['id'])
            if surfaces.get(opening['surface_id']) != room['id']:
                errors.append(f'opening {opening["id"]}: invalid surface reference')
    for edge in plan.get('adjacency', []):
        if edge['room_a_id'] not in room_ids or edge['room_b_id'] not in room_ids or edge['room_a_id'] == edge['room_b_id']:
            errors.append('adjacency: invalid room reference')
        if edge['opening_id'] is not None and edge['opening_id'] not in openings:
            errors.append('adjacency: invalid opening reference')
    for ambiguity in plan.get('placement_ambiguities', []):
        if len(set(ambiguity['room_ids'])) != len(ambiguity['room_ids']) or any(room_id not in room_ids for room_id in ambiguity['room_ids']):
            errors.append('placement ambiguity: invalid or repeated room reference')
    damage_ids = set()
    for item in plan.get('damage_regions', []):
        damage_ids.add(item['id'])
    for collection in ('damage_regions', 'concealed_damage_flags', 'scope_items'):
        for item in plan.get(collection, []):
            if item['room_id'] not in room_ids or surfaces.get(item['surface_id']) != item['room_id']:
                errors.append(f'{item["id"]}: invalid room/surface reference')
            if collection == 'scope_items' and item['damage_region_id'] is not None and item['damage_region_id'] not in damage_ids:
                errors.append(f'{item["id"]}: invalid damage reference')
    def walk(value, path):
        if isinstance(value, dict):
            if {'value', 'unit', 'interval', 'status', 'source_refs'} <= value.keys():
                point = value['value']; lo = value['interval']['lower']; hi = value['interval']['upper']
                if any(v is not None and v < 0 for v in (point, lo, hi)):
                    errors.append(f'{path}: negative physical measurement')
                if lo is not None and hi is not None and lo > hi:
                    errors.append(f'{path}: inverted interval')
                if point is not None and ((lo is not None and point < lo) or (hi is not None and point > hi)):
                    errors.append(f'{path}: point outside interval')
            for key, child in value.items(): walk(child, f'{path}.{key}')
        elif isinstance(value, list):
            for i, child in enumerate(value): walk(child, f'{path}[{i}]')
    walk(plan, '$')
    def area(poly):
        return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))/2)
    for room in plan.get('rooms', []):
        poly = room['boundary']
        if poly is not None and area(poly) <= 0:
            errors.append(f'{room["id"]}: degenerate boundary')
        if poly is not None and room['floor_area']['value'] is not None and abs(area(poly)-room['floor_area']['value']) > max(.05, area(poly)*.05):
            errors.append(f'{room["id"]}: area disagrees with boundary')
    polygons = [(room['id'], room['boundary']) for room in plan.get('rooms', []) if room['boundary'] is not None]
    def inside(point, polygon):
        x, y = point; hit = False
        for i, first in enumerate(polygon):
            second = polygon[(i+1) % len(polygon)]
            if (first[1] > y) != (second[1] > y):
                cross_x = first[0] + (y-first[1])*(second[0]-first[0])/(second[1]-first[1])
                if x < cross_x: hit = not hit
        return hit
    for i, (first_id, first) in enumerate(polygons):
        for second_id, second in polygons[i+1:]:
            if any(inside(point, second) for point in first) or any(inside(point, first) for point in second):
                errors.append(f'{first_id} and {second_id}: room boundaries overlap')
    return errors


def render(plan, path):
    rooms = plan['rooms']; height = max(450, 190 + 100*len(rooms))
    subtitle = ('Provisional LiDAR geometry · metric accuracy unvalidated'
                if plan['plan']['status'] == 'inferred' else 'Geometry and scale unresolved')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}">', '<rect width="100%" height="100%" fill="#f8fafc"/>', '<style>text{font-family:Arial,sans-serif;fill:#172b4d}.title{font-size:26px;font-weight:bold}.body{font-size:16px}.small{font-size:13px;fill:#52657d}</style>', f'<text x="36" y="45" class="title">Property plan: {html.escape(plan["property_id"])}</text>', f'<text x="36" y="72" class="small">{html.escape(plan["capture"]["tier"].title())} capture · {html.escape(subtitle)}</text>']
    for i, room in enumerate(rooms):
        y = 105 + i*100
        area = room['floor_area']['value']
        area_label = f'{area:.2f} m²' if area is not None else 'unknown m²'
        opening_count = len(room['openings'])
        opening_label = f'{opening_count} candidate(s), unverified' if opening_count else 'unassessed'
        damage_count = sum(item['room_id'] == room['id'] for item in plan['damage_regions'])
        parts += [f'<rect x="36" y="{y}" width="920" height="82" rx="8" fill="white" stroke="#94a3b8" stroke-dasharray="7 5"/>', f'<text x="55" y="{y+29}" class="body">{html.escape(room["name"])} ({html.escape(room["id"])})</text>', f'<text x="55" y="{y+55}" class="small">Area: {area_label} · Openings: {opening_label} · Damage regions: {damage_count} · {html.escape(room["status"])}</text>']
    y = 125 + 100*len(rooms)
    parts += [f'<text x="36" y="{y}" class="body">Connections: {len(plan["adjacency"])} supported</text>', f'<text x="36" y="{y+27}" class="small">Dashed cards indicate indexed spaces; any drawn LiDAR layout is provisional.</text>']
    if plan.get('placement_ambiguities'):
        groups = ', '.join(', '.join(item['room_ids']) for item in plan['placement_ambiguities'])
        parts.append(f'<text x="36" y="{y+47}" class="small">Unresolved placement: {html.escape(groups[:110])}</text>')
    for i, warning in enumerate(plan['warnings'][:3]):
        parts.append(f'<text x="36" y="{y+60+i*22}" class="small">⚠ {html.escape(warning[:115])}</text>')
    polygons = [room['boundary'] for room in rooms if room['boundary'] is not None]
    if polygons:
        xs = [p[0] for poly in polygons for p in poly]; ys = [p[1] for poly in polygons for p in poly]
        scale = min(850/max(max(xs)-min(xs), .01), 550/max(max(ys)-min(ys), .01))
        offset_y = height + 100
        parts[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height+750}" viewBox="0 0 1000 {height+750}">'
        parts.append(f'<text x="36" y="{offset_y-20}" class="title">Provisional layout</text>')
        def xy(p): return (75+(p[0]-min(xs))*scale, offset_y+550-(p[1]-min(ys))*scale)
        for room in rooms:
            poly = room['boundary']
            if poly is None: continue
            points = ' '.join(f'{x:.1f},{y:.1f}' for x,y in map(xy,poly))
            parts.append(f'<polygon points="{points}" fill="#dbeafe" stroke="#1e3a5f" stroke-width="3"/>')
            center = (sum(p[0] for p in poly)/len(poly), sum(p[1] for p in poly)/len(poly))
            cx,cy=xy(center)
            parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" class="body">{html.escape(room["name"])}</text>')
            for wall in room['surfaces']:
                if wall['kind'] != 'wall' or wall['length']['value'] is None: continue
                midpoint = [(wall['line'][0][j]+wall['line'][1][j])/2 for j in (0,1)]
                wx,wy=xy(midpoint)
                parts.append(f'<text x="{wx:.1f}" y="{wy:.1f}" class="small">{wall["length"]["value"]:.2f} m</text>')
            for opening in room['openings']:
                parts.append(f'<text x="{cx:.1f}" y="{cy+24:.1f}" class="small">Possible {html.escape(opening["kind"])}: {opening["width"]["value"] if opening["width"]["value"] is not None else "?"} m wide, height unknown</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')
