"""Low-resolution motion and opening-region continuity over every video frame."""

from collections import defaultdict

import cv2
import numpy as np


def _box(candidate, size):
    x0, y0, x1, y1 = candidate['geometry']['xyxy_px']
    width, height = candidate['geometry']['image_width'], candidate['geometry']['image_height']
    return (x0*size[0]/width, y0*size[1]/height,
            x1*size[0]/width, y1*size[1]/height)


def _seed(gray, box):
    x0, y0, x1, y1 = box
    mask = np.zeros(gray.shape, np.uint8)
    h, w = gray.shape
    cv2.rectangle(mask, (max(0, int(x0)), max(0, int(y0))),
                  (min(w-1, int(x1)), min(h-1, int(y1))), 255, -1)
    return cv2.goodFeaturesToTrack(gray, maxCorners=40, qualityLevel=.015,
                                   minDistance=4, mask=mask)


def trace_video(video_path, video_index, opening_groups, records):
    """Track candidate texture between selected model frames, without metric pose."""
    frame_by_ref = {}
    for pair in records:
        for side in ('left', 'right'):
            if pair[f'{side}_tier'] != 'video':
                continue
            ref = pair[f'{side}_source_ref']
            index = pair.get(f'{side}_source_frame_index')
            if index is None:
                continue
            for candidate in pair[f'{side}_opening_proposals']:
                frame_by_ref[candidate['candidate_id']] = (index, candidate, ref)
    starts = defaultdict(list)
    segments = []
    for group_index, group in enumerate(opening_groups['groups'], 1):
        views = sorted((frame_by_ref[cid] for cid in group['candidate_ids']
                        if cid in frame_by_ref), key=lambda item: item[0])
        for first, second in zip(views, views[1:]):
            if second[0] <= first[0] or second[0]-first[0] > 180:
                continue
            entry = {'opening_track_group_index': group_index,
                     'start_frame_index': first[0], 'end_frame_index': second[0],
                     'start_source_ref': first[2], 'end_source_ref': second[2],
                     'first_candidate': first[1], 'second_candidate': second[1],
                     'status': 'pending', 'tracked_frame_count': 0}
            starts[first[0]].append(entry)
            segments.append(entry)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f'cannot decode standalone video for temporal tracking: {video_path}')
    previous = None
    global_points = None
    motion = []
    active = []
    index = 0
    target_width = 240
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        size = (target_width, max(1, round(h*target_width/w)))
        gray = cv2.cvtColor(cv2.resize(frame, size), cv2.COLOR_BGR2GRAY)
        if previous is not None:
            if global_points is None or len(global_points) < 12:
                global_points = cv2.goodFeaturesToTrack(previous, maxCorners=90,
                                                        qualityLevel=.025, minDistance=5)
            if global_points is not None and len(global_points):
                next_points, valid, _ = cv2.calcOpticalFlowPyrLK(previous, gray, global_points, None)
                good = valid.ravel().astype(bool) if valid is not None else np.zeros(len(global_points), bool)
                if next_points is not None and good.sum() >= 6:
                    flow = next_points[good, 0]-global_points[good, 0]
                    median = np.median(flow, axis=0)
                    motion.append({'source_frame_index': index,
                                   'tracked_feature_count': int(good.sum()),
                                   'median_image_flow_px': [round(float(value), 3) for value in median],
                                   'status': '2d_motion_only'})
                    global_points = next_points[good].reshape(-1, 1, 2)
                else:
                    motion.append({'source_frame_index': index, 'tracked_feature_count': 0,
                                   'median_image_flow_px': None, 'status': 'track_break'})
                    global_points = None
            else:
                motion.append({'source_frame_index': index, 'tracked_feature_count': 0,
                               'median_image_flow_px': None, 'status': 'track_break'})
        else:
            motion.append({'source_frame_index': index, 'tracked_feature_count': 0,
                           'median_image_flow_px': None, 'status': 'first_frame'})
        for segment in starts.get(index, []):
            segment['points'] = _seed(gray, _box(segment['first_candidate'], size))
            segment['status'] = 'tracking' if segment['points'] is not None and len(segment['points']) >= 6 else 'insufficient_texture'
            if segment['status'] == 'tracking':
                active.append(segment)
        for segment in list(active):
            if index > segment['start_frame_index']:
                next_points, valid, _ = cv2.calcOpticalFlowPyrLK(
                    previous, gray, segment['points'], None)
                good = valid.ravel().astype(bool) if valid is not None else np.zeros(len(segment['points']), bool)
                if next_points is None or good.sum() < 6:
                    segment['status'] = 'track_break'; active.remove(segment); continue
                segment['points'] = next_points[good].reshape(-1, 1, 2)
                segment['tracked_frame_count'] += 1
            if index == segment['end_frame_index']:
                x0, y0, x1, y1 = _box(segment['second_candidate'], size)
                xy = segment['points'][:, 0]
                inside = ((xy[:, 0] >= x0) & (xy[:, 0] <= x1) &
                          (xy[:, 1] >= y0) & (xy[:, 1] <= y1))
                segment['ending_feature_count'] = len(xy)
                segment['ending_box_feature_fraction'] = round(float(inside.mean()), 3)
                segment['status'] = ('image_region_continuity_hypothesis' if
                                     len(xy) >= 8 and inside.mean() >= .35 else
                                     'inconsistent_with_next_box')
                active.remove(segment)
        previous = gray
        index += 1
    capture.release()
    for segment in active:
        segment['status'] = 'video_ended_before_next_sighting'
    for segment in segments:
        segment.pop('points', None)
        segment.pop('first_candidate', None)
        segment.pop('second_candidate', None)
    return {'report_version': '0.1.0', 'status': '2d_motion_and_region_tracks_only',
            'decoded_frame_count': index,
            'indexed_source_frame_count': video_index.get('source_frame_count'),
            'low_resolution_width': target_width,
            'motion_frames': motion,
            'opening_track_segments': segments,
            'continuous_region_segment_count': sum(item['status'] ==
                                                    'image_region_continuity_hypothesis'
                                                    for item in segments),
            'warnings': ['Optical flow follows image texture, not a physical wall plane or metric camera trajectory.']}
