"""Gate video room-crossing claims on calibrated metric wall geometry."""

import math
import re


_FRAME = re.compile(r'#frame=(\d+)$')


def _frame(source_ref):
    match = _FRAME.search(source_ref)
    return int(match.group(1)) if match else None


def find_verified_crossings(registration, registered_openings, room_fit):
    boundary = room_fit.get('boundary_xz_m')
    gaps = room_fit.get('opening_gap_candidates', [])
    if not boundary or not registration.get('metric_registration_accepted'):
        return {'status': 'unresolved', 'verified_crossings': [],
                'reason': 'no calibrated video poses and supported metric wall boundary'}
    poses = sorted(((_frame(item['left_source_ref']), item)
                    for item in registration.get('accepted_camera_poses', [])
                    if '#frame=' in item['left_source_ref']), key=lambda row: row[0])
    crossings = []
    for opening in registered_openings.get('accepted_openings', []):
        number = int(opening['lidar_gap_id'].removeprefix('opening-gap-'))
        if not 1 <= number <= len(gaps):
            continue
        gap = gaps[number-1]
        wall_index = gap['wall_index']
        start, end = boundary[wall_index], boundary[(wall_index+1)%len(boundary)]
        dx, dz = end[0]-start[0], end[1]-start[1]
        length = math.hypot(dx, dz)
        opening_frames = [_frame(view['source_ref']) for view in opening['source_views']
                          if _frame(view['source_ref']) is not None]
        if not opening_frames:
            continue
        for (first_index, first), (second_index, second) in zip(poses, poses[1:]):
            if second_index-first_index > 300 or not any(
                    first_index-30 <= index <= second_index+30 for index in opening_frames):
                continue
            a, b = first['camera_center_m'], second['camera_center_m']
            side_a = ((a[0]-start[0])*(-dz)+(a[2]-start[1])*dx)/length
            side_b = ((b[0]-start[0])*(-dz)+(b[2]-start[1])*dx)/length
            if side_a*side_b >= 0 or min(abs(side_a), abs(side_b)) < .12:
                continue
            fraction = side_a/(side_a-side_b)
            cross_x = a[0]+fraction*(b[0]-a[0])
            cross_z = a[2]+fraction*(b[2]-a[2])
            along = ((cross_x-start[0])*dx+(cross_z-start[1])*dz)/length
            if not (gap['offset_along_wall_m']-.1 <= along <=
                    gap['offset_along_wall_m']+gap['width_m']+.1):
                continue
            crossings.append({
                'lidar_gap_id': opening['lidar_gap_id'],
                'before_video_source_ref': first['left_source_ref'],
                'after_video_source_ref': second['left_source_ref'],
                'crossing_xz_m': [round(cross_x, 3), round(cross_z, 3)],
                'offset_along_wall_m': round(along, 3),
                'status': 'calibrated_wall_crossing_supported',
                'reason': 'calibrated camera centers straddle a registered opening on one LiDAR wall',
            })
    return {'status': 'verified_crossings' if crossings else 'unresolved',
            'verified_crossings': crossings,
            'reason': None if crossings else 'no accepted pose sequence crosses a registered metric opening'}
