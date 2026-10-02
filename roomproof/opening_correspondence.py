"""Evidence-only links between model opening regions on matched views."""

from collections import defaultdict


def _view_box(candidate, tier, view_size, scan_rotation):
    geometry = candidate['geometry']
    if geometry['type'] != 'box':
        return None
    width, height = view_size
    x0, y0, x1, y1 = geometry['xyxy_px']
    gx, gy = geometry['image_width'], geometry['image_height']
    corners = [(x0*width/gx, y0*height/gy), (x1*width/gx, y1*height/gy)]
    if tier == 'scan_rgb' and scan_rotation:
        # Candidate boxes are in the original scan RGB orientation; feature
        # matching operates on a clockwise-rotated view.
        raw_width, raw_height = (height, width) if scan_rotation in (90, 270) else (width, height)
        corners = [(x0*raw_width/gx, y0*raw_height/gy),
                   (x1*raw_width/gx, y1*raw_height/gy)]
        if scan_rotation == 90:
            corners = [(raw_height-1-y, x) for x, y in corners]
        elif scan_rotation == 180:
            corners = [(raw_width-1-x, raw_height-1-y) for x, y in corners]
        else:
            corners = [(y, raw_width-1-x) for x, y in corners]
    xs, ys = [x for x, _ in corners], [y for _, y in corners]
    box = (min(xs), min(ys), max(xs), max(ys))
    if (box[2]-box[0])*(box[3]-box[1]) >= .35*width*height:
        return None
    return box


def _compatible(a, b):
    structural = {'door', 'doorway', 'open_passage'}
    return a == b or (a in structural and b in structural)


def _inside(point, box):
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def match_opening_regions(records, scan_rotation):
    """Require matching local keypoints inside both candidate boxes.

    This establishes only an image-region identity hypothesis. A detector
    box may include furniture or an adjacent surface, so no room connection
    or metric width is inferred from it.
    """
    links = []
    for pair in records:
        if not pair['overlap_supported'] or not pair.get('inlier_coordinates'):
            continue
        left = [(candidate, _view_box(candidate, pair['left_tier'],
                                      pair['left_image_size'], scan_rotation))
                for candidate in pair['left_opening_proposals']]
        right = [(candidate, _view_box(candidate, pair['right_tier'],
                                       pair['right_image_size'], scan_rotation))
                 for candidate in pair['right_opening_proposals']]
        left_masks = [(a, [_inside(item['left_xy'], box_a)
                           for item in pair['inlier_coordinates']])
                      for a, box_a in left if box_a is not None]
        right_masks = [(b, [_inside(item['right_xy'], box_b)
                            for item in pair['inlier_coordinates']])
                       for b, box_b in right if box_b is not None]
        options = []
        for a, mask_a in left_masks:
            left_count = sum(mask_a)
            if left_count < 5:
                continue
            for b, mask_b in right_masks:
                if not _compatible(a['class'], b['class']):
                    continue
                right_count = sum(mask_b)
                joint = sum(x and y for x, y in zip(mask_a, mask_b))
                union = left_count + right_count - joint
                purity = joint/union if union else 0
                if joint >= 5 and purity >= .5:
                    options.append((joint*purity, joint, purity, a, b))
        best_left, best_right = {}, {}
        for option in options:
            score, _, _, a, b = option
            if score > best_left.get(a['candidate_id'], (0,))[0]:
                best_left[a['candidate_id']] = option
            if score > best_right.get(b['candidate_id'], (0,))[0]:
                best_right[b['candidate_id']] = option
        for score, count, purity, a, b in options:
            if (best_left[a['candidate_id']][4]['candidate_id'] != b['candidate_id'] or
                    best_right[b['candidate_id']][3]['candidate_id'] != a['candidate_id']):
                continue
            links.append({
                'left_candidate_id': a['candidate_id'],
                'right_candidate_id': b['candidate_id'],
                'left_source_ref': pair['left_source_ref'],
                'right_source_ref': pair['right_source_ref'],
                'classes': [a['class'], b['class']],
                'matched_region_keypoints': count,
                'matched_region_jaccard': round(purity, 3),
                'image_pair_inliers': pair['inliers'],
                'status': 'image_region_correspondence_hypothesis'})
    links.sort(key=lambda item: (-item['matched_region_keypoints'],
                                 item['left_candidate_id'], item['right_candidate_id']))
    graph = defaultdict(set)
    for item in links:
        a, b = item['left_candidate_id'], item['right_candidate_id']
        graph[a].add(b); graph[b].add(a)
    groups = []
    visited = set()
    for start in sorted(graph):
        if start in visited:
            continue
        pending = [start]
        group = set()
        while pending:
            node = pending.pop()
            if node in group:
                continue
            group.add(node)
            pending.extend(graph[node]-group)
        visited.update(group)
        matching = [item for item in links if item['left_candidate_id'] in group
                    and item['right_candidate_id'] in group]
        groups.append({'candidate_ids': sorted(group),
                       'source_refs': sorted({ref for item in matching
                                              for ref in (item['left_source_ref'],
                                                          item['right_source_ref'])}),
                       'edge_count': len(matching),
                       'status': 'unverified_physical_opening_hypothesis'})
    return {'report_version': '0.1.0', 'status': 'hypotheses_only',
            'method': 'mutual-best compatible model boxes with >=5 shared matched keypoints, >=0.5 matched-point Jaccard, and <35% frame box area; no physical identity assumed',
            'link_count': len(links), 'group_count': len(groups),
            'links': links, 'groups': groups,
            'warnings': ['Region correspondences may be furniture, repeated texture, or overlapping boxes; none establishes a doorway, room adjacency, or width.']}
