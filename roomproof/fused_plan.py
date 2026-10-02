"""Assemble a conservative common plan from independent completed captures."""

import copy
import json
from pathlib import Path

from .cli import sha256, write_json
from .plan import render, unknown, validate


def assemble_fused_plan(photo_run, video_run, lidar_run, link_report,
                        registration, opening_links, run_dir,
                        verified_connections=(), registered_openings=None):
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
    if registered_openings:
        fit = json.loads((Path(lidar_run)/'lidar_geometry.json').read_text())['room_fit']
        gaps = fit.get('opening_gap_candidates', [])
        slug = result['rooms'][0]['id'].removeprefix('room-')
        for item in registered_openings.get('accepted_openings', []):
            gap_id = item['lidar_gap_id']
            if not gap_id.startswith('opening-gap-'):
                continue
            number = int(gap_id.removeprefix('opening-gap-'))
            if not 1 <= number <= len(gaps):
                continue
            opening = next((candidate for candidate in result['rooms'][0]['openings']
                            if candidate['id'] == f'opening-{slug}-candidate-{number}'), None)
            if opening is None:
                continue
            from .plan import _provisional
            refs = sorted(set(opening['source_refs']) |
                          {view['source_ref'] for view in item['source_views']})
            opening['kind'] = ('open_passage' if gaps[number-1]['kind_hypothesis'] ==
                               'wide_open_passage_depth_gap' else 'door')
            opening['status'] = 'inferred'
            opening['width'] = _provisional(gaps[number-1]['width_m'], 'm', refs)
            opening['offset_along_wall'] = _provisional(
                gaps[number-1]['offset_along_wall_m'], 'm', refs)
            opening['source_refs'] = refs
    from .room_placement import apply_verified_placements, solve_placements
    placement = solve_placements(result['rooms'], verified_connections)
    result = apply_verified_placements(result, placement, verified_connections)
    placement_path = Path(run_dir)/'room_placement.json'
    write_json(placement_path, placement)
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
        f"Cross-capture pose probes: {registration.get('plausible_assumed_pose_count', 0)} plausible under assumed calibration; {len(registration.get('accepted_camera_poses', []))} accepted calibrated views.",
        f"Opening-region links: {opening_links['link_count']} unverified correspondences; none establishes adjacency or a measured opening.",
        f"Metric room placement: {placement['status']}; see room_placement.json.",
        'Fusion retains only the LiDAR-supported room geometry; independent capture labels do not supply missing walls or scale.',
    ])
    errors = validate(result)
    if errors:
        raise ValueError('fused plan invalid: ' + '; '.join(errors[:8]))
    path = Path(run_dir)/'property_plan.json'
    svg = Path(run_dir)/'property_plan.svg'
    write_json(path, result)
    render(result, svg)
    return result, [{'path': str(placement_path), 'sha256': sha256(placement_path)},
                    {'path': str(path), 'sha256': sha256(path)},
                    {'path': str(svg), 'sha256': sha256(svg)}]
