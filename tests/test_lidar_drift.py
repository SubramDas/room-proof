"""Small controlled geometry cases for the optional LiDAR loop constraint."""

import random
import unittest

from roomproof.lidar_geometry import _closure_constraint, _drift_ablation, project


class LidarDriftTests(unittest.TestCase):
    def test_depth_projection_units_and_camera_axes(self):
        pose = {'translation_m': [0, 0, 0], 'quaternion_xyzw': [0, 0, 0, 1]}
        intrinsics = {'fx': 960, 'fy': 720, 'cx': 960, 'cy': 720}
        point = project(127.5, 95.5, 2000, intrinsics, (256, 192), pose)
        self.assertEqual(point, (0, 0, 2))

    def test_verified_revisit_changes_footprint_only_when_enabled(self):
        rng = random.Random(4)
        first = [(rng.random()*2, rng.random()*2, rng.random()*2) for _ in range(900)]
        second = [(x+.05, y, z) for x, y, z in first]
        constraint = _closure_constraint(first, second)
        self.assertIsNotNone(constraint)
        self.assertAlmostEqual(constraint['translation_m'][0], -.05)
        self.assertLessEqual(constraint['overlap_fraction'], 1.0)
        frames = [
            {'frame_id': '000000', 'pose': {'timestamp_seconds': 0, 'translation_m': [0, 0, 0],
                                            'quaternion_xyzw': [0, 0, 0, 1]}},
            {'frame_id': '000100', 'pose': {'timestamp_seconds': 25, 'translation_m': [.05, 0, 0],
                                            'quaternion_xyzw': [0, 0, 0, 1]}},
        ]
        points = {'000000': first, '000100': second}
        raw, off = _drift_ablation(frames, points, False)
        corrected, on = _drift_ablation(frames, points, True)
        self.assertEqual(raw, first+second)
        self.assertIsNone(off['applied_constraint'])
        self.assertIsNotNone(on['applied_constraint'])
        self.assertAlmostEqual(corrected[len(first)][0], first[0][0], places=5)

    def test_disjoint_surfaces_do_not_trigger_closure(self):
        rng = random.Random(7)
        first = [(rng.random(), rng.random(), rng.random()) for _ in range(900)]
        second = [(x+2, y, z) for x, y, z in first]
        self.assertIsNone(_closure_constraint(first, second))

    def test_single_plane_cannot_trigger_translation(self):
        rng = random.Random(8)
        first = [(rng.random()*2, rng.random()*2, 0.0) for _ in range(900)]
        second = [(x+.05, y, z) for x, y, z in first]
        self.assertIsNone(_closure_constraint(first, second))


if __name__ == '__main__':
    unittest.main()
