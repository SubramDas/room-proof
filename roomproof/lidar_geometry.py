"""Bounded, auditable Stray depth-to-world conversion and plane candidates.

Coordinates are provisional until checked with a measured target. The exported
point cloud is a diagnostic, not a calibrated room plan.
"""

from collections import Counter
import math
from pathlib import Path
import statistics

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
    """Project Stray depth through camera-to-world pose using vision camera axes."""
    width, height = image_size
    fx = intrinsics['fx'] * width / 1920
    fy = intrinsics['fy'] * height / 1440
    cx = intrinsics['cx'] * width / 1920
    cy = intrinsics['cy'] * height / 1440
    distance = depth_mm / 1000
    camera = ((u + .5 - cx) * distance / fx,
              (v + .5 - cy) * distance / fy,
              distance)
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


def _pose_revisits(frames, stride=15, min_separation_seconds=20, max_distance_m=.4,
                   max_rotation_degrees=45):
    """Unverified return-to-place candidates from recorded poses only."""
    sampled = frames[::stride]
    candidates = []
    for first_index, first in enumerate(sampled):
        a = first['pose']
        for second in sampled[first_index+1:]:
            b = second['pose']
            separation = b['timestamp_seconds'] - a['timestamp_seconds']
            if separation < min_separation_seconds:
                continue
            distance = math.dist(a['translation_m'], b['translation_m'])
            if distance > max_distance_m:
                continue
            dot = abs(sum(x*y for x, y in zip(a['quaternion_xyzw'], b['quaternion_xyzw'])))
            rotation = math.degrees(2*math.acos(min(1., dot)))
            candidates.append({'first_frame_id': first['frame_id'],
                               'second_frame_id': second['frame_id'],
                               'separation_seconds': round(separation, 2),
                               'pose_distance_m': round(distance, 3),
                               'orientation_difference_degrees': round(rotation, 1),
                               'similar_orientation': rotation <= max_rotation_degrees})
    candidates.sort(key=lambda item: (item['pose_distance_m'], item['orientation_difference_degrees']))
    return {'nearby_pose_pairs': candidates[:20],
            'similar_view_pairs': [item for item in candidates if item['similar_orientation']][:20]}


def _voxel_footprint(points, cell=.10):
    cells = {(math.floor(point[0] / cell), math.floor(point[2] / cell)) for point in points}
    if not cells:
        return {'occupied_cells': 0, 'occupied_area_m2': 0, 'bounds_xz_m': None}
    return {'occupied_cells': len(cells), 'occupied_area_m2': round(len(cells) * cell * cell, 3),
            'bounds_xz_m': [[round(min(x for x, _ in cells) * cell, 3),
                             round((max(x for x, _ in cells) + 1) * cell, 3)],
                            [round(min(z for _, z in cells) * cell, 3),
                             round((max(z for _, z in cells) + 1) * cell, 3)]]}


def _closure_constraint(first, second, cell=.08):
    """Estimate a translation only from same-view, nearby 3D surface samples."""
    if len(first) < 300 or len(second) < 300:
        return None
    grid = {}
    for point in first[::max(1, len(first)//1500)]:
        key = tuple(round(value/cell) for value in point)
        grid.setdefault(key, []).append(point)
    residuals = []
    matched_positions = []
    sampled_second = second[::max(1, len(second)//1500)]
    for point in sampled_second:
        key = tuple(round(value/cell) for value in point)
        nearest = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for other in grid.get((key[0]+dx, key[1]+dy, key[2]+dz), ()):
                        distance = math.dist(point, other)
                        if nearest is None or distance < nearest[0]:
                            nearest = (distance, other)
        if nearest is not None and nearest[0] <= .10:
            residuals.append(tuple(nearest[1][axis]-point[axis] for axis in range(3)))
            matched_positions.append(point)
    overlap = len(residuals) / max(1, len(sampled_second))
    if len(residuals) < 100 or overlap < .20:
        return None
    # A single flat wall can appear to match after sliding along itself.
    if any(max(point[axis] for point in matched_positions) -
           min(point[axis] for point in matched_positions) < .35 for axis in range(3)):
        return None
    translation = tuple(statistics.median(row[axis] for row in residuals) for axis in range(3))
    spread = statistics.median(math.dist(row, translation) for row in residuals)
    magnitude = math.dist((0, 0, 0), translation)
    if spread > .045 or not .02 <= magnitude <= .25:
        return None
    return {'translation_m': [round(value, 5) for value in translation],
            'matched_points': len(residuals), 'overlap_fraction': round(overlap, 3),
            'median_residual_spread_m': round(spread, 4),
            'translation_magnitude_m': round(magnitude, 4)}


def _drift_ablation(frames, frame_points, enabled):
    """One conservative loop translation, distributed along the intervening path."""
    candidates = []
    for first_index, first in enumerate(frames):
        for second_index in range(first_index + 1, len(frames)):
            second = frames[second_index]
            a, b = first['pose'], second['pose']
            if b['timestamp_seconds'] - a['timestamp_seconds'] < 20:
                continue
            pose_distance = math.dist(a['translation_m'], b['translation_m'])
            if pose_distance > .4:
                continue
            dot = abs(sum(x*y for x, y in zip(a['quaternion_xyzw'], b['quaternion_xyzw'])))
            angle = math.degrees(2*math.acos(min(1., dot)))
            if angle > 30:
                continue
            constraint = _closure_constraint(frame_points[first['frame_id']], frame_points[second['frame_id']])
            if constraint is not None:
                candidates.append({'first_frame_id': first['frame_id'], 'second_frame_id': second['frame_id'],
                                   'first_sample_index': first_index, 'second_sample_index': second_index,
                                   'pose_distance_m': round(pose_distance, 4),
                                   'orientation_difference_degrees': round(angle, 2), **constraint})
    candidates.sort(key=lambda item: (-item['matched_points'], item['median_residual_spread_m']))
    chosen = candidates[0] if candidates and enabled else None
    raw = [point for frame in frames for point in frame_points[frame['frame_id']]]
    corrected = []
    for index, frame in enumerate(frames):
        if chosen is None or index <= chosen['first_sample_index']:
            fraction = 0
        else:
            fraction = min(1, (index-chosen['first_sample_index']) /
                           (chosen['second_sample_index']-chosen['first_sample_index']))
        offset = chosen['translation_m'] if chosen else (0, 0, 0)
        corrected.extend(tuple(point[axis] + fraction*offset[axis] for axis in range(3))
                         for point in frame_points[frame['frame_id']])
    return corrected, {'enabled': enabled, 'method': 'single verified same-view 3D translation closure; linear path distribution',
                       'candidate_count': len(candidates), 'verified_candidates': candidates[:10],
                       'applied_constraint': chosen, 'raw_footprint': _voxel_footprint(raw),
                       'corrected_footprint': _voxel_footprint(corrected),
                       'area_change_m2': round(_voxel_footprint(corrected)['occupied_area_m2'] -
                                               _voxel_footprint(raw)['occupied_area_m2'], 3),
                       'footprint_kind': 'occupied sampled depth cells, not a room or property boundary'}


def _rgb_light_audit(scan, rgb_count, maximum=32):
    """Scan-wide light diagnostic; RGB/depth pairing is deliberately not assumed."""
    import imageio_ffmpeg

    stream = imageio_ffmpeg.read_frames(str(scan / 'rgb.mp4'), pix_fmt='rgb24',
                                       output_params=['-vf', 'scale=64:48', '-vsync', '0'])
    header = next(stream)
    selected = set(selected_indices(rgb_count, min(maximum, rgb_count)))
    records = []
    for frame_number, pixels in enumerate(stream):
        if frame_number not in selected:
            continue
        if len(pixels) != 64*48*3:
            raise ValueError(f'RGB light sample {frame_number}: unexpected decoded size')
        luminance = [(54*pixels[at] + 183*pixels[at+1] + 19*pixels[at+2]) // 256
                     for at in range(0, len(pixels), 3)]
        median = statistics.median(luminance)
        dark_fraction = sum(value < 32 for value in luminance) / len(luminance)
        records.append({'rgb_frame_index': frame_number, 'median_luma_0_255': median,
                        'dark_pixel_fraction': round(dark_fraction, 3),
                        'low_light_heuristic': median < 40})
    return {'method': '64x48 grayscale frame median below 40/255; uncalibrated scene-light heuristic',
            'rgb_depth_pairing': 'unresolved; these are scan-wide RGB frame indices only',
            'sampled_frames': records,
            'low_light_frame_count': sum(item['low_light_heuristic'] for item in records)}


def extract_geometry(scan, index, run_dir, max_frames=32, pixel_stride=4, minimum_confidence=1,
                     drift_correction=True, single_room=False):
    """Write a bounded world-point PLY and candidate horizontal plane heights."""
    scan = Path(scan)
    revisit_candidates = _pose_revisits(index['frames'])
    # Temporal quality windows can miss a short revisit. Reserve a few slots
    # for pose-near, similarly oriented frame pairs; 3D still has to verify them.
    anchor_ids = []
    anchor_limit = min(6, max_frames // 4) if max_frames >= 12 else 0
    for pair in revisit_candidates['similar_view_pairs'][:8]:
        for key in ('first_frame_id', 'second_frame_id'):
            frame_id = pair[key]
            if frame_id not in anchor_ids and len(anchor_ids) < anchor_limit:
                anchor_ids.append(frame_id)
    frame_index_by_id = {frame['frame_id']: number for number, frame in enumerate(index['frames'])}
    quality_chosen, selection_probes = quality_selected_indices(
        scan, index['frames'], max_frames - len(anchor_ids))
    chosen = sorted(set(quality_chosen) | {frame_index_by_id[frame_id] for frame_id in anchor_ids})
    points = []
    horizontal = []
    vertical = []
    confidence_counts = Counter()
    rejection = Counter()
    frame_records = []
    frame_points = {}
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
        frame_points[frame_id] = []
        frame_rejection = Counter()
        for v in range(1, height-1, pixel_stride):
            for u in range(1, width-1, pixel_stride):
                at = v*width+u
                d, c = dvals[at], cvals[at]
                confidence_counts[c] += 1
                if d < 250 or d > 6000:
                    rejection['depth_out_of_range'] += 1; frame_rejection['depth_out_of_range'] += 1; continue
                if c < minimum_confidence:
                    rejection['low_confidence'] += 1; frame_rejection['low_confidence'] += 1; continue
                # Large local jumps are commonly occlusion edges or stray returns.
                neighbors = (dvals[at-1], dvals[at+1], dvals[at-width], dvals[at+width])
                if any(other == 0 or abs(other-d) > max(250, .18*d) for other in neighbors):
                    rejection['depth_discontinuity'] += 1; frame_rejection['depth_discontinuity'] += 1; continue
                world = project(u, v, d, intrinsics, (width, height), pose)
                points.append((world, frame_id, c))
                frame_points[frame_id].append(world)
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
                              'sampled_pixels': accepted + sum(frame_rejection.values()),
                              'rejected_sample_counts': dict(frame_rejection),
                              'depth_source_ref': frame['depth']['source_ref'],
                              'pose_source_ref': frame['pose_source_ref']})
    if not points:
        raise ValueError('no usable depth points at the selected confidence/depth thresholds')
    sampled_frames = [index['frames'][number] for number in chosen]
    corrected_points, ablation = _drift_ablation(sampled_frames, frame_points, drift_correction)
    frame_offsets = {}
    closure = ablation['applied_constraint']
    for sample_index, frame in enumerate(sampled_frames):
        if closure is None or sample_index <= closure['first_sample_index']:
            fraction = 0
        else:
            fraction = min(1, (sample_index-closure['first_sample_index']) /
                           (closure['second_sample_index']-closure['first_sample_index']))
        frame_offsets[frame['frame_id']] = tuple(fraction*value for value in
                                                  (closure['translation_m'] if closure else (0, 0, 0)))
    corrected_frame_points = {}
    for frame_id, raw_points in frame_points.items():
        offset = frame_offsets[frame_id]
        corrected_frame_points[frame_id] = [tuple(point[axis]+offset[axis] for axis in range(3))
                                            for point in raw_points]
    corrected_horizontal = [(y+frame_offsets[frame_id][1], sign, frame_id)
                            for y, sign, frame_id in horizontal]
    corrected_vertical = [(x+frame_offsets[frame_id][0], y+frame_offsets[frame_id][1],
                           z+frame_offsets[frame_id][2], nx, nz, frame_id)
                          for x, y, z, nx, nz, frame_id in vertical]
    from .lidar_room import fit_single_room
    room_fit = (fit_single_room(corrected_frame_points, corrected_horizontal, corrected_vertical,
                                statistics.median(position[1] for position in pose_positions), pose_positions)
                if single_room else {'status': 'unresolved', 'warnings': [
                    'Single-room rectangular fitting requires an explicit --room-id; multiroom segmentation is not yet validated.']})
    light_audit = _rgb_light_audit(scan, index['rgb_decoded_frame_count'])
    ply = run_dir / 'lidar_points.ply'
    with ply.open('w', encoding='ascii') as stream:
        stream.write(f'ply\nformat ascii 1.0\nelement vertex {len(points)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
        for point, _, _ in points:
            stream.write(f'{point[0]:.5f} {point[1]:.5f} {point[2]:.5f}\n')
    corrected_ply = run_dir / 'lidar_points_after_drift.ply'
    with corrected_ply.open('w', encoding='ascii') as stream:
        stream.write(f'ply\nformat ascii 1.0\nelement vertex {len(corrected_points)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
        for point in corrected_points:
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
            'Camera local x right, y down, z forward; exported xyzw quaternion is treated as camera-to-world. This matches the StrayVisualizer/Open3D depth convention linked from the Stray Scanner repository.',
            'No lens-distortion correction or RGB alignment is applied.',
            'Confidence code >= 1 is used because Stray documents 0/1/2 with higher meaning more confidence.'
        ],
        'selection': {'total_frames': len(index['frames']), 'selected_frame_indices': chosen,
                      'revisit_anchor_frame_ids': anchor_ids,
                      'rule': 'reserve up to six slots for pose-near similar-view return pairs; fill remaining slots with one best valid-depth/confidence frame per evenly spaced temporal window from up to four candidates; pose proximity alone never authorizes drift correction',
                      'probe_pixel_stride': 8, 'quality_probes': selection_probes,
                      'pixel_stride': pixel_stride, 'min_confidence_code': minimum_confidence,
                      'depth_range_m': [.25, 6.0]},
        'point_count': len(points), 'horizontal_candidate_count': len(horizontal),
        'vertical_candidate_count': len(vertical),
        'confidence_counts_sampled': {str(k): v for k,v in sorted(confidence_counts.items())},
        'rejected_sample_counts': dict(rejection),
        'tracking_jump_frame_indices': jump_indices,
        'pose_start_end_distance_m': math.dist(pose_positions[0], pose_positions[-1]),
        'pose_return_candidates': revisit_candidates['nearby_pose_pairs'],
        'pose_revisit_candidates': revisit_candidates['similar_view_pairs'],
        'pose_revisit_warning': 'Pose proximity is not loop closure; overlapping 3D surfaces must confirm the same view before correcting drift.',
        'drift_ablation': ablation,
        'room_fit': room_fit,
        'rgb_light_audit': light_audit,
        'largest_pose_step_m': max(pose_jumps, default=0),
        'coordinate_extent_m': {'x': [min(xs), max(xs)], 'y': [min(ys), max(ys)], 'z': [min(zs), max(zs)]},
        'horizontal_y_peaks': sorted(_horizontal_bins(horizontal), key=lambda item: -item['samples'])[:8],
        'horizontal_surface_bins': _horizontal_bins(horizontal),
        'vertical_plane_candidates': _vertical_bins(vertical),
        'frames': frame_records,
        'warnings': ['Candidate plane heights are not a calibrated floor/ceiling estimate.',
                     'Reflective surface type cannot be diagnosed from sparse depth alone; inspect RGB and revisit weak-depth areas.']
    }
    if not drift_correction:
        report['warnings'].append('Drift correction is disabled; recorded poses are used as exported.')
    elif ablation['applied_constraint'] is None:
        report['warnings'].append('No verified same-view geometric closure; drift correction left the scan unchanged.')
    strong_walls = [item for item in report['vertical_plane_candidates']
                    if item['samples'] >= 100 and item['supporting_frames'] >= 3 and item['vertical_span_m'] >= 1.5]
    if not any(60 <= abs(first['normal_angle_degrees'] - second['normal_angle_degrees']) <= 120
               for first in strong_walls for second in strong_walls):
        report['warnings'].append('No two strongly supported perpendicular wall directions; room corners and boundaries remain unresolved.')
    camera_height = statistics.median(position[1] for position in pose_positions)
    for label, side in (('lower', -1), ('upper', 1)):
        if not any(item['supporting_frames'] >= 4 and item['samples'] >= 100 and
                   side * (item['center_m'] - camera_height) >= .3
                   for item in report['horizontal_surface_bins']):
            report['warnings'].append(f'No strongly supported {label} horizontal patch relative to the camera trajectory; floor/ceiling coverage is unverified.')
    weak_coverage = [item['frame_id'] for item in frame_records
                     if item['accepted_points'] / max(1, item['sampled_pixels']) < .15]
    report['weak_depth_frame_ids'] = weak_coverage
    if weak_coverage:
        report['warnings'].append(f'{len(weak_coverage)} sampled frames retain under 15% of depth pixels; surface measurements remain unbounded.')
    report['warnings'].extend(room_fit['warnings'])
    if light_audit['low_light_frame_count']:
        report['warnings'].append(f"{light_audit['low_light_frame_count']} sampled RGB frames appear dark by a scan-wide heuristic; depth frame correspondence is unresolved.")
    if jump_indices:
        report['warnings'].append(f'{len(jump_indices)} pose steps exceed 0.10 m between consecutive frames; inspect tracking before using geometry')
    weak_frames = [item['frame_id'] for item in frame_records if item['accepted_points'] < 500]
    if weak_frames:
        report['warnings'].append(f'{len(weak_frames)} sampled depth frames have fewer than 500 retained points')
    report_path = run_dir / 'lidar_geometry.json'
    write_json(report_path, report)
    return report, [{'path': str(path), 'sha256': sha256(path)} for path in (ply, corrected_ply, report_path)]
