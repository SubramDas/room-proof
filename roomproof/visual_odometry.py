"""Sparse, arbitrary-scale visual motion from ordered standalone-video views."""

import cv2
import numpy as np


def estimate_video_trajectory(records):
    pairs = sorted((item for item in records
                    if item['left_tier'] == item['right_tier'] == 'video'),
                   key=lambda item: (item.get('left_source_frame_index', -1),
                                     item.get('right_source_frame_index', -1)))
    edges = []
    centers = {}
    orientations = {}
    for pair in pairs:
        source = pair['left_source_ref']; target = pair['right_source_ref']
        points = pair.get('inlier_coordinates', [])
        entry = {'source_ref': source, 'target_ref': target,
                 'source_frame_index': pair.get('left_source_frame_index'),
                 'target_frame_index': pair.get('right_source_frame_index'),
                 'status': 'unresolved'}
        edges.append(entry)
        if not pair['overlap_supported'] or len(points) < 16:
            entry['reason'] = 'too few epipolar inlier matches'
            continue
        first = np.asarray([item['left_xy'] for item in points], np.float64)
        second = np.asarray([item['right_xy'] for item in points], np.float64)
        width, height = pair['left_image_size']
        focal = float(width)
        camera = np.asarray([[focal, 0, width/2], [0, focal, height/2], [0, 0, 1]])
        cv2.setRNGSeed(0)
        essential, mask = cv2.findEssentialMat(first, second, camera,
                                               cv2.RANSAC, .999, 2.0)
        if essential is None or essential.shape != (3, 3):
            entry['reason'] = 'essential-matrix fit failed'
            continue
        count, rotation, translation, positive = cv2.recoverPose(
            essential, first, second, camera, mask=mask)
        if count < 14:
            entry['reason'] = 'insufficient points with consistent positive depth'
            continue
        normalized_first = cv2.undistortPoints(first.reshape(-1, 1, 2), camera, None).reshape(-1, 2)
        normalized_second = cv2.undistortPoints(second.reshape(-1, 1, 2), camera, None).reshape(-1, 2)
        p1 = np.eye(3, 4)
        p2 = np.hstack((rotation, translation))
        homogeneous = cv2.triangulatePoints(p1, p2, normalized_first.T, normalized_second.T)
        depth = homogeneous[2]/homogeneous[3]
        finite = np.isfinite(depth) & (depth > 0)
        if finite.sum() < 14:
            entry['reason'] = 'sparse visual geometry has insufficient positive-depth points'
            continue
        entry.update({'status': 'arbitrary_scale_motion_hypothesis',
                      'positive_depth_matches': int(count),
                      'triangulated_positive_points': int(finite.sum()),
                      'focal_assumption_px': focal,
                      'relative_rotation_matrix': rotation.round(6).tolist(),
                      'relative_translation_direction': translation.ravel().round(6).tolist(),
                      'reason': 'monocular translation has arbitrary scale; camera intrinsics are assumed'})
        if source not in centers:
            centers[source] = np.zeros(3)
            orientations[source] = np.eye(3)
        # recoverPose gives x_target = R*x_source + t. Compose world-to-camera
        # rotations, then transform the unit target-camera center to world.
        world_to_source = orientations[source]
        centers[target] = centers[source] - world_to_source.T@rotation.T@translation.ravel()
        orientations[target] = rotation@world_to_source
    return {'report_version': '0.1.0', 'status': 'arbitrary_scale_hypotheses_only',
            'method': 'calibration-assumed essential matrix and positive-depth triangulation on adjacent selected video views',
            'edges': edges,
            'camera_centers_arbitrary_units': [
                {'source_ref': ref, 'center': center.round(4).tolist()}
                for ref, center in centers.items()],
            'supported_edge_count': sum(item['status'] == 'arbitrary_scale_motion_hypothesis'
                                        for item in edges),
            'warnings': ['No metric scale or calibrated camera intrinsics; this path cannot certify a doorway crossing.']}
