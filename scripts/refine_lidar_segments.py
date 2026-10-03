"""Rebuild named spaces from explicitly reviewed scan ranges, without reference sizes.

This is an assisted reconstruction, not automatic room recognition. Geometry stays
in the original scan coordinate system; the original run is never overwritten.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astra import __main__  # Configure local cache paths before plotting imports.
import numpy as np
from astra.io import sha256, write_json
from astra.layout import build_layout
from astra.openings import geometric_openings
from astra.pipeline import adjacency_from_openings
from astra.quality import topology_quality
from astra.schema import validate
from astra.export import render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--segments', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.source.resolve():
        parser.error('Use a separate output folder to preserve the automatic run.')
    args.output.mkdir(parents=True, exist_ok=True)
    spec = json.loads(args.segments.read_text())
    original = json.loads((args.source / 'result.json').read_text())
    geometry = dict(np.load(args.source / 'geometry/geometry.npz'))
    layout = {'rooms': [], 'surfaces': [], 'openings': [], 'adjacency': []}
    evidence = []
    for item in spec['spaces']:
        if 'retain_automatic_room' in item:
            rid = item['retain_automatic_room']
            room = copy.deepcopy(next(r for r in original['rooms'] if r['id'] == rid))
            room['name'] = item['name']
            layout['rooms'].append(room)
            surfaces = copy.deepcopy([s for s in original['surfaces'] if s['room_id'] == rid])
            for surface in surfaces:
                surface['damage_ids'] = []
            layout['surfaces'].extend(surfaces)
            evidence.append(item)
            continue
        low, high = item['source_frame_range_inclusive']
        selected = np.flatnonzero((geometry['indices'] >= low) & (geometry['indices'] <= high))
        if len(selected) < 2:
            raise ValueError(f"Insufficient frames for {item['name']}")
        mask = np.isin(geometry['frame_ids'], selected)
        remap = np.full(len(geometry['indices']), -1)
        remap[selected] = np.arange(len(selected))
        local = {k: geometry[k][mask] for k in ['points', 'normals']}
        local['frame_ids'] = remap[geometry['frame_ids'][mask]]
        local['poses'] = geometry['poses'][selected]
        part = build_layout(local, single_room=True, room_names=[item['name']])
        if len(part['rooms']) != 1:
            raise ValueError(f"Could not extract one space for {item['name']}")
        for room in part['rooms']:
            room['camera_visits'] = selected[room['camera_visits']].tolist()
        layout['rooms'].extend(part['rooms'])
        layout['surfaces'].extend(part['surfaces'])
        evidence.append({**item, 'selected_source_frames': geometry['indices'][selected].tolist()})
    layout['openings'] = geometric_openings(geometry, layout['surfaces'])
    layout['adjacency'] = adjacency_from_openings(layout)
    result = {
        'schema_version': original['schema_version'],
        'capture_id': original['capture_id'] + '_assisted', 'tier': 'lidar',
        'status': 'provisional_reconstruction', **layout,
        'layout_quality': topology_quality(layout['rooms'], layout['adjacency'], 'lidar', physical_stitch=True),
        'damage': [], 'concealed_damage_flags': [], 'scope_items': [],
        'warnings': [
            'Assisted reconstruction: room frame ranges and names were selected by visual review; this is not fully automatic segmentation.',
            'The original automatic layout merged hall and kitchen; its outputs remain in the source run.',
            'Connector retains the automatic geometry and remains inaccurate; its boundaries were not replaced with reference dimensions.',
            'Opening proposals are geometric and unverified; missing adjacency does not establish absence of a doorway.',
            'Reference measurements and declared connections were not used to fit geometry.',
            'Intervals are engineering ranges, not empirically calibrated confidence intervals.',
            'Damage detection was not rerun for this assisted layout.',
            'Official evaluator schema unavailable; validated against astra.provisional.v1.',
        ] + original['diagnostics']['quality']['warnings'],
        'diagnostics': {'assisted_segmentation': evidence},
    }
    validate(result)
    write_json(args.output / 'result.json', result)
    write_json(args.output / 'segments.json', spec)
    write_json(args.output / 'provenance.json', {
        'source_run': str(args.source.resolve()),
        'source_result_sha256': sha256(args.source / 'result.json'),
        'source_geometry_sha256': sha256(args.source / 'geometry/geometry.npz'),
        'script_sha256': sha256(Path(__file__)),
        'segments_sha256': sha256(args.segments),
        'ground_truth_used_for_inference': False,
        'manual_frame_selection': True,
    })
    render(result, args.output)
    write_json(args.output / 'run_status.json', {'status': 'complete_with_limitations', 'assisted': True})
    print(args.output / 'report.html')


if __name__ == '__main__':
    main()
