"""Current production expectations; older capture epochs remain immutable."""
import json
from pathlib import Path

import probe_radialblur_public_aligned_20261001 as public

PATH = public.ROOT/'reports/radialblur_rotation_size_noise_public_20261001.json'


def capture():
    report = json.loads(PATH.read_text())
    assert public.sha(public.SOURCE.read_bytes()) == report['source_sha256']
    assert public.sha(public.SOURCE.with_suffix('.h').read_bytes()) == report['header_sha256']
    return report


def rows():
    return capture()['rows']


def keyed_rows():
    return {(r['group'], r['matrix'], r['row_index']): r for r in rows()}
