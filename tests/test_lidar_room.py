"""Controlled room-plane evidence tests without laser truth in inference."""

import unittest

from roomproof.lidar_room import fit_single_room


def rectangular_fixture(with_ceiling=True):
    points, horizontal, vertical = {}, [], []
    for frame_number in range(4):
        fid = f'{frame_number:06d}'
        points[fid] = []
        for i in range(30):
            for j in range(60):
                along = -1.5 + 3*j/59
                y = -1.1 + 2.2*i/29
                for x, nx in ((-2.0, -1.0), (2.0, 1.0)):
                    points[fid].append((x, y, along))
                    vertical.append((x, y, along, nx, 0.0, fid))
                for z, nz in ((-1.5, -1.0), (1.5, 1.0)):
                    points[fid].append(((-2+4*j/59), y, z))
                    vertical.append(((-2+4*j/59), y, z, 0.0, nz, fid))
                horizontal.append((-1.3, 1, fid))
                if with_ceiling:
                    horizontal.append((1.5, -1, fid))
    return points, horizontal, vertical


class RoomFitTests(unittest.TestCase):
    def test_supported_rectangle(self):
        fit = fit_single_room(*rectangular_fixture(), camera_y=0)
        self.assertEqual(fit['status'], 'inferred')
        self.assertAlmostEqual(fit['area_m2'], 12, delta=.5)
        self.assertAlmostEqual(fit['ceiling_height_m'], 2.8, places=2)
        self.assertEqual(len(fit['boundary_xz_m']), 4)

    def test_missing_ceiling_rejects_fit(self):
        fit = fit_single_room(*rectangular_fixture(with_ceiling=False), camera_y=0)
        self.assertEqual(fit['status'], 'unresolved')

    def test_opening_remains_unverified(self):
        points, horizontal, vertical = rectangular_fixture()
        for fid, cloud in points.items():
            points[fid] = [(x, y, z) for x, y, z in cloud
                           if not (x == 2.0 and abs(z) < .4 and y < .8)]
        fit = fit_single_room(points, horizontal, vertical, camera_y=0)
        self.assertEqual(fit['status'], 'inferred')
        self.assertTrue(fit['opening_gap_candidates'])
        self.assertTrue(all(item['status'] == 'unverified' for item in fit['opening_gap_candidates']))


if __name__ == '__main__':
    unittest.main()
