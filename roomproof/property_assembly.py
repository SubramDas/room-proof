"""Assemble separately scanned rooms using shared calibrated opening evidence."""

import copy
import hashlib
import json
from pathlib import Path

from .cli import sha256, write_json
from .plan import render, unknown, validate
from .room_placement import apply_verified_placements, solve_placements


def _scan_room(plan):
    metric = [room for room in plan['rooms'] if room['boundary'] is not None]
    if len(metric) != 1:
        raise ValueError('each linked room run must contain exactly one measured LiDAR room')
    return metric[0]


def _shared_connections(entries):
    by_candidate = {}
    for room, openings in entries:
        for item in openings.get('accepted_openings', []):
            for view in item['source_views']:
                by_candidate.setdefault(view['candidate_id'], []).append((room, item, view))
    results = {}
    for candidate_id, sightings in by_candidate.items():
        for i, (first_room, first, first_view) in enumerate(sightings):
            for second_room, second, second_view in sightings[i+1:]:
                if first_room['id'] == second_room['id']:
                    continue
                a, b = sorted((first_room['id'], second_room['id']))
                first_gap = first['lidar_gap_id'].removeprefix('opening-gap-')
                second_gap = second['lidar_gap_id'].removeprefix('opening-gap-')
                first_id = f"opening-{first_room['id'].removeprefix('room-')}-candidate-{first_gap}"
                second_id = f"opening-{second_room['id'].removeprefix('room-')}-candidate-{second_gap}"
                ids = (first_id, second_id) if first_room['id'] == a else (second_id, first_id)
                token = hashlib.sha256(f'{a}:{b}:{ids}'.encode()).hexdigest()[:12]
                key = (a, b, ids)
                result = results.setdefault(key, {
                    'id': f'connection-{token}', 'room_ids': [a, b],
                    'opening_ids': list(ids), 'status': 'verified_physical_opening',
                    'source_refs': set(), 'shared_visual_candidate_ids': set()})
                result['source_refs'].update((first_view['source_ref'], second_view['source_ref']))
                result['shared_visual_candidate_ids'].add(candidate_id)
    return [{**item, 'source_refs': sorted(item['source_refs']),
             'shared_visual_candidate_ids': sorted(item['shared_visual_candidate_ids'])}
            for item in results.values()]


def assemble_property(linked_runs, run_dir):
    """Write one plan, retaining local metrics but unknown global placement."""
    if len(linked_runs) < 2:
        raise ValueError('assemble-property needs at least two linked room runs')
    inputs = []
    for path in linked_runs:
        root = Path(path).resolve(strict=True)
        plan = json.loads((root/'property_plan.json').read_text())
        openings = json.loads((root/'registered_openings.json').read_text())
        inputs.append((root, plan, openings))
    if len({plan['property_id'] for _, plan, _ in inputs}) != 1:
        raise ValueError('linked room runs must have the same property ID')
    metric_rooms = [copy.deepcopy(_scan_room(plan)) for _, plan, _ in inputs]
    if len({room['id'] for room in metric_rooms}) != len(metric_rooms):
        raise ValueError('linked room runs have duplicate measured room IDs')
    rooms = list(metric_rooms)
    known_ids = {room['id'] for room in rooms}
    for _, source_plan, _ in inputs:
        for room in source_plan['rooms']:
            if room['id'] not in known_ids:
                rooms.append(copy.deepcopy(room))
                known_ids.add(room['id'])
    connections = _shared_connections([(room, openings)
                                       for room, (_, _, openings) in zip(metric_rooms, inputs)])
    placement = solve_placements(rooms, connections)
    result = copy.deepcopy(inputs[0][1])
    result['run_id'] = Path(run_dir).name
    result['capture'] = {
        'capture_id': f'cap-property-{Path(run_dir).name.removeprefix("run-")[:16]}',
        'tier': 'fusion', 'device_model': None, 'ios_version': None,
        'capture_app': None, 'capture_app_version': None,
        'source_refs': sorted({ref for _, plan, _ in inputs
                               for ref in plan['capture']['source_refs']}),
    }
    result['rooms'] = rooms
    result['adjacency'] = []
    result['placement_ambiguities'] = []
    result = apply_verified_placements(result, placement, connections)
    unplaced = set(placement['unplaced_room_ids'])
    if unplaced:
        # Room-local dimensions remain in measurements; their coordinates are
        # removed from the common property frame until a transform is known.
        for room in result['rooms']:
            if room['id'] not in unplaced:
                continue
            room['boundary'] = None
            room['status'] = 'unresolved'
            for surface in room['surfaces']:
                if surface['kind'] == 'wall':
                    surface['line'] = [[0, 0], [0, 0]]
                    surface['status'] = 'unresolved'
        result['placement_ambiguities'].append({
            'room_ids': sorted({placement['anchor_room_id']} | unplaced),
            'reason': 'No verified shared physical opening gives a unique cross-scan transform.',
            'source_refs': result['capture']['source_refs'],
        })
    result['plan']['status'] = 'unresolved'
    result['plan']['footprint'] = None
    result['plan']['floor_area'] = unknown('m2', result['capture']['source_refs'])
    result['plan']['rendered_plan_path'] = 'property_plan.svg'
    result['warnings'] = sorted(set(result['warnings']) |
                                {warning for _, plan, _ in inputs for warning in plan['warnings']})
    result['warnings'].append(
        f"Property assembly: {len(connections)} shared calibrated opening connection(s), "
        f"{len(unplaced)} unplaced room(s).")
    errors = validate(result)
    if errors:
        raise ValueError('assembled property plan invalid: ' + '; '.join(errors[:8]))
    output = {'report_version': '0.1.0', 'status': placement['status'],
              'linked_runs': [str(root) for root, _, _ in inputs],
              'verified_connections': connections, 'placement': placement}
    report_path = Path(run_dir)/'property_assembly.json'
    plan_path = Path(run_dir)/'property_plan.json'
    svg_path = Path(run_dir)/'property_plan.svg'
    write_json(report_path, output)
    write_json(plan_path, result)
    render(result, svg_path)
    return output, [{'path': str(path), 'sha256': sha256(path)}
                    for path in (report_path, plan_path, svg_path)]
