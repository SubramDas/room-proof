"""Bounded, auditable Stray depth-to-world conversion and plane candidates.

Coordinates are provisional until checked with a measured target. The exported
point cloud is a diagnostic, not a calibrated room plan.
"""

from collections import Counter
import math
from pathlib import Path

from .cli import sha256, write_json
from .stray_audit import png_info


def rotate(q, p):
    """Apply a unit xyzw quaternion to a 3-vector."""
    x, y, z, w = q
    vx, vy, vz = p
    tx = 2 * (y * vz - z * vy)
    ty = 2 * (z * vx - x * vz)
    tz = 2 * (x * vy - y * vx)
    return (vx + w * tx + y * tz - z * ty,
            vy + w * ty + z * tx - x * tz,
            vz + w * tz + x * ty - y * tx)


def project(u, v, depth_mm, intrinsics, image_size, pose):
    """Project a depth pixel using scaled RGB intrinsics and an ARKit-style axis hypothesis."""
    width, height = image_size
    fx = intrinsics['fx'] * width / 1920
    fy = intrinsics['fy'] * height / 1440
    cx = intrinsics['cx'] * width / 1920
    cy = intrinsics['cy'] * height / 1440
    distance = depth_mm / 1000
    camera = ((u + .5 - cx) * distance / fx,
              -(v + .5 - cy) * distance / fy,
              -distance)
    rotated = rotate(pose['quaternion_xyzw'], camera)
    return tuple(pose['translation_m'][axis] + rotated[axis] for axis in range(3))


def selected_indices(total, maximum):
    count = min(total, maximum)
    if count == 1:
        return [0]
    return sorted({i * (total - 1) // (count - 1) for i in range(count)})


def quality_selected_indices(scan, frames, maximum, candidates_per_window=4, probe_stride=8):
    """Select one high-coverage depth frame from each temporal window.

    Quality uses only raw depth/confidence, never RGB or reference dimensions.
    The first and last windows are kept; no temporal region is discarded.
    """
    total = len(frames)
    windows = min(total, maximum)
    if total <= maximum:
        return list(range(total)), []
    chosen, probes = [], []
    for window in range(windows):
        start = window * total // windows
        stop = (window + 1) * total // windows
        count = min(candidates_per_window, stop - start)
        indices = sorted({start + j * (stop - start - 1) // max(1, count - 1) for j in range(count)})
        options = []
        for frame_number in indices:
            frame_id = frames[frame_number]['frame_id']
            depth = png_info(scan / 'depth' / f'{frame_id}.png', decode=True, pixels=True)
            confidence = png_info(scan / 'confidence' / f'{frame_id}.png', decode=True, pixels=True)
            if (depth['width'], depth['height']) != (confidence['width'], confidence['height']):
                raise ValueError(f'frame {frame_id}: depth/confidence dimensions differ')
            width, height = depth['width'], depth['height']
            dvals, cvals = depth['pixels'], confidence['pixels']
            valid = sum(250 <= dvals[v*width+u] <= 6000 and cvals[v*width+u] >= 1
                        for v in range(1, height-1, probe_stride)
                        for u in range(1, width-1, probe_stride))
            options.append({'frame_index': frame_number, 'valid_probe_pixels': valid})
        selected = max(options, key=lambda item: (item['valid_probe_pixels'], -item['frame_index']))
        chosen.append(selected['frame_index'])
        probes.append({'window_index': window, 'window_frame_range': [start, stop-1],
                       'candidates': options, 'selected_frame_index': selected['frame_index']})
    return chosen, probes


def _horizontal_bins(observations, bin_width=.05, minimum_count=30):
    bins = Counter(round(height / bin_width) for height, _, _ in observations)
    frames = {}
    signs = Counter()
    for height, normal_sign, frame_id in observations:
        key = round(height / bin_width)
        frames.setdefault(key, set()).add(frame_id)
        signs[(key, normal_sign)] += 1
    return [{'center_m': round(key * bin_width, 3), 'samples': count,
             'supporting_frames': len(frames[key]),
             'frame_ids': sorted(frames[key]),
             'positive_normal_samples': signs[(key, 1)],
             'negative_normal_samples': signs[(key, -1)]}
            for key, count in sorted(bins.items(), key=lambda item: item[0])
            if count >= minimum_count]


def _vertical_bins(observations, angle_step_degrees=5, distance_step=.1):
    groups = {}
    for x, y, z, nx, nz, frame_id in observations:
        angle = math.atan2(nz, nx)
        if angle < 0:
            angle += math.pi
            nx, nz = -nx, -nz
        if angle >= math.pi:
            angle -= math.pi
            nx, nz = -nx, -nz
        angle_bin = round(math.degrees(angle) / angle_step_degrees)
        distance_bin = round((nx*x + nz*z) / distance_step)
        group = groups.setdefault((angle_bin, distance_bin), {'count': 0, 'frames': set(), 'y_min': y, 'y_max': y})
        group['count'] += 1
        group['frames'].add(frame_id)
        group['y_min'] = min(group['y_min'], y)
        group['y_max'] = max(group['y_max'], y)
    candidates = []
    for (angle_bin, distance_bin), group in groups.items():
        if group['count'] < 20 or len(group['frames']) < 2:
            continue
        candidates.append({'normal_angle_degrees': angle_bin * angle_step_degrees,
                           'signed_distance_m': round(distance_bin * distance_step, 3),
                           'samples': group['count'], 'supporting_frames': len(group['frames']),
                           'frame_ids': sorted(group['frames']),
                           'vertical_span_m': round(group['y_max']-group['y_min'], 3)})
    return sorted(candidates, key=lambda item: (-item['supporting_frames'], -item['samples']))[:40]


def extract_geometry(scan, index, run_dir, max_frames=32, pixel_stride=4, minimum_confidence=1):
    """Write a bounded world-point PLY and candidate horizontal plane heights."""
    scan = Path(scan)
    chosen, selection_probes = quality_selected_indices(scan, index['frames'], max_frames)
    points = []
    horizontal = []
    vertical = []
    confidence_counts = Counter()
    rejection = Counter()
    frame_records = []
    pose_positions = [frame['pose']['translation_m'] for frame in index['frames']]
    pose_jumps = [math.dist(a, b) for a, b in zip(pose_positions, pose_positions[1:])]
    jump_indices = [i+1 for i, jump in enumerate(pose_jumps) if jump > .10]
    for frame_number in chosen:
        frame = index['frames'][frame_number]
        frame_id = frame['frame_id']
        depth = png_info(scan / 'depth' / f'{frame_id}.png', decode=True, pixels=True)
        confidence = png_info(scan / 'confidence' / f'{frame_id}.png', decode=True, pixels=True)
        width, height = depth['width'], depth['height']
        if (confidence['width'], confidence['height']) != (width, height):
            raise ValueError(f'frame {frame_id}: depth/confidence dimensions differ')
        dvals, cvals = depth['pixels'], confidence['pixels']
        pose = frame['pose']
        intrinsics = pose['intrinsics_px']
        if any(not math.isfinite(intrinsics[key]) or intrinsics[key] <= 0 for key in ('fx', 'fy')):
            raise ValueError(f'frame {frame_id}: invalid intrinsics')
        accepted = 0
        for v in range(1, height-1, pixel_stride):
            for u in range(1, width-1, pixel_stride):
                at = v*width+u
                d, c = dvals[at], cvals[at]
                confidence_counts[c] += 1
                if d < 250 or d > 6000:
                    rejection['depth_out_of_range'] += 1; continue
                if c < minimum_confidence:
                    rejection['low_confidence'] += 1; continue
                # Large local jumps are commonly occlusion edges or stray returns.
                neighbors = (dvals[at-1], dvals[at+1], dvals[at-width], dvals[at+width])
                if any(other == 0 or abs(other-d) > max(250, .18*d) for other in neighbors):
                    rejection['depth_discontinuity'] += 1; continue
                world = project(u, v, d, intrinsics, (width, height), pose)
                points.append((world, frame_id, c))
                accepted += 1
                # A local depth normal identifies approximately horizontal patches.
                right = project(u+1, v, dvals[at+1], intrinsics, (width, height), pose)
                down = project(u, v+1, dvals[at+width], intrinsics, (width, height), pose)
                a = tuple(right[j]-world[j] for j in range(3))
                b = tuple(down[j]-world[j] for j in range(3))
                nx = a[1]*b[2]-a[2]*b[1]
                ny = a[2]*b[0]-a[0]*b[2]
                nz = a[0]*b[1]-a[1]*b[0]
                norm = math.sqrt(nx*nx+ny*ny+nz*nz)
                if norm > 1e-8 and abs(ny)/norm > .9:
                    horizontal.append((world[1], 1 if ny > 0 else -1, frame_id))
                elif norm > 1e-8 and abs(ny)/norm < .25:
                    horizontal_norm = math.hypot(nx, nz)
                    if horizontal_norm > 1e-8:
                        vertical.append((world[0], world[1], world[2], nx/horizontal_norm,
                                         nz/horizontal_norm, frame_id))
        frame_records.append({'frame_id': frame_id, 'accepted_points': accepted,
                              'depth_source_ref': frame['depth']['source_ref'],
                              'pose_source_ref': frame['pose_source_ref']})
    if not points:
        raise ValueError('no usable depth points at the selected confidence/depth thresholds')
    ply = run_dir / 'lidar_points.ply'
    with ply.open('w', encoding='ascii') as stream:
        stream.write(f'ply\nformat ascii 1.0\nelement vertex {len(points)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
        for point, _, _ in points:
            stream.write(f'{point[0]:.5f} {point[1]:.5f} {point[2]:.5f}\n')
    xs = [point[0][0] for point in points]
    ys = [point[0][1] for point in points]
    zs = [point[0][2] for point in points]
    report = {
        'report_version': '0.1.0', 'status': 'provisional_coordinates_unvalidated_scale',
        'source': 'Stray depth/confidence/odometry by frame ID; RGB pairing unused',
        'assumptions': [
            'Depth PNG values are millimetres per Stray format; no tape validation yet.',
            'Per-frame intrinsics are scaled from 1920x1440 RGB pixels to 256x192 depth pixels; depth/RGB registration is unverified.',
            'Camera local x right, y up, z backward; exported xyzw quaternion is treated as camera-to-world.',
            'No lens-distortion correction or RGB alignment is applied.',
            'Confidence code >= 1 is used because Stray documents 0/1/2 with higher meaning more confidence.'
        ],
        'selection': {'total_frames': len(index['frames']), 'selected_frame_indices': chosen,
                      'rule': 'one best valid-depth/confidence frame per evenly spaced temporal window; up to four evenly spaced candidates per window; ties choose earlier frame',
                      'probe_pixel_stride': 8, 'quality_probes': selection_probes,
                      'pixel_stride': pixel_stride, 'min_confidence_code': minimum_confidence,
                      'depth_range_m': [.25, 6.0]},
        'point_count': len(points), 'horizontal_candidate_count': len(horizontal),
        'vertical_candidate_count': len(vertical),
        'confidence_counts_sampled': {str(k): v for k,v in sorted(confidence_counts.items())},
        'rejected_sample_counts': dict(rejection),
        'tracking_jump_frame_indices': jump_indices,
        'largest_pose_step_m': max(pose_jumps, default=0),
        'coordinate_extent_m': {'x': [min(xs), max(xs)], 'y': [min(ys), max(ys)], 'z': [min(zs), max(zs)]},
        'horizontal_y_peaks': sorted(_horizontal_bins(horizontal), key=lambda item: -item['samples'])[:8],
        'horizontal_surface_bins': _horizontal_bins(horizontal),
        'vertical_plane_candidates': _vertical_bins(vertical),
        'frames': frame_records,
        'warnings': ['Candidate plane heights are not a calibrated floor/ceiling estimate.',
                     'Glass, mirrors, wet surfaces, low light, and unobserved ceiling cannot yet be diagnosed from this extraction.']
    }
    if jump_indices:
        report['warnings'].append(f'{len(jump_indices)} pose steps exceed 0.10 m between consecutive frames; inspect tracking before using geometry')
    weak_frames = [item['frame_id'] for item in frame_records if item['accepted_points'] < 500]
    if weak_frames:
        report['warnings'].append(f'{len(weak_frames)} sampled depth frames have fewer than 500 retained points')
    report_path = run_dir / 'lidar_geometry.json'
    write_json(report_path, report)
    return report, [{'path': str(path), 'sha256': sha256(path)} for path in (ply, report_path)]
