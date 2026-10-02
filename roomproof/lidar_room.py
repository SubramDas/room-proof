"""Evidence-gated rectangular room hypothesis from Stray depth patches.

This module never reads reference measurements. A fitted rectangle is a
provisional sensor estimate and must be checked against separate laser truth.
"""

from collections import Counter, defaultdict
import math
import statistics


def _angle_distance(a, b):
    return abs((a - b + 90) % 180 - 90)


def _height_pair(horizontal, camera_y):
    width = .05
    counts = Counter(round(y / width) for y, _, _ in horizontal)
    frames = defaultdict(set)
    for y, _, frame_id in horizontal:
        frames[round(y / width)].add(frame_id)
    lower = [(key, count) for key, count in counts.items()
             if key*width < camera_y-.3 and count >= 250 and len(frames[key]) >= 4]
    upper = [(key, count) for key, count in counts.items()
             if key*width > camera_y+.3 and count >= 250 and len(frames[key]) >= 4]
    choices = [(lo, hi, math.sqrt(a*b)*(hi-lo)*width)
               for lo, a in lower for hi, b in upper if 1.8 <= (hi-lo)*width <= 4.2]
    if not choices:
        return None
    lo, hi, _ = max(choices, key=lambda item: item[2])
    result = []
    for key in (lo, hi):
        samples = [(y, frame_id) for y, _, frame_id in horizontal
                   if abs(y-key*width) <= .075]
        center = statistics.median(y for y, _ in samples)
        result.append({'height_m': round(center, 4), 'samples': len(samples),
                       'frame_ids': sorted({frame_id for _, frame_id in samples})})
    return result


def _wall_axis(vertical):
    angles = [(math.degrees(math.atan2(nz, nx)) % 180, frame_id)
              for _, _, _, nx, nz, frame_id in vertical]
    if len(angles) < 1000:
        return None
    bins = Counter(round(angle / 5) % 36 for angle, _ in angles)
    scores = {key: sum(bins[(key+step) % 36] for step in range(-2, 3))
              for key in range(36)}
    first = max(scores, key=scores.get) * 5
    second = (first + 90) % 180
    support_a = [(angle, frame_id) for angle, frame_id in angles
                 if _angle_distance(angle, first) <= 15]
    support_b = [(angle, frame_id) for angle, frame_id in angles
                 if _angle_distance(angle, second) <= 15]
    if (min(len(support_a), len(support_b)) < 300 or
            min(len({fid for _, fid in support_a}), len({fid for _, fid in support_b})) < 4):
        return None
    # Double angles make a wall normal and its opposite equivalent.
    vx = sum(math.cos(2*math.radians(angle)) for angle, _ in support_a)
    vz = sum(math.sin(2*math.radians(angle)) for angle, _ in support_a)
    refined = math.degrees(math.atan2(vz, vx))/2 % 180
    return {'first_angle_degrees': round(refined, 3),
            'second_angle_degrees': round((refined+90) % 180, 3),
            'normal_samples': [len(support_a), len(support_b)]}


def _wall_pair(vertical, angle, floor_y, ceiling_y):
    step = .1
    nx, nz = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    wall_points = [(x, y, z, frame_id) for x, y, z, vx, vz, frame_id in vertical
                   if floor_y+.25 <= y <= ceiling_y-.25 and
                   _angle_distance(math.degrees(math.atan2(vz, vx)) % 180, angle) <= 15]
    if len(wall_points) < 600:
        return None
    bins = Counter(round((nx*x+nz*z)/step) for x, _, z, _ in wall_points)
    smooth = {key: sum(bins.get(key+offset, 0) for offset in (-1, 0, 1)) for key in bins}
    peaks = []
    for key, count in sorted(smooth.items(), key=lambda item: (-item[1], item[0])):
        if all(abs(key-previous) > 2 for previous, _ in peaks):
            peaks.append((key, count))
        if len(peaks) == 12:
            break
    minimum = max(75, len(wall_points)*.015)
    pairs = [(left, right, math.sqrt(a*b)*(right-left)*step)
             for left, a in peaks for right, b in peaks
             if left < right and a >= minimum and b >= minimum
             and 1.5 <= (right-left)*step <= 8.0]
    if not pairs:
        return None
    left, right, _ = max(pairs, key=lambda item: item[2])
    walls = []
    for key in (left, right):
        center = key*step
        samples = [(nx*x+nz*z, y, frame_id) for x, y, z, frame_id in wall_points
                   if abs(nx*x+nz*z-center) <= .12]
        ys = sorted(y for _, y, _ in samples)
        if len(samples) < minimum or len({fid for _, _, fid in samples}) < 4:
            return None
        if ys[int(.95*(len(ys)-1))] - ys[int(.05*(len(ys)-1))] < 1.4:
            return None
        walls.append({'offset_m': round(statistics.median(d for d, _, _ in samples), 4),
                      'samples': len(samples),
                      'vertical_span_p05_p95_m': round(ys[int(.95*(len(ys)-1))]-ys[int(.05*(len(ys)-1))], 3),
                      'frame_ids': sorted({fid for _, _, fid in samples})})
    return walls


def _opening_gap_candidates(frame_points, boundary, floor_y, ceiling_y):
    """Find wall-plane holes only as unverified depth-gap hypotheses."""
    candidates = []
    for wall_index in range(4):
        start, end = boundary[wall_index], boundary[(wall_index+1) % 4]
        length = math.dist(start, end)
        count = max(1, round(length/.1))
        bins = [[0, 0, 0] for _ in range(count)]
        frame_ids = [set() for _ in range(count)]
        ux, uz = (end[0]-start[0])/length, (end[1]-start[1])/length
        for fid, points in frame_points.items():
            for x, y, z in points:
                along = (x-start[0])*ux + (z-start[1])*uz
                distance = abs((x-start[0])*(-uz)+(z-start[1])*ux)
                height = y-floor_y
                if not 0 <= along < length or distance > .1 or not .1 < height < ceiling_y-floor_y-.1:
                    continue
                cell = min(count-1, int(along/length*count))
                level = 0 if height < .6 else 1 if height < 2.1 else 2
                bins[cell][level] += 1
                frame_ids[cell].add(fid)
        if count < 12:
            continue
        medians = [statistics.median([row[level] for row in bins if row[level] > 0])
                   if any(row[level] for row in bins) else 0 for level in range(3)]
        if min(medians) < 5:
            continue
        def supported(cell):
            return bins[cell][0] >= .3*medians[0] and bins[cell][1] >= .3*medians[1]
        gap = [bins[i][0] < .15*medians[0] and bins[i][1] < .15*medians[1]
               and bins[i][2] >= .3*medians[2] for i in range(count)]
        index = 0
        while index < count:
            if not gap[index]:
                index += 1
                continue
            end_index = index
            while end_index < count and gap[end_index]:
                end_index += 1
            width = (end_index-index)*length/count
            left = any(supported(cell) for cell in range(max(0,index-3), index))
            right = any(supported(cell) for cell in range(end_index,min(count,end_index+3)))
            if .35 <= width <= 1.6 and index >= 2 and end_index <= count-2 and left and right:
                evidence = sorted(set().union(*frame_ids[max(0,index-3):min(count,end_index+3)]))
                candidates.append({'wall_index': wall_index, 'kind_hypothesis': 'doorway_depth_gap',
                                   'status': 'unverified', 'offset_along_wall_m': round(index*length/count, 3),
                                   'width_m': round(width, 3), 'frame_ids': evidence,
                                   'reason': 'low/mid wall returns absent beneath supported upper wall; RGB and occlusion checks pending'})
            index = end_index
    return candidates


def fit_single_room(frame_points, horizontal, vertical, camera_y, camera_positions=None):
    """Return a rectangle only if floor, ceiling, and four walls have support."""
    result = {'status': 'unresolved', 'method': 'multi-frame horizontal patches and orthogonal mid-height wall peaks',
              'warnings': [], 'floor': None, 'ceiling': None, 'axes': None, 'walls': None,
              'boundary_xz_m': None, 'area_m2': None, 'ceiling_height_m': None}
    heights = _height_pair(horizontal, camera_y)
    if heights is None:
        result['warnings'].append('Cannot identify both a supported floor and ceiling plane.')
        return result
    result['floor'], result['ceiling'] = heights
    axis = _wall_axis(vertical)
    if axis is None:
        result['warnings'].append('Two supported perpendicular wall directions are unavailable.')
        return result
    result['axes'] = axis
    floor_y, ceiling_y = heights[0]['height_m'], heights[1]['height_m']
    mid_points = [(x, y, z, fid) for fid, points in frame_points.items()
                  for x, y, z in points if floor_y+.25 <= y <= ceiling_y-.25]
    if len(mid_points) < 3000:
        result['warnings'].append('Too few mid-height 3D points to fit four walls.')
        return result
    first = _wall_pair(vertical, axis['first_angle_degrees'], floor_y, ceiling_y)
    second = _wall_pair(vertical, axis['second_angle_degrees'], floor_y, ceiling_y)
    if first is None or second is None:
        result['warnings'].append('Four multi-frame wall planes were not supported.')
        return result
    angles = [math.radians(axis['first_angle_degrees']), math.radians(axis['second_angle_degrees'])]
    normals = [(math.cos(angle), math.sin(angle)) for angle in angles]
    determinant = normals[0][0]*normals[1][1]-normals[0][1]*normals[1][0]
    if abs(determinant) < .95:
        result['warnings'].append('Wall directions are not sufficiently perpendicular.')
        return result
    def intersection(a, b):
        return [round((a*normals[1][1]-b*normals[0][1])/determinant, 4),
                round((b*normals[0][0]-a*normals[1][0])/determinant, 4)]
    a0, a1 = (wall['offset_m'] for wall in first)
    b0, b1 = (wall['offset_m'] for wall in second)
    boundary = [intersection(a0,b0),intersection(a1,b0),intersection(a1,b1),intersection(a0,b1)]
    width_a, width_b = a1-a0, b1-b0
    result.update({'status': 'inferred', 'walls': [first, second], 'boundary_xz_m': boundary,
                   'axis_lengths_m': [round(width_a, 4), round(width_b, 4)],
                   'area_m2': round(width_a*width_b, 4),
                   'ceiling_height_m': round(ceiling_y-floor_y, 4),
                   'warnings': ['Rectangular LiDAR fit is provisional; scale and accuracy are uncalibrated.',
                                'Openings are not yet detected; wall lines may cross doorways.']})
    result['opening_gap_candidates'] = _opening_gap_candidates(frame_points, boundary, floor_y, ceiling_y)
    if result['opening_gap_candidates']:
        result['warnings'].append(f"{len(result['opening_gap_candidates'])} possible doorway depth gaps are unverified plan candidates; RGB/occlusion confirmation is needed.")
    if camera_positions:
        inside = 0
        for x, _, z in camera_positions:
            projected = [nx*x+nz*z for nx, nz in normals]
            if all(pair[0]['offset_m']-.2 <= projected[index] <= pair[1]['offset_m']+.2
                   for index, pair in enumerate((first, second))):
                inside += 1
        fraction = inside/len(camera_positions)
        result['camera_inside_fraction'] = round(fraction, 3)
        if fraction < .9:
            result['warnings'].append('Some camera poses fall outside the fitted room; the scan may include doorway or adjacent-space views.')
    return result
