"""Current production expectations; older capture epochs remain immutable."""
import json
from pathlib import Path
import subprocess

import probe_radialblur_public_aligned_20261001 as public

PATH = public.ROOT/'reports/radialblur_seed_thickness_public_20261002.json'


def capture():
    report = json.loads(PATH.read_text())
    assert public.sha(public.SOURCE.read_bytes()) == report['source_sha256']
    assert public.sha(public.SOURCE.with_suffix('.h').read_bytes()) == report['header_sha256']
    assert public.sha((public.ROOT/'core/dblur_noise.h').read_bytes()) == report['core_sha256']
    return report


def rows():
    return capture()['rows']


def keyed_rows():
    return {(r['group'], r['matrix'], r['row_index']): r for r in rows()}


def historical_dependency_sha256(relative_path):
    """Bind old captures to their core epoch while checking the live core separately.

    All archived RadialBlur captures through a79c54d2 used this same core.
    Production replays compile the actual core and compare the archived outputs.
    """
    if relative_path == 'core/dblur_noise.h':
        capture()
        data = subprocess.check_output(['git', 'show',
            'a79c54d2df1e14e5fea585eb6fc77dad421bca42:'+relative_path], cwd=public.ROOT)
    else:
        data = (public.ROOT/relative_path).read_bytes()
    return public.sha(data)
