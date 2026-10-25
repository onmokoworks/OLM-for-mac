"""Offline checks of failure attribution; does not launch AE."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import numpy as np
import tifffile
import render_downsample

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/A02b-real-ae-retest-downsample'


class RenderTests(unittest.TestCase):
    def test_nonzero_exit_cannot_be_green_even_with_output(self):
        self.check(7, 'error')

    def test_transparent_rgb_is_flagged(self):
        self.check(0, 'black')

    def check(self, code, expected):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=SCRATCH) as directory:
            state = Path(directory)
            rgba = np.ones((2, 3, 4), dtype=np.uint8)
            rgba[:, :, 3] = 0
            tifffile.imwrite(state / 'frame_[00000].tif', rgba)
            data = {'projects': [{'path': 'project.aep', 'items': [
                {'outputPrefix': 'frame', 'queueIndex': 1, 'depth': 8}]}]}
            with patch.object(render_downsample.subprocess, 'run') as run:
                run.return_value.returncode = code
                render_downsample.render(state, data, Path('/AE/AE.app'), lambda _: None)
                self.assertIn('-rqindex', run.call_args.args[0])
                self.assertEqual(run.call_args.kwargs['env']['OLM_REFUSAL_TRACE'],
                                 str(state / 'frame.refusals.log'))
            row = json.loads((state / 'render-results.json').read_text())[0]
            self.assertEqual(row['status'], expected)


if __name__ == '__main__':
    unittest.main()
