"""Auditable 2D-to-LiDAR 3D pose hypotheses for independent captures.

The ordinary camera intrinsics and Stray RGB/depth extrinsics are not known.
PnP output therefore remains an explicitly assumed hypothesis, even if its
reprojection residual is small. No hypothesis is written into a plan.
"""

from pathlib import Path
from functools import lru_cache
import math

import cv2
import numpy as np
from PIL import Image

from .lidar_geometry import project


def _scan_to_depth(xy, sample_width, sample_height, rotation, depth_width, depth_height):
    x, y = xy
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


def _point_at(scan, frame, xy, sample_width, sample_height, rotation):
    depth, confidence = _images(str(scan), frame['frame_id'])
    if depth.shape != confidence.shape:
        return None
    height, width = depth.shape
    u, v = _scan_to_depth(xy, sample_width, sample_height, rotation, width, height)
    if not 1 <= u < width-1 or not 1 <= v < height-1:
        return None
    patch = depth[v-1:v+2, u-1:u+2]
    valid = patch[confidence[v-1:v+2, u-1:u+2] >= 1]
    valid = valid[(valid >= 250) & (valid <= 6000)]
    if len(valid) < 6 or np.percentile(valid, 90)-np.percentile(valid, 10) > 80:
        return None
    return project(u, v, float(np.median(valid)), frame['pose']['intrinsics_px'],
                   (width, height), frame['pose'])


def inspect_registration(links, scan, lidar_index, pairing, rgb_index, rotation):
    """Try held-out PnP on supported 2D pairs; never infer uncalibrated scale."""
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
                            rgb_frame['width'], rgb_frame['height'], rotation)
            if xyz is not None:
                world.append(xyz)
                pixels.append(item['left_xy'])
        hypothesis['valid_confident_3d_matches'] = len(world)
        if len(world) < 24:
            hypothesis['reason'] = 'too few locally consistent depth landmarks'
            continue
        world = np.asarray(world, np.float64)
        pixels = np.asarray(pixels, np.float64)
        # Independent camera focal length is unavailable. Search a small,
        # disclosed range; the resulting pose must remain a hypothesis.
        width, height = record['left_image_size']
        training = np.arange(len(world)) % 5 != 0
        validation = ~training
        if validation.sum() < 5:
            hypothesis['reason'] = 'insufficient held-out 3D landmarks'
            continue
        options = []
        for factor in (.7, 1., 1.3):
            focal = width*factor
            camera = np.array([[focal, 0, width/2], [0, focal, height/2], [0, 0, 1]], np.float64)
            cv2.setRNGSeed(0)
            ok, rvec, tvec, inliers = cv2.solvePnPRansac(
                world[training], pixels[training], camera, None,
                iterationsCount=2000, reprojectionError=5, confidence=.999,
                flags=cv2.SOLVEPNP_EPNP)
            if not ok or inliers is None or len(inliers) < 12:
                continue
            predicted, _ = cv2.projectPoints(world[validation], rvec, tvec, camera, None)
            errors = np.linalg.norm(predicted.reshape(-1, 2)-pixels[validation], axis=1)
            options.append({'focal_assumption_px': round(focal, 2),
                            'training_inliers': len(inliers),
                            'validation_median_error_px': round(float(np.median(errors)), 2),
                            'validation_p90_error_px': round(float(np.percentile(errors, 90)), 2),
                            'rvec': [float(x) for x in rvec.ravel()],
                            'tvec_m': [float(x) for x in tvec.ravel()]})
        hypothesis['focal_assumptions_tested'] = [width*x for x in (.7, 1., 1.3)]
        if not options:
            hypothesis['reason'] = 'PnP found no supported pose'
            continue
        best = min(options, key=lambda item: (item['validation_median_error_px'],
                                               -item['training_inliers']))
        hypothesis['best_assumed_pose'] = best
        rotation_matrix, _ = cv2.Rodrigues(np.asarray(best['rvec']))
        camera_center = -rotation_matrix.T@np.asarray(best['tvec_m'])
        best['left_camera_center_m'] = [round(float(value), 4) for value in camera_center]
        hypothesis['status'] = 'plausible_intrinsics_assumed' if (
            best['validation_median_error_px'] <= 5 and best['validation_p90_error_px'] <= 10) else 'unresolved'
        hypothesis['reason'] = ('unknown independent camera intrinsics and RGB/depth extrinsics; '
                                'reprojection fit alone cannot verify physical placement')
    consistent = []
    plausible = [item for item in hypotheses if item['status'] == 'plausible_intrinsics_assumed']
    for i, first in enumerate(plausible):
        for second in plausible[i+1:]:
            if first['left_source_ref'] != second['left_source_ref']:
                continue
            a, b = first['best_assumed_pose'], second['best_assumed_pose']
            if a['focal_assumption_px'] != b['focal_assumption_px']:
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
                    'status': 'cross_view_consistent_under_assumed_calibration'})
    return {'status': 'hypotheses_only', 'pair_hypotheses': hypotheses,
            'plausible_assumed_pose_count': sum(x['status'] == 'plausible_intrinsics_assumed' for x in hypotheses),
            'cross_view_consistent_hypotheses': consistent,
            'cross_view_thresholds': {'minimum_scan_camera_separation_m': .5,
                                      'maximum_left_camera_center_disagreement_m': .15,
                                      'maximum_rotation_disagreement_degrees': 10},
            'metric_registration_accepted': False,
            'reason': 'independent camera calibration and cross-view consistency are not verified'}
