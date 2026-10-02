"""Assemble a conservative common plan from independent completed captures."""

import copy
import json
from pathlib import Path

from .cli import sha256, write_json
from .plan import render, unknown, validate


def assemble_fused_plan(photo_run, video_run, lidar_run, link_report,
                        registration, opening_links, run_dir):
    plans = [json.loads((Path(path)/'property_plan.json').read_text())
             for path in (photo_run, video_run, lidar_run)]
    photo, video, lidar = plans
    if len({plan['property_id'] for plan in plans}) != 1:
        raise ValueError('cannot fuse plans with different property IDs')
    result = copy.deepcopy(lidar)
    result['run_id'] = Path(run_dir).name
    result['capture'] = {
        'capture_id': f'cap-fusion-{Path(run_dir).name.removeprefix("run-")[:16]}',
        'tier': 'fusion', 'device_model': None, 'ios_version': None,
        'capture_app': None, 'capture_app_version': None,
        'source_refs': sorted({ref for plan in plans for ref in plan['capture']['source_refs']}),
    }
    known = {room['id'] for room in result['rooms']}
    for source in (photo, video):
        for room in source['rooms']:
            if room['id'] not in known:
                result['rooms'].append(copy.deepcopy(room))
                known.add(room['id'])
    unresolved = [room['id'] for room in result['rooms'] if room['boundary'] is None]
    if unresolved:
        result['plan']['status'] = 'unresolved'
        result['plan']['footprint'] = None
        result['plan']['floor_area'] = unknown('m2', result['capture']['source_refs'])
        result['placement_ambiguities'].append({
            'room_ids': unresolved,
            'reason': 'No verified metric placement relative to the LiDAR anchor; room folder labels are supplied IDs.',
            'source_refs': sorted({ref for room in result['rooms'] if room['id'] in unresolved
                                   for ref in room['source_refs']}),
        })
    result['plan']['rendered_plan_path'] = 'property_plan.svg'
    result['warnings'].extend([
        f"Cross-capture image links: {link_report['supported_2d_overlap_count']} supported 2D pairs; see cross_capture_links.json.",
        f"Cross-capture pose probes: {registration.get('plausible_assumed_pose_count', 0)} plausible under assumed calibration; no accepted metric registration.",
        f"Opening-region links: {opening_links['link_count']} unverified correspondences; none establishes adjacency or a measured opening.",
        'Fusion retains only the LiDAR-supported room geometry; independent capture labels do not supply missing walls or scale.',
    ])
    errors = validate(result)
    if errors:
        raise ValueError('fused plan invalid: ' + '; '.join(errors[:8]))
    path = Path(run_dir)/'property_plan.json'
    svg = Path(run_dir)/'property_plan.svg'
    write_json(path, result)
    render(result, svg)
    return result, [{'path': str(path), 'sha256': sha256(path)},
                    {'path': str(svg), 'sha256': sha256(svg)}]
