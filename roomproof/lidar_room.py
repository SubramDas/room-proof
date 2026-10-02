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


def _opening_gap_candidates(frame_points, boundary, floor_y, ceiling_y,
                            camera_positions=None):
    """Find wall-plane holes only as unverified depth-gap hypotheses."""
    candidates = []
    for wall_index in range(len(boundary)):
        start, end = boundary[wall_index], boundary[(wall_index+1) % 4]
        length = math.dist(start, end)
        count = max(1, round(length/.1))
        bins = [[0, 0, 0] for _ in range(count)]
        frame_ids = [set() for _ in range(count)]
        side_frame_ids = [set() for _ in range(count)]
        behind_counts = [0 for _ in range(count)]
        behind_frames = [set() for _ in range(count)]
        ux, uz = (end[0]-start[0])/length, (end[1]-start[1])/length
        camera_side = 1
        if camera_positions:
            signed = statistics.median((x-start[0])*(-uz)+(z-start[1])*ux
                                       for x, _, z in camera_positions)
            camera_side = 1 if signed >= 0 else -1
        for fid, points in frame_points.items():
            for x, y, z in points:
                along = (x-start[0])*ux + (z-start[1])*uz
                signed_distance = (x-start[0])*(-uz)+(z-start[1])*ux
                distance = abs(signed_distance)
                height = y-floor_y
                if not 0 <= along < length or not .1 < height < ceiling_y-floor_y-.1:
                    continue
                cell = min(count-1, int(along/length*count))
                if camera_side*signed_distance < -.25 and distance < 3.0 and height < 2.1:
                    behind_counts[cell] += 1
                    behind_frames[cell].add(fid)
                if distance > .1:
                    continue
                level = 0 if height < .6 else 1 if height < 2.1 else 2
                bins[cell][level] += 1
                frame_ids[cell].add(fid)
                if level in (0, 1):
                    side_frame_ids[cell].add(fid)
        if count < 12:
            continue
        medians = [statistics.median([row[level] for row in bins if row[level] > 0])
                   if any(row[level] for row in bins) else 0 for level in range(3)]
        if min(medians) < 5:
            continue
        def supported(cell):
            return bins[cell][0] >= .3*medians[0] and bins[cell][1] >= .3*medians[1]
        gap = [bins[i][0] < .15*medians[0] and bins[i][1] < .15*medians[1]
               and (bins[i][2] >= .3*medians[2] or
                    (behind_counts[i] >= 5 and len(behind_frames[i]) >= 2))
               for i in range(count)]
        index = 0
        while index < count:
            if not gap[index]:
                index += 1
                continue
            end_index = index
            while end_index < count and gap[end_index]:
                end_index += 1
            width = (end_index-index)*length/count
            left_cells = [cell for cell in range(max(0,index-3), index) if supported(cell)]
            right_cells = [cell for cell in range(end_index,min(count,end_index+3)) if supported(cell)]
            left = bool(left_cells)
            right = bool(right_cells)
            # An open passage can span most of a short wall. Width alone is
            # not evidence that a hole is a doorway, so retain it unverified.
            if .35 <= width <= min(3.2, .95*length) and index >= 1 and end_index <= count-1 and left and right:
                evidence = sorted(set().union(*frame_ids[max(0,index-3):min(count,end_index+3)]))
                side_views = sorted(set().union(*(side_frame_ids[cell] for cell in left_cells)) &
                                    set().union(*(side_frame_ids[cell] for cell in right_cells)))
                behind_views = sorted(set().union(*behind_frames[index:end_index]))
                kind = 'wide_open_passage_depth_gap' if width > 1.6 else 'doorway_depth_gap'
                candidates.append({'wall_index': wall_index, 'kind_hypothesis': kind,
                                   'status': 'unverified', 'offset_along_wall_m': round(index*length/count, 3),
                                   'width_m': round(width, 3), 'frame_ids': evidence,
                                   'left_edge_xz_m': [round(start[0]+ux*index*length/count, 3),
                                                      round(start[1]+uz*index*length/count, 3)],
                                   'right_edge_xz_m': [round(start[0]+ux*end_index*length/count, 3),
                                                       round(start[1]+uz*end_index*length/count, 3)],
                                   'edge_quantization_m': round(length/count, 3),
                                   'left_wall_support_cells': left_cells,
                                   'right_wall_support_cells': right_cells,
                                   'both_edges_visible_frame_ids': side_views,
                                   'behind_wall_frame_ids': behind_views,
                                   'reason': 'two wall-side depth edges with low mid-height returns; behind-wall returns or upper lintel support are hypotheses until RGB and occlusion checks agree'})
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
    result['opening_gap_candidates'] = _opening_gap_candidates(
        frame_points, boundary, floor_y, ceiling_y, camera_positions)
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


def fit_room(frame_points, horizontal, vertical, camera_y, camera_positions=None):
    """Select a supported rectangle or convex irregular boundary.

    The irregular alternative must independently close on depth-supported
    walls. A scan spanning several rooms or a concave shape stays unresolved
    when this evidence is insufficient.
    """
    rectangle = fit_single_room(frame_points, horizontal, vertical,
                                camera_y, camera_positions)
    heights = _height_pair(horizontal, camera_y)
    from .lidar_irregular import fit_irregular_room
    irregular = fit_irregular_room(vertical, heights[0] if heights else None,
                                   heights[1] if heights else None,
                                   camera_positions or [])
    rectangle['irregular_alternative'] = irregular
    if irregular['status'] != 'inferred':
        return rectangle
    choose = rectangle['status'] != 'inferred'
    if rectangle['status'] == 'inferred' and len(irregular['boundary_xz_m']) >= 5:
        area_change = abs(irregular['area_m2']-rectangle['area_m2'])/rectangle['area_m2']
        choose = (area_change >= .12 and
                  all(wall['edge_support_fraction'] >= .75
                      for wall in irregular['walls_ordered']))
    if not choose:
        return rectangle
    irregular.update({'floor': heights[0], 'ceiling': heights[1],
                      'shape': 'supported_convex_irregular',
                      'warnings': ['Convex multi-wall fit is provisional; concave or multiroom geometry is unresolved.',
                                   'Scale and RGB/depth projection still require independent validation.']})
    irregular['opening_gap_candidates'] = _opening_gap_candidates(
        frame_points, irregular['boundary_xz_m'],
        heights[0]['height_m'], heights[1]['height_m'], camera_positions)
    return irregular
