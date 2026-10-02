"""Build an evidence graph from opening tracks and the full video timeline.

The graph does not turn a scene cut, room-folder name, or image match into a
physical doorway. Those signals are useful for prioritizing verification.
"""

import re


_FRAME = re.compile(r'#frame=(\d+)$')


def _video_index(source_ref):
    match = _FRAME.search(source_ref)
    return int(match.group(1)) if match else None


def build_visual_room_map(records, opening_links, profile, room_labels,
                          temporal=None):
    observations = {}
    for pair in records:
        for side in ('left', 'right'):
            tier = pair[f'{side}_tier']
            source_ref = pair[f'{side}_source_ref']
            for candidate in pair[f'{side}_opening_proposals']:
                observations[candidate['candidate_id']] = {
                    'candidate_id': candidate['candidate_id'],
                    'tier': tier, 'source_ref': source_ref,
                    'room_label': pair.get(f'{side}_room_label'),
                    'video_frame_index': _video_index(source_ref) if tier == 'video' else None,
                    'class': candidate['class'],
                    'box': candidate['geometry']['xyxy_px'],
                    'image_size': pair[f'{side}_image_size'],
                }
    scene_indices = [item['source_frame_index']
                     for item in profile.get('scene_change_candidates', [])]
    tracks, transitions, connections = [], [], []
    temporal_segments = (temporal or {}).get('opening_track_segments', [])
    for number, group in enumerate(opening_links['groups'], 1):
        members = [observations[cid] for cid in group['candidate_ids'] if cid in observations]
        video = sorted({item['video_frame_index'] for item in members
                        if item['video_frame_index'] is not None})
        photo_labels = sorted({item['room_label'] for item in members
                               if item['tier'] == 'photo' and item['room_label']})
        scan_refs = sorted({item['source_ref'] for item in members if item['tier'] == 'scan_rgb'})
        track_id = f'opening-track-{number}'
        continuity = [segment for segment in temporal_segments
                      if segment['opening_track_group_index'] == number and
                      segment['status'] == 'image_region_continuity_hypothesis']
        tracks.append({
            'id': track_id, 'candidate_ids': group['candidate_ids'],
            'source_refs': group['source_refs'], 'video_frame_indices': video,
            'photo_room_labels': photo_labels, 'scan_rgb_source_refs': scan_refs,
            'edge_count': group['edge_count'],
            'continuous_video_segment_count': len(continuity),
            'status': 'image_region_track_unverified',
        })
        if len(video) >= 2:
            nearby_changes = [index for index in scene_indices
                              if video[0]-15 <= index <= video[-1]+15]
            transitions.append({
                'opening_track_id': track_id,
                'video_frame_range': [video[0], video[-1]],
                'scene_change_frame_indices': nearby_changes,
                'status': 'possible_crossing_needs_camera_trajectory' if nearby_changes and continuity
                          else 'tracked_opening_without_crossing_evidence',
                'reason': ('Appearance changes and opening sightings do not prove the '
                           'camera crossed a wall plane; no calibrated video trajectory exists.'),
                'source_refs': sorted({item['source_ref'] for item in members if item['tier'] == 'video'}),
            })
        if len(photo_labels) >= 2:
            connections.append({
                'opening_track_id': track_id, 'room_label_hypotheses': photo_labels,
                'status': 'unverified_two_sided_view_hypothesis',
                'reason': 'Image-region matches and supplied photo folder labels do not verify adjacency.',
                'source_refs': group['source_refs'],
            })
    return {
        'report_version': '0.1.0', 'status': 'visual_hypotheses_only',
        'room_labels_by_capture': room_labels,
        'full_video_frame_count': profile.get('sample_count', 0),
        'scene_change_candidate_count': len(scene_indices),
        'opening_tracks': tracks,
        'transition_hypotheses': transitions,
        'room_connection_hypotheses': connections,
        'inferred_room_adjacency': [],
        'warnings': [
            'Opening tracks are image-region correspondences; overlapping boxes may merge distinct features.',
            'No room connection is accepted without a verified crossing and physical opening identity.',
        ],
    }
