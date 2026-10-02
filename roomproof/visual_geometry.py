"""Bounded CPU visual evidence from ordinary RGB frames and stills.

Reports image-space overlap and motion only. No metric or 3D camera pose is claimed.
"""

import math
import hashlib
from pathlib import Path
import statistics

import imageio_ffmpeg

from .cli import sha256, write_json


def thumbnail(rgb, width, height, target_width=160):
    if len(rgb) != width * height * 3:
        raise ValueError('RGB byte count disagrees with frame dimensions')
    step = max(1, width // target_width)
    xs = list(range(step//2, width, step))
    ys = list(range(step//2, height, step))
    gray = bytearray(len(xs) * len(ys))
    for j, y in enumerate(ys):
        row = y * width * 3
        for i, x in enumerate(xs):
            at = row + x * 3
            gray[j*len(xs)+i] = (77*rgb[at] + 150*rgb[at+1] + 29*rgb[at+2]) >> 8
    return gray, len(xs), len(ys)


def features(gray, width, height, limit=120):
    """Select gradient intersections with spatial suppression; describe local contrast."""
    candidates = []
    gradients = []
    for y in range(4, height-4, 2):
        for x in range(4, width-4, 2):
            at = y*width+x
            gx = abs(gray[at+1]-gray[at-1])
            gy = abs(gray[at+width]-gray[at-width])
            gradients.append(gx+gy)
            score = min(gx, gy) + (gx*gy)//32
            if score >= 12:
                candidates.append((score, x, y))
    candidates.sort(reverse=True)
    chosen = []
    for score, x, y in candidates:
        if any(abs(x-px)<7 and abs(y-py)<7 for px,py,_ in chosen):
            continue
        values = [gray[(y+dy)*width+x+dx] for dy in (-3,-2,-1,0,1,2,3) for dx in (-3,-2,-1,0,1,2,3)]
        mean = sum(values)/len(values)
        centered = tuple(value-mean for value in values)
        norm = math.sqrt(sum(value*value for value in centered))
        if norm < 35:
            continue
        chosen.append((x, y, tuple(value/norm for value in centered)))
        if len(chosen) >= limit:
            break
    quality = {'corner_count': len(chosen), 'mean_gradient': round(statistics.mean(gradients), 2) if gradients else 0,
               'mean_luma': round(statistics.mean(gray), 2) if gray else 0}
    return chosen, quality


def line_evidence(gray, width, height):
    """Find long axis-aligned contrast ridges as wall/opening cues."""
    vertical = []
    horizontal = []
    for x in range(3, width-3):
        scores = [abs(gray[y*width+x+1]-gray[y*width+x-1])
                  for y in range(height//10, 9*height//10, 2)]
        vertical.append(sum(value >= 22 for value in scores) / max(1, len(scores)))
    for y in range(3, height-3):
        scores = [abs(gray[(y+1)*width+x]-gray[(y-1)*width+x])
                  for x in range(width//10, 9*width//10, 2)]
        horizontal.append(sum(value >= 22 for value in scores) / max(1, len(scores)))
    def peaks(values, offset, extent):
        found = []
        for i in sorted(range(len(values)), key=lambda at: values[at], reverse=True):
            if values[i] < .16:
                break
            position = i+offset
            if all(abs(position-item['pixel']) >= 7 for item in found):
                found.append({'pixel': position, 'fraction': round(position/extent, 3),
                              'edge_support': round(values[i], 3)})
            if len(found) == 8:
                break
        return sorted(found, key=lambda item: item['pixel'])
    return {'vertical': peaks(vertical, 3, width), 'horizontal': peaks(horizontal, 3, height),
            'interpretation': 'long contrast ridges; may be wall edges, door/window frames, furniture, or curtains'}


def match(first, second):
    if len(first) < 2 or len(second) < 2:
        return []
    forward = {}
    backward = {}
    for left, right, result in ((first, second, forward), (second, first, backward)):
        for i, (_, _, descriptor) in enumerate(left):
            similarities = sorted(((sum(a*b for a,b in zip(descriptor, other[2])), j) for j,other in enumerate(right)), reverse=True)
            if len(similarities) >= 2 and similarities[0][0] >= .68 and similarities[0][0]-similarities[1][0] >= .02:
                result[i] = similarities[0][1]
    return [(i,j) for i,j in forward.items() if backward.get(j) == i]


def compare(first, second):
    a, b = first['features'], second['features']
    matches = match(a,b)
    if not matches:
        return {'matches': 0, 'inliers': 0, 'inlier_fraction': 0, 'overlap_supported': False,
                'apparent_shift_px': None}
    shifts = [(b[j][0]-a[i][0], b[j][1]-a[i][1]) for i,j in matches]
    dx = statistics.median(item[0] for item in shifts)
    dy = statistics.median(item[1] for item in shifts)
    inliers = sum(abs(x-dx)<=8 and abs(y-dy)<=8 for x,y in shifts)
    model = 'translation'
    # A second camera position can rotate and scale a shared view. Fit a
    # two-point similarity model with a bounded, deterministic hypothesis set.
    for k in range(min(len(matches), 24)):
        for m in range(k+1, min(len(matches), 24)):
            p1 = a[matches[k][0]]; p2 = a[matches[m][0]]
            q1 = b[matches[k][1]]; q2 = b[matches[m][1]]
            px, py = p2[0]-p1[0], p2[1]-p1[1]
            qx, qy = q2[0]-q1[0], q2[1]-q1[1]
            denominator = px*px+py*py
            if denominator < 100:
                continue
            alpha = (px*qx+py*qy)/denominator
            beta = (px*qy-py*qx)/denominator
            scale = math.hypot(alpha,beta)
            if not .5 <= scale <= 2.0:
                continue
            tx = q1[0]-alpha*p1[0]+beta*p1[1]
            ty = q1[1]-beta*p1[0]-alpha*p1[1]
            count = sum(math.hypot(alpha*a[i][0]-beta*a[i][1]+tx-b[j][0],
                                   beta*a[i][0]+alpha*a[i][1]+ty-b[j][1]) <= 5
                        for i,j in matches)
            if count > inliers:
                inliers = count
                model = 'similarity'
                dx, dy = tx, ty
    fraction = inliers / len(matches)
    supported = len(matches) >= 8 and inliers >= 8 and fraction >= .4
    return {'matches': len(matches), 'inliers': inliers, 'inlier_fraction': round(fraction, 3),
            'overlap_supported': supported,
            'motion_model': model,
            'apparent_shift_px': [round(dx, 2), round(dy, 2)] if supported else None}


def _analyze_rgb(rgb, width, height, frame):
    gray, thumb_width, thumb_height = thumbnail(rgb, width, height)
    found, quality = features(gray, thumb_width, thumb_height)
    return {'frame_id': frame['frame_id'], 'source_ref': frame['source_ref'],
            'sampling_group': frame.get('sampling_group'),
            'features': found, 'quality': quality,
            'line_evidence': line_evidence(gray, thumb_width, thumb_height),
            'thumbnail_size': [thumb_width, thumb_height]}


def _strip(frame):
    return {key: value for key,value in frame.items() if key != 'features'}


def coarse_scene_profile(video_path, maximum=180):
    """One-frame-per-second appearance changes; not semantic room detection."""
    stream = imageio_ffmpeg.read_frames(str(video_path), pix_fmt='rgb24',
                                        output_params=['-vf', 'fps=1,scale=160:-2', '-vsync', '0'])
    next(stream, None)
    signatures = []
    for rgb in stream:
        width = 160
        if len(rgb) % (width*3):
            raise ValueError('coarse video frame has unexpected RGB byte count')
        height = len(rgb)//(width*3)
        cells = [[0,0,0,0] for _ in range(16)]
        for y in range(0,height,4):
            for x in range(0,width,4):
                cell = min(3, 4*y//height)*4 + min(3, 4*x//width)
                at = (y*width+x)*3
                cells[cell][0] += rgb[at]
                cells[cell][1] += rgb[at+1]
                cells[cell][2] += rgb[at+2]
                cells[cell][3] += 1
        signatures.append([channel/count for red,green,blue,count in cells
                           for channel in (red,green,blue)])
        if len(signatures) >= maximum:
            break
    differences = [sum(abs(a-b) for a,b in zip(first,second))/len(first)
                   for first,second in zip(signatures,signatures[1:])]
    threshold = max(28.0, sorted(differences)[int(.85*(len(differences)-1))]*1.2) if differences else None
    candidates = []
    for second, score in enumerate(differences, start=1):
        if score >= threshold and (not candidates or second-candidates[-1]['second_index'] >= 5):
            candidates.append({'second_index': second, 'timestamp_estimate_seconds': second,
                               'appearance_change_score': round(score,2)})
    return {'sample_rate_hz': 1, 'sample_count': len(signatures),
            'threshold': round(threshold,2) if threshold is not None else None,
            'scene_change_candidates': candidates,
            'interpretation': 'appearance changes may reflect a turn, lighting, occlusion, or a room transition'}


def analyze_video(index, run_dir, video_path=None):
    analyzed = []
    for frame in index['frames']:
        path = run_dir / 'frames' / frame['sampled_path']
        analyzed.append(_analyze_rgb(path.read_bytes(), frame['width'], frame['height'], frame))
    links = []
    gaps = []
    sampling_gaps = []
    for i, (first, second) in enumerate(zip(analyzed, analyzed[1:])):
        if index['frames'][i].get('sampling_group') != index['frames'][i+1].get('sampling_group'):
            sampling_gaps.append(i+1)
            continue
        result = compare(first, second)
        result.update({'from_frame_id': first['frame_id'], 'to_frame_id': second['frame_id'],
                       'from_source_ref': first['source_ref'], 'to_source_ref': second['source_ref']})
        links.append(result)
        if not result['overlap_supported']:
            gaps.append(i+1)
    warnings = ['Image motion is in thumbnail pixels; no camera pose, depth, or metric scale is recovered.']
    poor = [item['frame_id'] for item in analyzed if item['quality']['corner_count'] < 8 or item['quality']['mean_luma'] < 35]
    if poor:
        warnings.append(f'{len(poor)} sampled frames are dark or have too few usable corners')
    if gaps:
        warnings.append(f'{len(gaps)} of {len(links)} sampled frame transitions lack supported feature overlap')
    if len(analyzed) < 2:
        warnings.append('At least two sampled frames are needed for visual motion evidence')
    report = {'report_version': '0.1.0', 'tier': 'video', 'method': 'grayscale gradient corners, normalized 7x7 patch descriptors, mutual ratio matching, bounded translation/similarity consensus',
              'frame_count': len(analyzed), 'frames': [_strip(item) for item in analyzed],
              'transitions': links, 'tracking_gap_after_sample_indices': gaps,
              'sampling_gap_after_sample_indices': sampling_gaps,
              'supported_transition_count': sum(item['overlap_supported'] for item in links),
              'room_transition_hypotheses': [], 'metric_scale_status': 'unidentifiable',
              'warnings': warnings}
    if video_path is not None:
        report['coarse_scene_profile'] = coarse_scene_profile(video_path)
        if report['coarse_scene_profile']['scene_change_candidates']:
            report['warnings'].append('Coarse video appearance changes are candidates only; none is verified as a doorway or room transition')
    path = run_dir / 'visual_geometry.json'
    write_json(path, report)
    return report, [{'path': str(path), 'sha256': sha256(path)}]


def _photo_rgb(path):
    frames = imageio_ffmpeg.read_frames(str(path), pix_fmt='rgb24', output_params=['-vf', 'scale=320:-2', '-vsync', '0'])
    next(frames, None)
    rgb = next(frames, None)
    if rgb is None or len(rgb) % (320*3):
        raise ValueError(f'photo could not be decoded at 320 pixels wide: {path}')
    return rgb, 320, len(rgb)//(320*3)


def analyze_photos(root, index, run_dir):
    analyzed = []
    for frame in index['frames']:
        rgb, width, height = _photo_rgb(Path(root)/frame['source_path'])
        item = _analyze_rgb(rgb, width, height, frame)
        item['room_id'] = frame['room_id']
        analyzed.append(item)
    pairs = []
    room_stats = {room_id: {'frame_count': 0, 'supported_overlap_pairs': 0} for room_id in index['room_ids']}
    for item in analyzed:
        room_stats[item['room_id']]['frame_count'] += 1
    candidates = [(i, j) for i in range(len(analyzed)) for j in range(i+1, len(analyzed))]
    candidates.sort(key=lambda pair: (analyzed[pair[0]]['room_id'] != analyzed[pair[1]]['room_id'],
                                      hashlib.sha256((analyzed[pair[0]]['frame_id'] + analyzed[pair[1]]['frame_id']).encode()).digest()))
    selected = candidates[:256]
    for i, j in selected:
        first, second = analyzed[i], analyzed[j]
        result = compare(first, second)
        result.update({'first_frame_id': first['frame_id'], 'second_frame_id': second['frame_id'],
                       'first_room_id': first['room_id'], 'second_room_id': second['room_id']})
        pairs.append(result)
        if result['overlap_supported'] and first['room_id'] == second['room_id']:
            room_stats[first['room_id']]['supported_overlap_pairs'] += 1
    poor = [item['frame_id'] for item in analyzed if item['quality']['corner_count'] < 8 or item['quality']['mean_luma'] < 35]
    warnings = ['Feature overlap alone does not establish a shared doorway, room placement, or metric scale.',
                'Wall, corner, opening, and full-room coverage inference is pending.']
    if poor:
        warnings.append(f'{len(poor)} stills are dark or have too few usable corners')
    report = {'report_version': '0.1.0', 'tier': 'photo',
              'method': 'grayscale gradient corners, normalized 7x7 patch descriptors, mutual ratio matching, bounded translation/similarity consensus',
              'frames': [_strip(item) for item in analyzed], 'pairs': pairs, 'rooms': room_stats,
              'pair_selection': {'candidate_count': len(candidates), 'evaluated_count': len(selected),
                                 'rule': 'within-room first; SHA-256 order; maximum 256 pairs'},
              'adjacency_hypotheses': [], 'metric_scale_status': 'unidentifiable',
              'warnings': warnings}
    path = run_dir / 'visual_geometry.json'
    write_json(path, report)
    return report, [{'path': str(path), 'sha256': sha256(path)}]
