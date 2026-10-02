"""Rigid 2D placement from verified, measured shared openings.

Supplied room labels or image overlap cannot make a connection verified. The
caller must provide accepted physical opening correspondences with metric
widths and offsets. Unplaced metric rooms remain in their capture-local frame.
"""

import math


def _signed_area(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(poly, poly[1:]+poly[:1]))/2


def _opening(room, opening_id):
    opening = next((item for item in room['openings'] if item['id'] == opening_id), None)
    if opening is None or opening['status'] != 'inferred':
        return None
    width = opening['width']['value']
    offset = opening['offset_along_wall']['value']
    surface = next((item for item in room['surfaces']
                    if item['id'] == opening['surface_id'] and item['kind'] == 'wall'), None)
    if width is None or offset is None or surface is None or room['boundary'] is None:
        return None
    start, end = surface['line']
    length = math.dist(start, end)
    if length <= 0 or offset < 0 or width <= 0 or offset+width > length+.03:
        return None
    tangent = ((end[0]-start[0])/length, (end[1]-start[1])/length)
    midpoint = (start[0]+tangent[0]*(offset+width/2),
                start[1]+tangent[1]*(offset+width/2))
    sign = 1 if _signed_area(room['boundary']) > 0 else -1
    outward = (sign*tangent[1], -sign*tangent[0])
    return {'center': midpoint, 'outward': outward, 'width_m': width}


def _transform(point, rotation, translation):
    cosine, sine = math.cos(rotation), math.sin(rotation)
    return [cosine*point[0]-sine*point[1]+translation[0],
            sine*point[0]+cosine*point[1]+translation[1]]


def _convex_overlap_area(first, second):
    """Convex polygon intersection; shared boundary has zero area."""
    poly = [tuple(point) for point in first]
    orientation = 1 if _signed_area(second) > 0 else -1
    for a, b in zip(second, second[1:]+second[:1]):
        next_poly = []
        for p, q in zip(poly, poly[1:]+poly[:1]):
            vp = orientation*((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
            vq = orientation*((b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]))
            if vp >= 0:
                next_poly.append(p)
            if (vp < 0 < vq) or (vq < 0 < vp):
                fraction = vp/(vp-vq)
                next_poly.append((p[0]+fraction*(q[0]-p[0]),
                                  p[1]+fraction*(q[1]-p[1])))
        poly = next_poly
        if len(poly) < 3:
            return 0.0
    return abs(_signed_area(poly)) if len(poly) >= 3 else 0.0


def _triangles(poly):
    """Ear-clip a simple polygon so the overlap check also handles concavity."""
    vertices = [tuple(point) for point in poly]
    if _signed_area(vertices) < 0:
        vertices.reverse()
    result = []
    while len(vertices) > 3:
        chosen = None
        for i in range(len(vertices)):
            a, b, c = vertices[i-1], vertices[i], vertices[(i+1)%len(vertices)]
            cross = (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
            if cross <= 1e-9:
                continue
            def inside(p):
                edges = ((a,b),(b,c),(c,a))
                return all((q[0]-r[0])*(p[1]-r[1])-(q[1]-r[1])*(p[0]-r[0]) >= -1e-9
                           for r, q in edges)
            if any(inside(point) for j, point in enumerate(vertices)
                   if j not in ((i-1)%len(vertices), i, (i+1)%len(vertices))):
                continue
            chosen = i
            result.append([a, b, c])
            break
        if chosen is None:
            return []
        vertices.pop(chosen)
    result.append(vertices)
    return result


def _overlap_area(first, second):
    return sum(_convex_overlap_area(a, b)
               for a in _triangles(first) for b in _triangles(second))


def solve_placements(rooms, connections):
    """Return unique nonoverlapping transforms; never guess from labels."""
    by_id = {room['id']: room for room in rooms}
    metric = [room for room in rooms if room['boundary'] is not None]
    if not metric:
        return {'status': 'no_metric_anchor', 'placements': [], 'rejected': [],
                'unplaced_room_ids': sorted(by_id)}
    anchor = metric[0]['id']
    placements = {anchor: {'room_id': anchor, 'rotation_degrees': 0,
                           'translation_m': [0, 0], 'supporting_connection_ids': []}}
    rejected = []
    pending = list(connections)
    while pending:
        proposals = {}
        for connection in pending:
            if connection.get('status') != 'verified_physical_opening':
                continue
            room_a, room_b = connection['room_ids']
            if room_a not in by_id or room_b not in by_id or (room_a in placements) == (room_b in placements):
                continue
            placed_id, new_id = ((room_a, room_b) if room_a in placements else (room_b, room_a))
            placed_opening_id = connection['opening_ids'][0 if placed_id == room_a else 1]
            new_opening_id = connection['opening_ids'][1 if placed_id == room_a else 0]
            placed_opening = _opening(by_id[placed_id], placed_opening_id)
            new_opening = _opening(by_id[new_id], new_opening_id)
            if placed_opening is None or new_opening is None:
                rejected.append({'connection_id': connection['id'],
                                 'reason': 'opening lacks inferred metric wall, width, or offset'})
                continue
            if abs(placed_opening['width_m']-new_opening['width_m']) > .15:
                rejected.append({'connection_id': connection['id'],
                                 'reason': 'measured opening widths disagree by more than 0.15 m'})
                continue
            base = placements[placed_id]
            base_angle = math.radians(base['rotation_degrees'])
            base_center = _transform(placed_opening['center'], base_angle, base['translation_m'])
            base_normal = _transform(placed_opening['outward'], base_angle, (0, 0))
            target_angle = math.atan2(-base_normal[1], -base_normal[0])
            source_angle = math.atan2(new_opening['outward'][1], new_opening['outward'][0])
            rotation = target_angle-source_angle
            rotated_center = _transform(new_opening['center'], rotation, (0, 0))
            translation = [base_center[0]-rotated_center[0], base_center[1]-rotated_center[1]]
            poly = [_transform(point, rotation, translation) for point in by_id[new_id]['boundary']]
            overlap = max((_overlap_area(poly, [_transform(point,
                           math.radians(place['rotation_degrees']), place['translation_m'])
                           for point in by_id[other]['boundary']])
                           for other, place in placements.items()), default=0)
            if overlap > .02:
                rejected.append({'connection_id': connection['id'],
                                 'reason': f'placed room overlaps existing room by {overlap:.3f} m2'})
                continue
            proposals.setdefault(new_id, []).append({
                'room_id': new_id, 'rotation_degrees': round(math.degrees(rotation)%360, 3),
                'translation_m': [round(value, 4) for value in translation],
                'supporting_connection_ids': [connection['id']]})
        newly_placed = {}
        for room_id, options in proposals.items():
            distinct = {(round(option['rotation_degrees'], 1),
                         tuple(round(value, 2) for value in option['translation_m']))
                        for option in options}
            if len(distinct) == 1:
                newly_placed[room_id] = options[0]
            else:
                rejected.append({'room_id': room_id,
                                 'reason': 'multiple incompatible metric placements remain'})
        if not newly_placed:
            break
        placements.update(newly_placed)
        pending = [item for item in pending if not all(room in placements for room in item['room_ids'])]
    conflicts = []
    for connection in connections:
        if connection.get('status') != 'verified_physical_opening':
            continue
        a, b = connection['room_ids']
        if a not in placements or b not in placements:
            continue
        opening_a = _opening(by_id[a], connection['opening_ids'][0])
        opening_b = _opening(by_id[b], connection['opening_ids'][1])
        if opening_a is None or opening_b is None:
            conflicts.append({'connection_id': connection['id'],
                              'reason': 'a verified connection lacks a metric opening'})
            continue
        pose_a, pose_b = placements[a], placements[b]
        center_a = _transform(opening_a['center'], math.radians(pose_a['rotation_degrees']),
                              pose_a['translation_m'])
        center_b = _transform(opening_b['center'], math.radians(pose_b['rotation_degrees']),
                              pose_b['translation_m'])
        normal_a = _transform(opening_a['outward'], math.radians(pose_a['rotation_degrees']), (0,0))
        normal_b = _transform(opening_b['outward'], math.radians(pose_b['rotation_degrees']), (0,0))
        if (math.dist(center_a, center_b) > .15 or
                sum(x*y for x, y in zip(normal_a, normal_b)) > -math.cos(math.radians(10)) or
                abs(opening_a['width_m']-opening_b['width_m']) > .15):
            conflicts.append({'connection_id': connection['id'],
                              'reason': 'measured opening centers, directions, or widths conflict after placement'})
    if conflicts:
        return {'status': 'conflicting_constraints', 'anchor_room_id': anchor,
                'placements': [placements[anchor]],
                'rejected': rejected+conflicts,
                'unplaced_room_ids': sorted(set(by_id)-{anchor}),
                'method': 'verified opening centers and opposite outward normals; conflicting cycles remain unresolved'}
    return {'status': 'metric_placements_proposed' if len(placements) > 1 else 'anchor_only',
            'anchor_room_id': anchor, 'placements': list(placements.values()),
            'rejected': rejected,
            'unplaced_room_ids': sorted(set(by_id)-set(placements)),
            'method': 'verified opening centers and opposite outward normals; width and polygon-overlap gates'}


def apply_verified_placements(plan, report, connections):
    """Move uniquely placed metric rooms and add only accepted adjacency."""
    if report['status'] != 'metric_placements_proposed':
        return plan
    placements = {item['room_id']: item for item in report['placements']}
    for room in plan['rooms']:
        pose = placements.get(room['id'])
        if pose is None or room['id'] == report['anchor_room_id']:
            continue
        rotation = math.radians(pose['rotation_degrees'])
        shift = pose['translation_m']
        room['boundary'] = [[round(value, 4) for value in _transform(point, rotation, shift)]
                            for point in room['boundary']]
        for surface in room['surfaces']:
            if surface['kind'] == 'wall':
                surface['line'] = [[round(value, 4) for value in _transform(point, rotation, shift)]
                                   for point in surface['line']]
    for connection in connections:
        if connection.get('status') != 'verified_physical_opening':
            continue
        a, b = connection['room_ids']
        if a not in placements or b not in placements:
            continue
        plan['adjacency'].append({
            'room_a_id': a, 'room_b_id': b,
            'opening_id': connection['opening_ids'][0],
            'status': 'inferred', 'confidence': None,
            'source_refs': connection.get('source_refs', []),
        })
    if len(placements) > 1:
        # A union of room polygons can be concave; the schema has one outline.
        # Leave the whole-property footprint unknown until union vectorization.
        from .plan import unknown
        plan['plan']['status'] = 'unresolved'
        plan['plan']['footprint'] = None
        plan['plan']['floor_area'] = unknown('m2', plan['capture']['source_refs'])
        plan['warnings'].append('Rooms are placed by verified shared openings; whole-property outer footprint remains unvectorized.')
    return plan
