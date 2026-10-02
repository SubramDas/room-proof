"""Auditable 2D-to-LiDAR 3D poses for independent captures.

Without explicit camera intrinsics and scan RGB-to-depth pixel calibration,
PnP output remains a hypothesis even when reprojection residual is small.
Only calibrated agreement across separated scan views can be accepted.
"""

from pathlib import Path
from functools import lru_cache
import math
import statistics

import cv2
import numpy as np
from PIL import Image

from .lidar_geometry import project


def load_calibration(path):
    """Load explicit pixel calibration; never treat evaluator lengths as input."""
    import json
    from .cli import sha256

    source = Path(path).resolve(strict=True)
    data = json.loads(source.read_text())
    if data.get('version') != 1 or not isinstance(data.get('camera_intrinsics'), dict):
        raise ValueError('calibration needs version 1 and camera_intrinsics')
    mapping = data.get('scan_rgb_to_depth')
    if not isinstance(mapping, dict):
        raise ValueError('calibration needs scan_rgb_to_depth pixel mapping')
    for key in ('scan_view_size', 'depth_size'):
        size = mapping.get(key)
        if not isinstance(size, list) or len(size) != 2 or any(
                not isinstance(value, int) or value <= 0 for value in size):
            raise ValueError(f'invalid {key} in calibration')
    affine = mapping.get('affine_2x3')
    if not isinstance(affine, list) or len(affine) != 2 or any(
            not isinstance(row, list) or len(row) != 3 or
            any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in row)
            for row in affine):
        raise ValueError('calibration needs finite 2x3 scan pixel mapping')
    for key, camera in data['camera_intrinsics'].items():
        if not isinstance(key, str) or not isinstance(camera, dict):
            raise ValueError('camera intrinsics must be keyed by tier or exact source ref')
        size = camera.get('image_size')
        if not isinstance(size, list) or len(size) != 2 or any(
                not isinstance(value, int) or value <= 0 for value in size):
            raise ValueError(f'invalid camera image_size for {key}')
        for field in ('fx', 'fy', 'cx', 'cy'):
            value = camera.get(field)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'invalid camera {field} for {key}')
        if camera['fx'] <= 0 or camera['fy'] <= 0:
            raise ValueError(f'camera focal length must be positive for {key}')
    data['source_sha256'] = sha256(source)
    return data


def _scan_to_depth(xy, sample_width, sample_height, rotation, depth_width, depth_height,
                   calibration=None):
    x, y = xy
    if calibration is not None:
        mapping = calibration['scan_rgb_to_depth']
        matching_size = ([sample_height, sample_width] if rotation in (90, 270)
                         else [sample_width, sample_height])
        if mapping['scan_view_size'] != matching_size or mapping['depth_size'] != [depth_width, depth_height]:
            return -1, -1
        affine = mapping['affine_2x3']
        return (round(affine[0][0]*x+affine[0][1]*y+affine[0][2]),
                round(affine[1][0]*x+affine[1][1]*y+affine[1][2]))
    if rotation == 90:
        x, y = y, sample_height - 1 - x
    elif rotation == 180:
        x, y = sample_width - 1 - x, sample_height - 1 - y
    elif rotation == 270:
        x, y = sample_width - 1 - y, x
    return int(x * depth_width / sample_width), int(y * depth_height / sample_height)


@lru_cache(maxsize=32)
def _images(scan, frame_id):
    depth_path = Path(scan)/'depth'/f"{frame_id}.png"
    confidence_path = Path(scan)/'confidence'/f"{frame_id}.png"
    with Image.open(depth_path) as depth_image, Image.open(confidence_path) as conf_image:
        depth = np.asarray(depth_image)
        confidence = np.asarray(conf_image)
    return depth, confidence


def _point_at(scan, frame, xy, sample_width, sample_height, rotation,
              calibration=None):
    depth, confidence = _images(str(scan), frame['frame_id'])
    if depth.shape != confidence.shape:
        return None
    height, width = depth.shape
    u, v = _scan_to_depth(xy, sample_width, sample_height, rotation, width, height,
                          calibration)
    if not 1 <= u < width-1 or not 1 <= v < height-1:
        return None
    patch = depth[v-1:v+2, u-1:u+2]
    valid = patch[confidence[v-1:v+2, u-1:u+2] >= 1]
    valid = valid[(valid >= 250) & (valid <= 6000)]
    if len(valid) < 6 or np.percentile(valid, 90)-np.percentile(valid, 10) > 80:
        return None
    return project(u, v, float(np.median(valid)), frame['pose']['intrinsics_px'],
                   (width, height), frame['pose'])


def inspect_registration(links, scan, lidar_index, pairing, rgb_index, rotation,
                         calibration=None):
    """Probe held-out PnP and accept only consistent calibrated scan views."""
    if not pairing.get('spatial_registration_verified'):
        return {'status': 'unresolved', 'pair_hypotheses': [],
                'reason': 'scan RGB/depth sampled registration unresolved'}
    by_depth = {frame['frame_id']: frame for frame in lidar_index['frames']}
    by_rgb = {frame['frame_id']: frame for frame in rgb_index['frames']}
    paired = {item['rgb_frame_index']: item for item in pairing['links']}
    hypotheses = []
    attempted_by_view = {}
    for record in links['records']:
        if not record['overlap_supported'] or record['right_tier'] != 'scan_rgb':
            continue
        points = record.get('inlier_coordinates', [])
        if not points:
            continue
        rgb_frame = by_rgb.get(record['right_frame_id'])
        if rgb_frame is None:
            continue
        timing = paired.get(rgb_frame['source_frame_index'])
        hypothesis = {'left_source_ref': record['left_source_ref'],
                      'scan_source_ref': record['right_source_ref'],
                      'scan_pairing_status': timing['status'] if timing else 'absent',
                      'input_2d_matches': len(points), 'status': 'unresolved'}
        hypotheses.append(hypothesis)
        count = attempted_by_view.get(record['left_source_ref'], 0)
        if count >= 3:
            hypothesis['reason'] = 'bounded registration search: three stronger pairs already selected for this visual view'
            continue
        attempted_by_view[record['left_source_ref']] = count + 1
        if not timing or timing['status'] != 'registered_candidate':
            hypothesis['reason'] = 'scan frame lacks sampled pixel registration'
            continue
        depth_frame = by_depth.get(timing['depth_frame_id'])
        if depth_frame is None:
            hypothesis['reason'] = 'paired depth frame missing'
            continue
        hypothesis['depth_frame_id'] = depth_frame['frame_id']
        hypothesis['scan_camera_center_m'] = depth_frame['pose']['translation_m']
        world, pixels = [], []
        for item in points:
            xyz = _point_at(scan, depth_frame, item['right_xy'],
                            rgb_frame['width'], rgb_frame['height'], rotation,
                            calibration)
            if xyz is not None:
                world.append(xyz)
                pixels.append(item['left_xy'])
        hypothesis['valid_confident_3d_matches'] = len(world)
        if len(world) < 24:
            hypothesis['reason'] = 'too few locally consistent depth landmarks'
            continue
        world = np.asarray(world, np.float64)
        pixels = np.asarray(pixels, np.float64)
        singular = np.linalg.svd(world-world.mean(axis=0), compute_uv=False)
        hypothesis['landmark_singular_values_m'] = [round(float(value), 4) for value in singular]
        # Search disclosed focal assumptions unless a source-specific calibrated
        # camera matrix and scan-RGB-to-depth mapping are both supplied.
        width, height = record['left_image_size']
        training = np.arange(len(world)) % 5 != 0
        validation = ~training
        if validation.sum() < 5:
            hypothesis['reason'] = 'insufficient held-out 3D landmarks'
            continue
        options = []
        source_camera = None
        if calibration is not None:
            source_camera = calibration.get('camera_intrinsics', {}).get(
                record['left_source_ref'], calibration.get('camera_intrinsics', {}).get(record['left_tier']))
            if source_camera is not None and source_camera['image_size'] != [width, height]:
                hypothesis['reason'] = 'calibrated camera dimensions do not match this view'
                continue
            if source_camera is not None and (singular[-1] < .15 or singular[-1]/singular[0] < .025):
                hypothesis['reason'] = 'calibrated pose landmarks are nearly planar or lack 3D spread'
                continue
        cameras = ([('calibrated', np.array([
            [source_camera['fx'], 0, source_camera['cx']],
            [0, source_camera['fy'], source_camera['cy']], [0, 0, 1]], np.float64))]
                   if source_camera else
                   [(width*factor, np.array([[width*factor, 0, width/2],
                                             [0, width*factor, height/2],
                                             [0, 0, 1]], np.float64))
                    for factor in (.7, 1., 1.3)])
        for focal, camera in cameras:
            cv2.setRNGSeed(0)
            ok, rvec, tvec, inliers = cv2.solvePnPRansac(
                world[training], pixels[training], camera, None,
                iterationsCount=2000, reprojectionError=5, confidence=.999,
                flags=cv2.SOLVEPNP_EPNP)
            if not ok or inliers is None or len(inliers) < 12:
                continue
            predicted, _ = cv2.projectPoints(world[validation], rvec, tvec, camera, None)
            errors = np.linalg.norm(predicted.reshape(-1, 2)-pixels[validation], axis=1)
            options.append({'focal_assumption_px': round(focal, 2) if isinstance(focal, float) else None,
                            'calibrated_camera': focal == 'calibrated',
                            'training_inliers': len(inliers),
                            'validation_median_error_px': round(float(np.median(errors)), 2),
                            'validation_p90_error_px': round(float(np.percentile(errors, 90)), 2),
                            'rvec': [float(x) for x in rvec.ravel()],
                            'tvec_m': [float(x) for x in tvec.ravel()]})
        hypothesis['focal_assumptions_tested'] = ([] if source_camera else
                                                  [width*x for x in (.7, 1., 1.3)])
        if not options:
            hypothesis['reason'] = 'PnP found no supported pose'
            continue
        best = min(options, key=lambda item: (item['validation_median_error_px'],
                                               -item['training_inliers']))
        hypothesis['best_assumed_pose'] = best
        rotation_matrix, _ = cv2.Rodrigues(np.asarray(best['rvec']))
        camera_center = -rotation_matrix.T@np.asarray(best['tvec_m'])
        best['left_camera_center_m'] = [round(float(value), 4) for value in camera_center]
        strong = best['validation_median_error_px'] <= 5 and best['validation_p90_error_px'] <= 10
        hypothesis['status'] = ('plausible_calibrated_pose' if source_camera else
                                'plausible_intrinsics_assumed') if strong else 'unresolved'
        hypothesis['reason'] = ('needs agreement with a separated scan view' if source_camera else
                                'unknown independent camera intrinsics and RGB/depth extrinsics; '
                                'reprojection fit alone cannot verify physical placement')
    consistent = []
    plausible = [item for item in hypotheses if item['status'] in
                 ('plausible_intrinsics_assumed', 'plausible_calibrated_pose')]
    for i, first in enumerate(plausible):
        for second in plausible[i+1:]:
            if first['left_source_ref'] != second['left_source_ref']:
                continue
            a, b = first['best_assumed_pose'], second['best_assumed_pose']
            if a['focal_assumption_px'] != b['focal_assumption_px'] or a['calibrated_camera'] != b['calibrated_camera']:
                continue
            scan_separation = math.dist(first['scan_camera_center_m'], second['scan_camera_center_m'])
            center_difference = math.dist(a['left_camera_center_m'], b['left_camera_center_m'])
            ra, _ = cv2.Rodrigues(np.asarray(a['rvec']))
            rb, _ = cv2.Rodrigues(np.asarray(b['rvec']))
            cosine = np.clip((np.trace(ra@rb.T)-1)/2, -1, 1)
            angle = math.degrees(math.acos(cosine))
            if scan_separation >= .5 and center_difference <= .15 and angle <= 10:
                consistent.append({
                    'left_source_ref': first['left_source_ref'],
                    'scan_source_refs': [first['scan_source_ref'], second['scan_source_ref']],
                    'scan_camera_separation_m': round(scan_separation, 3),
                    'left_camera_center_disagreement_m': round(center_difference, 3),
                    'left_camera_rotation_disagreement_degrees': round(angle, 2),
                    'shared_focal_assumption_px': a['focal_assumption_px'],
                    'calibrated_camera': a['calibrated_camera'],
                    'status': ('cross_view_consistent_calibrated' if a['calibrated_camera'] else
                               'cross_view_consistent_under_assumed_calibration')})
    accepted = []
    if calibration and pairing.get('spatial_registration_verified'):
        by_source = {}
        for item in consistent:
            if item['calibrated_camera']:
                by_source.setdefault(item['left_source_ref'], []).append(item)
        for source_ref, items in by_source.items():
            scan_refs = sorted({ref for item in items for ref in item['scan_source_refs']})
            if len(scan_refs) < 2:
                continue
            matching = [item for item in plausible if item['left_source_ref'] == source_ref and
                        item['status'] == 'plausible_calibrated_pose' and
                        item['scan_source_ref'] in scan_refs]
            if len(matching) < 2:
                continue
            centers = [item['best_assumed_pose']['left_camera_center_m'] for item in matching]
            center = [round(float(statistics.median(row[axis] for row in centers)), 4)
                      for axis in range(3)]
            best = min(matching, key=lambda item:
                       item['best_assumed_pose']['validation_median_error_px'])
            pose = best['best_assumed_pose']
            accepted.append({'left_source_ref': source_ref, 'scan_source_refs': scan_refs,
                             'camera_center_m': center, 'supporting_pair_count': len(matching),
                             'world_to_camera_rvec': pose['rvec'],
                             'world_to_camera_tvec_m': pose['tvec_m'],
                             'validation_median_error_px': pose['validation_median_error_px'],
                             'status': 'calibrated_multi_scan_view_pose'})
    return {'status': 'accepted_calibrated_poses' if accepted else 'hypotheses_only',
            'pair_hypotheses': hypotheses,
            'plausible_assumed_pose_count': sum(x['status'] == 'plausible_intrinsics_assumed' for x in hypotheses),
            'plausible_calibrated_pose_count': sum(x['status'] == 'plausible_calibrated_pose' for x in hypotheses),
            'cross_view_consistent_hypotheses': consistent,
            'accepted_camera_poses': accepted,
            'cross_view_thresholds': {'minimum_scan_camera_separation_m': .5,
                                      'maximum_left_camera_center_disagreement_m': .15,
                                      'maximum_rotation_disagreement_degrees': 10},
            'metric_registration_accepted': bool(accepted),
            'calibration_sha256': calibration.get('source_sha256') if calibration else None,
            'reason': ('calibrated intrinsics, scan pixel mapping, and separated scan-view '
                       'PnP agree' if accepted else
                       'independent camera calibration and cross-view consistency are not verified')}
