"""Optional local ALIKED/LightGlue matching with image-space verification.

The resulting correspondences are still 2D evidence, never metric placement.
Weights and the upstream source live outside Git in .room-proof/models.
"""

import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np
import torch


class ALIKEDMatcher:
    def __init__(self, model_root='.room-proof/models', max_keypoints=512):
        root = Path(model_root).resolve()
        source = root/'LightGlue'
        cache = root/'torch-hub'/'checkpoints'
        required = [cache/'aliked-n16.pth', cache/'aliked_lightglue_v0-1_arxiv.pth']
        if not source.is_dir() or any(not path.is_file() for path in required):
            raise FileNotFoundError('ALIKED/LightGlue source or pinned local weights are missing; see docs/dependencies.md')
        sys.path.insert(0, str(source))
        torch.hub.set_dir(str(root/'torch-hub'))
        from lightglue import ALIKED, LightGlue
        torch.set_num_threads(min(torch.get_num_threads(), 4))
        self.extractor = ALIKED(model_name='aliked-n16', max_num_keypoints=max_keypoints).eval()
        self.matcher = LightGlue(features='aliked').eval()
        self.provenance = {
            'method': 'ALIKED-n16 + LightGlue; fundamental-matrix RANSAC; CPU',
            'source_revision': (source/'.git').exists() and _git_revision(source),
            'max_keypoints': max_keypoints,
            'weights': {path.name: _sha256(path) for path in required},
            'torch_version': torch.__version__, 'opencv_version': cv2.__version__,
        }

    def extract(self, rgb, width, height):
        image = np.frombuffer(rgb, np.uint8).reshape(height, width, 3).copy()
        tensor = torch.from_numpy(image).permute(2, 0, 1).float().div_(255)
        with torch.inference_mode():
            return self.extractor.extract(tensor, resize=640)

    def compare(self, left, right, left_size, right_size):
        with torch.inference_mode():
            result = self.matcher({'image0': left, 'image1': right})
        pairs = result['matches0'][0].cpu().numpy()
        indexes = np.flatnonzero(pairs >= 0)
        if len(indexes) < 8:
            return _empty(len(indexes))
        points_a = left['keypoints'][0, indexes].cpu().numpy().astype(np.float64)
        points_b = right['keypoints'][0, pairs[indexes]].cpu().numpy().astype(np.float64)
        # Normalize each image to a 640-pixel long side for a size-independent
        # RANSAC threshold. A fundamental matrix admits camera motion and depth.
        norm_a = 640/max(left_size); norm_b = 640/max(right_size)
        sample_a = points_a*norm_a; sample_b = points_b*norm_b
        matrix, mask = cv2.findFundamentalMat(sample_a, sample_b, cv2.FM_RANSAC, 2.5, .999, 3000)
        if matrix is None or matrix.shape != (3, 3) or mask is None:
            return _empty(len(indexes))
        valid = mask.reshape(-1).astype(bool)
        inliers = int(valid.sum())
        fraction = inliers/len(indexes)
        # Spread is measured separately on both images. Local cabinet texture
        # cannot establish a reliable whole-view correspondence by itself.
        def spread(points, size):
            if not len(points):
                return 0
            cells = {(min(3, int(4*p[0]/size[0])), min(3, int(4*p[1]/size[1]))) for p in points}
            return len(cells)
        cells_a = spread(points_a[valid], left_size)
        cells_b = spread(points_b[valid], right_size)
        supported = inliers >= 12 and fraction >= .35 and cells_a >= 3 and cells_b >= 3
        coordinates = [
            {'left_xy': [round(float(x), 2) for x in pa],
             'right_xy': [round(float(x), 2) for x in pb]}
            for pa, pb in zip(points_a[valid][:160], points_b[valid][:160])]
        return {'matches': len(indexes), 'inliers': inliers,
                'inlier_fraction': round(fraction, 3),
                'overlap_supported': supported, 'motion_model': 'fundamental_matrix',
                'apparent_shift_px': None, 'inlier_cells': [cells_a, cells_b],
                'inlier_coordinates': coordinates if supported else [],
                'verification': '2D epipolar agreement only; no metric transform'}


def _empty(matches):
    return {'matches': matches, 'inliers': 0, 'inlier_fraction': 0,
            'overlap_supported': False, 'motion_model': 'fundamental_matrix',
            'apparent_shift_px': None, 'inlier_cells': [0, 0],
            'inlier_coordinates': [], 'verification': 'insufficient 2D matches'}


def _sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision(path):
    import subprocess
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
