"""Source-linked 2D view correspondences across independent captures.

These matches are visual hypotheses. They do not establish a shared 3D pose,
metric scale, doorway identity, or room adjacency.
"""

import json
from pathlib import Path

from .cli import sha256, write_json
from .visual_geometry import _analyze_rgb, _photo_rgb, compare


def _spread(items, maximum):
    if len(items) <= maximum:
        return list(items)
    if maximum == 1:
        return [items[len(items)//2]]
    return [items[position] for position in
            sorted({i*(len(items)-1)//(maximum-1) for i in range(maximum)})]


def _load_run(path, tier):
    run_dir = Path(path).resolve(strict=True)
    quality = json.loads((run_dir/'quality_report.json').read_text())
    if quality['tier'] != tier or quality['validity'] == 'invalid':
        raise ValueError(f'{run_dir}: expected a valid {tier} capture run')
    index_name = 'lidar_frames.json' if tier == 'lidar' else 'frames.json'
    index = json.loads((run_dir/index_name).read_text())
    if quality['capture_id'] != index['capture_id']:
        raise ValueError(f'{run_dir}: capture ID differs between quality and frame index')
    return run_dir, quality, index


def _opening_proposals(run_dir, index):
    path = run_dir/'visual_candidates.json'
    if not path.is_file():
        return {}
    report = json.loads(path.read_text())
    if report.get('capture_id') != index['capture_id'] or not report.get('status', '').startswith('proposals'):
        return {}
    from .visual_candidates import validate_candidate_report
    reference_index = index
    if index['tier'] == 'lidar' and (run_dir/'rgb_frames.json').is_file():
        reference_index = json.loads((run_dir/'rgb_frames.json').read_text())
    validate_candidate_report(report, reference_index)
    by_frame = {}
    for item in report['candidates']:
        if item['class'] in ('door', 'doorway', 'open_passage', 'window'):
            by_frame.setdefault(item['frame_id'], []).append({
                'candidate_id': item['candidate_id'], 'class': item['class'],
                'raw_model_score': item['raw_model_score'],
                'geometry': item['geometry']})
    return by_frame


def _analyze_photo(source, frame):
    path = Path(source)/frame['source_path']
    if sha256(path) != frame['source_sha256']:
        raise ValueError(f"photo changed since its source run: {frame['source_path']}")
    rgb, width, height = _photo_rgb(path)
    item = _analyze_rgb(rgb, width, height, frame)
    item['_rgb'], item['_size'] = rgb, (width, height)
    return item


def _analyze_sample(run_dir, frame, rotation=0):
    rgb = (run_dir/'frames'/frame['sampled_path']).read_bytes()
    width, height = frame['width'], frame['height']
    if len(rgb) != width*height*3:
        raise ValueError(f"{frame['frame_id']}: sampled RGB length differs from index")
    if rotation:
        from PIL import Image
        image = Image.frombytes('RGB', (width, height), rgb)
        image = image.rotate(-rotation, expand=True)
        rgb, width, height = image.tobytes(), image.width, image.height
    item = _analyze_rgb(rgb, width, height, frame)
    item['_rgb'], item['_size'] = rgb, (width, height)
    return item


def link_captures(photo_run, video_run, lidar_run, photo_source, lidar_source,
                  run_dir, max_views=12, lidar_rgb_rotation=0,
                  match_backend='patch', model_root='.room-proof/models',
                  calibration_path=None):
    """Compare bounded photo/video/scan-RGB views without claiming 3D registration."""
    if max_views < 9:
        raise ValueError('at least nine scan RGB views are required for the registration gate')
    if lidar_rgb_rotation not in (0, 90, 180, 270):
        raise ValueError('LiDAR RGB rotation must be 0, 90, 180, or 270 degrees')
    if calibration_path and match_backend != 'aliked-lightglue':
        raise ValueError('calibrated registration requires --match-backend aliked-lightglue')
    photo_dir, photo_quality, photo_index = _load_run(photo_run, 'photo')
    video_dir, video_quality, video_index = _load_run(video_run, 'video')
    lidar_dir, lidar_quality, lidar_index = _load_run(lidar_run, 'lidar')
    property_ids = {item['property_id'] for item in
                    (photo_quality, video_quality, lidar_quality)}
    if len(property_ids) != 1:
        raise ValueError('capture runs have different property IDs')
    if photo_quality['input_path'] != str(Path(photo_source).resolve(strict=True)):
        raise ValueError('photo source differs from the photo run input')
    if lidar_quality['input_path'] != str(Path(lidar_source).resolve(strict=True)):
        raise ValueError('LiDAR source differs from the LiDAR run input')
    video_path = Path(video_quality['input_path']).resolve(strict=True)
    if sha256(video_path) != video_index['source_sha256']:
        raise ValueError('standalone video changed since its source run')
    rgb_source_record = next((item for item in lidar_quality['source_files']
                              if item['path'] == 'rgb.mp4'), None)
    if rgb_source_record is None or sha256(Path(lidar_source)/'rgb.mp4') != rgb_source_record['sha256']:
        raise ValueError('LiDAR RGB changed since its source run')

    photo_proposals = _opening_proposals(photo_dir, photo_index)
    video_proposals = _opening_proposals(video_dir, video_index)

    photos = [_analyze_photo(photo_source, frame)
              for frame in _spread(photo_index['frames'], max_views)]
    videos = [_analyze_sample(video_dir, frame)
              for frame in _spread(video_index['frames'], max_views)]
    from .lidar_rgb import read_lidar_rgb_samples
    geometry = json.loads((lidar_dir/'lidar_geometry.json').read_text())
    rgb_index, pairing, rgb_artifacts = read_lidar_rgb_samples(
        lidar_source, lidar_index, geometry, run_dir, max_views)
    scans = [_analyze_sample(run_dir, frame, lidar_rgb_rotation)
             for frame in rgb_index['frames']]
    scan_proposals = _opening_proposals(lidar_dir, rgb_index)
    groups = {'photo': photos, 'video': videos, 'scan_rgb': scans}
    learned = None
    if match_backend == 'aliked-lightglue':
        from .learned_matching import ALIKEDMatcher
        learned = ALIKEDMatcher(model_root=model_root)
        for items in groups.values():
            for item in items:
                item['_learned'] = learned.extract(item['_rgb'], *item['_size'])
                del item['_rgb']
    elif match_backend != 'patch':
        raise ValueError(f'unknown match backend: {match_backend}')
    proposals = {'photo': photo_proposals, 'video': video_proposals,
                 'scan_rgb': scan_proposals}
    records = []
    pair_specs = []
    for left_name, right_name in (('photo', 'video'), ('photo', 'scan_rgb'),
                                  ('video', 'scan_rgb')):
        pair_specs.extend((left_name, right_name, left, right)
                          for left in groups[left_name] for right in groups[right_name])
    # Adjacent selected video views support a chronological opening track.
    # Photo/photo matches can connect separate sightings without treating
    # supplied room-folder names as adjacency evidence.
    pair_specs.extend(('video', 'video', left, right)
                      for left, right in zip(videos, videos[1:]))
    pair_specs.extend(('photo', 'photo', left, right)
                      for i, left in enumerate(photos) for right in photos[i+1:])
    source_frames = {'photo': {frame['frame_id']: frame for frame in photo_index['frames']},
                     'video': {frame['frame_id']: frame for frame in video_index['frames']},
                     'scan_rgb': {frame['frame_id']: frame for frame in rgb_index['frames']}}
    for left_name, right_name, left, right in pair_specs:
        left_frame = source_frames[left_name][left['frame_id']]
        right_frame = source_frames[right_name][right['frame_id']]
        baseline = compare(left, right)
        if learned is None:
            result = baseline
        else:
            result = learned.compare(left['_learned'], right['_learned'],
                                     left['_size'], right['_size'])
            result['patch_baseline'] = {
                key: baseline[key] for key in
                ('matches', 'inliers', 'inlier_fraction', 'overlap_supported')}
        records.append({'left_tier': left_name, 'right_tier': right_name,
                        'left_frame_id': left['frame_id'],
                        'right_frame_id': right['frame_id'],
                        'left_room_label': left_frame.get('room_id'),
                        'right_room_label': right_frame.get('room_id'),
                        'left_source_frame_index': left_frame.get('source_frame_index'),
                        'right_source_frame_index': right_frame.get('source_frame_index'),
                        'left_image_size': list(left['_size']),
                        'right_image_size': list(right['_size']),
                        'left_source_ref': left['source_ref'],
                        'right_source_ref': right['source_ref'],
                        'left_opening_proposals': proposals[left_name].get(left['frame_id'], []),
                        'right_opening_proposals': proposals[right_name].get(right['frame_id'], []),
                        **result})
    records.sort(key=lambda item: (not item['overlap_supported'],
                                   -item['inliers'], -item['matches'],
                                   item['left_source_ref'], item['right_source_ref']))
    report = {
        'report_version': '0.1.0', 'status': 'visual_correspondence_hypotheses_only',
        'property_id': property_ids.pop(),
        'source_runs': {'photo': str(photo_dir), 'video': str(video_dir),
                        'lidar': str(lidar_dir)},
        'method': (learned.provenance['method'] if learned else
                   'same bounded thumbnail features and mutual descriptor matching as visual_geometry; no 3D transform'),
        'matching_provenance': learned.provenance if learned else None,
        'selected_views': {name: [{'frame_id': item['frame_id'],
                                   'source_ref': item['source_ref'],
                                   'corner_count': item['quality']['corner_count']}
                                  for item in items]
                           for name, items in groups.items()},
        'opening_proposal_count': {name: sum(len(proposals[name].get(item['frame_id'], []))
                                            for item in groups[name]) for name in groups},
        'lidar_rgb_rotation_clockwise_degrees': lidar_rgb_rotation,
        'rgb_pairing_path': 'rgb_pairing.json',
        'pair_count': len(records),
        'supported_2d_overlap_count': sum(item['overlap_supported'] for item in records),
        'records': records,
        'warnings': [
            '2D image overlap is a candidate correspondence, not verified cross-capture registration.',
            'No matched 3D landmarks, camera transform, shared doorway identity, or metric room connection is inferred.',
            'Opening boxes are linked only as image-region tracks, not verified as one physical opening.',
            'Photo/video frames remain independent of scan RGB timestamps and frame indices.'
        ],
    }
    path = Path(run_dir)/'cross_capture_links.json'
    write_json(path, report)
    calibration = None
    if learned is not None:
        from .metric_registration import inspect_registration, load_calibration
        calibration = load_calibration(calibration_path) if calibration_path else None
        registration = inspect_registration(report, lidar_source, lidar_index,
                                            pairing, rgb_index, lidar_rgb_rotation,
                                            calibration)
    else:
        registration = {'status': 'not_run_without_2d_keypoint_correspondences',
                        'pair_hypotheses': [], 'plausible_assumed_pose_count': 0,
                        'cross_view_consistent_hypotheses': [],
                        'metric_registration_accepted': False}
    registration_path = Path(run_dir)/'cross_capture_registration.json'
    write_json(registration_path, registration)
    from .opening_correspondence import match_opening_regions
    opening_links = match_opening_regions(report['records'], lidar_rgb_rotation)
    opening_path = Path(run_dir)/'opening_correspondences.json'
    write_json(opening_path, opening_links)
    if learned is not None:
        from .video_temporal import trace_video
        from .visual_odometry import estimate_video_trajectory
        temporal = trace_video(video_quality['input_path'], video_index,
                               opening_links, records)
        visual_odometry = estimate_video_trajectory(records)
    else:
        temporal = {'status': 'not_run_without_optical_flow_backend',
                    'decoded_frame_count': None, 'opening_track_segments': [],
                    'continuous_region_segment_count': 0}
        visual_odometry = {'status': 'not_run_without_keypoint_correspondences',
                           'edges': [], 'supported_edge_count': 0}
    temporal_path = Path(run_dir)/'video_motion_profile.json'
    write_json(temporal_path, temporal)
    odometry_path = Path(run_dir)/'visual_odometry.json'
    write_json(odometry_path, visual_odometry)
    from .registered_openings import link_registered_openings
    lidar_link_path = lidar_dir/'lidar_candidate_links.json'
    lidar_links = json.loads(lidar_link_path.read_text()) if lidar_link_path.is_file() else {}
    registered_openings = link_registered_openings(
        records, opening_links, registration, lidar_links,
        geometry['room_fit'], calibration)
    registered_path = Path(run_dir)/'registered_openings.json'
    write_json(registered_path, registered_openings)
    from .room_transitions import find_verified_crossings
    transitions = find_verified_crossings(
        registration, registered_openings, geometry['room_fit'])
    transitions_path = Path(run_dir)/'room_transitions.json'
    write_json(transitions_path, transitions)
    room_labels = {}
    for tier, source_dir in (('photo', photo_dir), ('video', video_dir), ('lidar', lidar_dir)):
        plan = json.loads((source_dir/'property_plan.json').read_text())
        room_labels[tier] = [room['id'] for room in plan['rooms']]
    profile_path = video_dir/'coarse_scene_profile.json'
    profile = json.loads(profile_path.read_text()) if profile_path.is_file() else {}
    from .visual_room_map import build_visual_room_map
    room_map = build_visual_room_map(records, opening_links, profile, room_labels,
                                     temporal)
    graph = {
        'report_version': '0.2.0', 'status': 'visual_hypotheses_only',
        'property_id': report['property_id'], 'room_labels_by_capture': room_labels,
        'observations': [
            {'tier': tier, 'frame_id': item['frame_id'],
             'source_ref': item['source_ref'],
             'opening_proposals': proposals[tier].get(item['frame_id'], [])}
            for tier, items in groups.items() for item in items],
        'visual_overlap_edges': [
            {'left_source_ref': item['left_source_ref'],
             'right_source_ref': item['right_source_ref'],
            'inliers': item['inliers'], 'inlier_fraction': item['inlier_fraction'],
            'inlier_coordinates': item.get('inlier_coordinates', [])}
            for item in records if item['overlap_supported']],
        'opening_hypotheses': opening_links['groups'],
        'opening_tracks': room_map['opening_tracks'],
        'transition_hypotheses': room_map['transition_hypotheses'],
        'room_connection_hypotheses': room_map['room_connection_hypotheses'],
        'full_video_frame_count': room_map['full_video_frame_count'],
        'scene_change_candidate_count': room_map['scene_change_candidate_count'],
        'video_motion_profile_path': 'video_motion_profile.json',
        'visual_odometry_path': 'visual_odometry.json',
        'arbitrary_scale_video_motion_edge_count': visual_odometry['supported_edge_count'],
        'continuous_region_segment_count': temporal['continuous_region_segment_count'],
        'metric_pose_hypotheses': registration.get('cross_view_consistent_hypotheses', []),
        'inferred_room_adjacency': [],
        'metric_registration': registration.get('accepted_camera_poses') or None,
        'metric_registration_hypotheses_path': 'cross_capture_registration.json',
        'opening_correspondence_hypotheses_path': 'opening_correspondences.json',
        'registered_openings_path': 'registered_openings.json',
        'room_transitions_path': 'room_transitions.json',
        'verified_crossings': transitions['verified_crossings'],
        'warnings': room_map['warnings']
    }
    graph_path = Path(run_dir)/'visual_room_graph.json'
    write_json(graph_path, graph)
    from .fused_plan import assemble_fused_plan
    fused, fused_artifacts = assemble_fused_plan(
        photo_dir, video_dir, lidar_dir, report, registration,
        opening_links, run_dir, registered_openings=registered_openings)
    return report, rgb_artifacts + [
        {'path': str(path), 'sha256': sha256(path)},
        {'path': str(registration_path), 'sha256': sha256(registration_path)},
        {'path': str(opening_path), 'sha256': sha256(opening_path)},
        {'path': str(temporal_path), 'sha256': sha256(temporal_path)},
        {'path': str(odometry_path), 'sha256': sha256(odometry_path)},
        {'path': str(registered_path), 'sha256': sha256(registered_path)},
        {'path': str(transitions_path), 'sha256': sha256(transitions_path)},
        {'path': str(graph_path), 'sha256': sha256(graph_path)}] + fused_artifacts
