"""Conservative convex, multi-wall alternative to the rectangular room fit.

This stage uses only repeated depth-derived vertical patches. It cannot
recover a concave footprint or a scan spanning multiple rooms; those remain
unresolved rather than being converted into an invented polygon.
"""

from collections import defaultdict
import math
import statistics


def _clip(poly, nx, nz, offset):
    output = []
    for first, second in zip(poly, poly[1:] + poly[:1]):
        a = nx*first[0] + nz*first[1] - offset
        b = nx*second[0] + nz*second[1] - offset
        if a <= 0:
            output.append(first)
        if (a < 0 < b) or (b < 0 < a):
            fraction = a/(a-b)
            output.append((first[0]+fraction*(second[0]-first[0]),
                           first[1]+fraction*(second[1]-first[1])))
    return output


def _area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(poly, poly[1:]+poly[:1])))/2


def _inside(point, poly):
    signs = []
    for a, b in zip(poly, poly[1:]+poly[:1]):
        cross = (b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
        signs.append(cross)
    return all(value >= -.15 for value in signs) or all(value <= .15 for value in signs)


def fit_irregular_room(vertical, floor, ceiling, camera_positions):
    """Return a supported convex polygon, or a diagnostic unresolved record."""
    result = {'status': 'unresolved', 'method': 'depth-normal wall planes and convex half-plane intersection',
              'reason': None, 'candidate_wall_count': 0, 'walls_ordered': []}
    if not camera_positions or floor is None or ceiling is None:
        result['reason'] = 'floor, ceiling, or camera trajectory unavailable'
        return result
    floor_y, ceiling_y = floor['height_m'], ceiling['height_m']
    grouped = defaultdict(list)
    for x, y, z, nx, nz, frame_id in vertical:
        if not floor_y+.25 <= y <= ceiling_y-.25:
            continue
        angle = math.atan2(nz, nx)
        if angle < 0:
            angle += math.pi; nx, nz = -nx, -nz
        if angle >= math.pi:
            angle -= math.pi; nx, nz = -nx, -nz
        key = (round(math.degrees(angle)/8), round((nx*x+nz*z)/.12))
        grouped[key].append((x, y, z, frame_id))
    candidates = []
    for (angle_bin, distance_bin), members in grouped.items():
        frames = {item[3] for item in members}
        if len(members) < 100 or len(frames) < 3:
            continue
        ys = sorted(item[1] for item in members)
        angle = math.radians(angle_bin*8)
        nx, nz = math.cos(angle), math.sin(angle)
        lateral = sorted(-nz*item[0]+nx*item[2] for item in members)
        vertical_span = ys[int(.95*(len(ys)-1))]-ys[int(.05*(len(ys)-1))]
        lateral_span = lateral[int(.95*(len(lateral)-1))]-lateral[int(.05*(len(lateral)-1))]
        if vertical_span < 1.4 or lateral_span < .8:
            continue
        offset = statistics.median(nx*x+nz*z for x, _, z, _ in members)
        residuals = sorted(abs(nx*x+nz*z-offset) for x, _, z, _ in members)
        residual_p90 = residuals[int(.9*(len(residuals)-1))]
        if residual_p90 > .08:
            continue
        candidates.append({'normal': [nx, nz], 'offset_m': offset,
                           'samples': len(members), 'frame_ids': sorted(frames),
                           'point_to_plane_residual_p90_m': round(residual_p90, 4),
                           'vertical_span_m': vertical_span, 'lateral_span_m': lateral_span,
                           'lateral_range_m': [lateral[int(.05*(len(lateral)-1))],
                                               lateral[int(.95*(len(lateral)-1))]]})
    candidates.sort(key=lambda item: (-len(item['frame_ids']), -item['samples']))
    unique = []
    for candidate in candidates:
        normal = candidate['normal']
        if any(abs(abs(sum(a*b for a, b in zip(normal, other['normal'])))-1) < .025
               and abs(candidate['offset_m']-other['offset_m']) < .25 for other in unique):
            continue
        unique.append(candidate)
        if len(unique) >= 12:
            break
    result['candidate_wall_count'] = len(unique)
    if len(unique) < 3:
        result['reason'] = 'fewer than three repeated depth-supported wall planes'
        return result
    center = (statistics.median(p[0] for p in camera_positions),
              statistics.median(p[2] for p in camera_positions))
    radius = 10.0
    polygon = [(center[0]-radius, center[1]-radius),
               (center[0]+radius, center[1]-radius),
               (center[0]+radius, center[1]+radius),
               (center[0]-radius, center[1]+radius)]
    oriented = []
    for wall in unique:
        nx, nz = wall['normal']; offset = wall['offset_m']
        lateral_range = wall['lateral_range_m']
        if nx*center[0]+nz*center[1] > offset:
            nx, nz, offset = -nx, -nz, -offset
            lateral_range = [-lateral_range[1], -lateral_range[0]]
        oriented.append({**wall, 'outward_normal': [nx, nz], 'outward_offset_m': offset,
                         'lateral_range_m': lateral_range})
        polygon = _clip(polygon, nx, nz, offset)
        if len(polygon) < 3:
            result['reason'] = 'wall half-planes conflict'
            return result
    compact = []
    for point in polygon:
        if not compact or math.dist(point, compact[-1]) > .04:
            compact.append(point)
    if len(compact) > 1 and math.dist(compact[0], compact[-1]) <= .04:
        compact.pop()
    polygon = compact
    if any(abs(value-center[axis]) >= radius-.2 for point in polygon
           for axis, value in enumerate(point)):
        result['reason'] = 'wall planes do not enclose the room'
        return result
    area = _area(polygon)
    if not (2 <= area <= 100 and 3 <= len(polygon) <= 10):
        result['reason'] = 'polygon area or corner count outside supported single-room range'
        return result
    camera_inside = sum(_inside((x, z), polygon) for x, _, z in camera_positions)/len(camera_positions)
    if camera_inside < .85:
        result['reason'] = 'camera trajectory spans outside the proposed single-room polygon'
        return result
    walls = []
    for start, end in zip(polygon, polygon[1:]+polygon[:1]):
        length = math.dist(start, end)
        if length < .45:
            result['reason'] = 'short unsupported polygon side'
            return result
        middle = ((start[0]+end[0])/2, (start[1]+end[1])/2)
        wall = min(oriented, key=lambda item:
                   abs(sum(n*p for n, p in zip(item['outward_normal'], middle))-
                       item['outward_offset_m']))
        residual = abs(sum(n*p for n, p in zip(wall['outward_normal'], middle))-
                       wall['outward_offset_m'])
        tx, tz = -wall['outward_normal'][1], wall['outward_normal'][0]
        side_range = sorted([tx*start[0]+tz*start[1], tx*end[0]+tz*end[1]])
        overlap = max(0, min(side_range[1], wall['lateral_range_m'][1])-
                      max(side_range[0], wall['lateral_range_m'][0]))/length
        if residual > .12 or overlap < .55:
            result['reason'] = 'one polygon edge lacks sufficient repeated wall support'
            return result
        walls.append({'frame_ids': wall['frame_ids'], 'samples': wall['samples'],
                      'edge_support_fraction': round(overlap, 3),
                      'plane_residual_m': round(residual, 3),
                      'point_to_plane_residual_p90_m': wall['point_to_plane_residual_p90_m']})
    result.update({'status': 'inferred', 'reason': None,
                   'boundary_xz_m': [[round(x, 4), round(z, 4)] for x, z in polygon],
                   'walls_ordered': walls, 'area_m2': round(area, 4),
                   'ceiling_height_m': round(ceiling_y-floor_y, 4),
                   'camera_inside_fraction': round(camera_inside, 3)})
    return result
