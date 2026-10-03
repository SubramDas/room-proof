"""Regression checks for a Stray export with one leading depth frame."""

import unittest
from unittest.mock import patch

from roomproof.lidar_rgb import _assess_registration


class LiDARRGBPairingTests(unittest.TestCase):
    def test_verified_offset_recovers_full_timed_sequence(self):
        frames = [{"frame_id": f"{i:06d}", "pose": {"timestamp_seconds":
                   0.0 if i == 0 else .016 + (i - 1) * .025}}
                  for i in range(16)]
        missing_initial_matches = {2, 5, 8, 11}
        links = [{"rgb_frame_index": i, "relative_time_seconds": i * .025,
                  "depth_frame_id": None if i in missing_initial_matches else f"{i:06d}",
                  "status": "unpaired" if i in missing_initial_matches else "timing_candidate"}
                 for i in range(15)]
        pairing = {"links": links, "max_timing_residual_seconds": .008}
        samples = [{"rgb_frame_index": i} for i in range(15)]
        strong = {"rgb_edge_at_depth_boundary": 10.0,
                  "shifted_control_edge": 2.0, "boundary_pixels": 200}
        weak = {"rgb_edge_at_depth_boundary": 3.0,
                "shifted_control_edge": 2.0, "boundary_pixels": 200}
        with patch("roomproof.lidar_rgb._edge_scores", return_value={0: weak, 1: strong}):
            _assess_registration(None, {"frames": frames}, pairing, samples)

        self.assertEqual(pairing["timing_candidate_count"], 15)
        self.assertEqual(pairing["unpaired_rgb_count"], 0)
        self.assertEqual(pairing["registered_sampled_frame_count"], 11)
        self.assertEqual(pairing["links"][0]["depth_frame_id"], "000001")
        self.assertEqual(pairing["links"][-1]["depth_frame_id"], "000015")


if __name__ == "__main__":
    unittest.main()
