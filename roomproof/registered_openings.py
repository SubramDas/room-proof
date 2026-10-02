"""Compare calibrated ordinary-image jamb rays with scan-supported gaps."""

import math


def _ray_on_wall(pixel, camera, pose, wall):
    import cv2
    import numpy as np

    rotation, _ = cv2.Rodrigues(np.asarray(pose['world_to_camera_rvec'], dtype=float))
    translation = np.asarray(pose['world_to_camera_tvec_m'], dtype=float)
    origin = -rotation.T @ translation
    local = np.asarray([(pixel[0]-camera['cx'])/camera['fx'],
                        (pixel[1]-camera['cy'])/camera['fy'], 1.], dtype=float)
    direction = rotation.T @ local
    start, end = wall
    sx, sz = end[0]-start[0], end[1]-start[1]
    denominator = direction[0]*(-sz)+sx*direction[2]
    if abs(denominator) < 1e-8:
        return None
    dx, dz = start[0]-origin[0], start[1]-origin[2]
    travel = (dx*(-sz)+sx*dz)/denominator
    fraction = (direction[0]*dz-direction[2]*dx)/denominator
    if travel <= 0 or not 0 <= fraction <= 1:
        return None
    return fraction*math.hypot(sx, sz)


def link_registered_openings(records, opening_groups, registration,
                             lidar_links, room_fit, calibration):
    """Require matched scan regions, calibrated poses, and matching 3D edges."""
    result = {'report_version': '0.1.0', 'status': 'unresolved',
              'registered_opening_hypotheses': [], 'accepted_openings': [],
              'warnings': []}
    poses = {item['left_source_ref']: item for item in registration.get('accepted_camera_poses', [])}
    if not poses or not calibration:
        result['warnings'].append('No accepted calibrated ordinary-image camera pose; opening rays remain unscaled.')
        return result
    gaps = room_fit.get('opening_gap_candidates', [])
    boundary = room_fit.get('boundary_xz_m')
    if not boundary or not gaps:
        result['warnings'].append('No supported LiDAR wall boundary and depth gap to associate.')
        return result
    candidates = {}
    for pair in records:
        for side in ('left', 'right'):
            for candidate in pair[f'{side}_opening_proposals']:
                candidates[candidate['candidate_id']] = {
                    **candidate, 'source_ref': pair[f'{side}_source_ref'],
                    'tier': pair[f'{side}_tier'],
                    'image_size': pair[f'{side}_image_size']}
    scan_links = {item['candidate_id']: item for item in lidar_links.get('records', [])}
    for group_number, group in enumerate(opening_groups['groups'], 1):
        scan_support = []
        for candidate_id in group['candidate_ids']:
            linked = scan_links.get(candidate_id)
            if linked and linked['status'] == 'supported_proposal':
                scan_support.extend(linked.get('matching_depth_gap_ids', []))
        unique_gaps = sorted(set(scan_support))
        if len(unique_gaps) != 1:
            continue
        gap_id = unique_gaps[0]
        if not gap_id.startswith('opening-gap-'):
            continue
        number = int(gap_id.removeprefix('opening-gap-'))
        if number > len(gaps):
            continue
        gap = gaps[number-1]
        if len(gap.get('both_edges_visible_frame_ids', [])) < 2:
            continue
        wall_index = gap['wall_index']
        wall = [boundary[wall_index], boundary[(wall_index+1)%len(boundary)]]
        matches = []
        for candidate_id in group['candidate_ids']:
            candidate = candidates.get(candidate_id)
            if not candidate or candidate['tier'] not in ('photo', 'video'):
                continue
            pose = poses.get(candidate['source_ref'])
            if pose is None:
                continue
            camera = calibration['camera_intrinsics'].get(
                candidate['source_ref'], calibration['camera_intrinsics'].get(candidate['tier']))
            if not camera or camera['image_size'] != candidate['image_size']:
                continue
            x0, y0, x1, y1 = candidate['geometry']['xyxy_px']
            source_width = candidate['geometry']['image_width']
            source_height = candidate['geometry']['image_height']
            view_width, view_height = candidate['image_size']
            x0, x1 = x0*view_width/source_width, x1*view_width/source_width
            y0, y1 = y0*view_height/source_height, y1*view_height/source_height
            left = _ray_on_wall((x0, (y0+y1)/2), camera, pose, wall)
            right = _ray_on_wall((x1, (y0+y1)/2), camera, pose, wall)
            if left is None or right is None:
                continue
            predicted_offset = min(left, right)
            predicted_width = abs(right-left)
            if (abs(predicted_offset-gap['offset_along_wall_m']) > .2 or
                    abs(predicted_width-gap['width_m']) > max(.2, .2*gap['width_m'])):
                continue
            matches.append({'candidate_id': candidate_id, 'source_ref': candidate['source_ref'],
                            'projected_offset_m': round(predicted_offset, 3),
                            'projected_width_m': round(predicted_width, 3)})
        if not matches:
            continue
        hypothesis = {'opening_track_group_index': group_number,
                      'lidar_gap_id': gap_id, 'wall_index': wall_index,
                      'source_views': matches, 'scan_candidate_ids': sorted(set(group['candidate_ids']) & set(scan_links)),
                      'status': 'registered_opening_hypothesis'}
        result['registered_opening_hypotheses'].append(hypothesis)
        if len({item['source_ref'] for item in matches}) >= 2:
            result['accepted_openings'].append({**hypothesis,
                                                'status': 'registered_multi_view_opening'})
    result['status'] = 'accepted_openings' if result['accepted_openings'] else 'hypotheses_only'
    result['warnings'].append('Detector boxes are approximate jamb boundaries; accepted widths remain provisional pending independent measurement checks.')
    return result
