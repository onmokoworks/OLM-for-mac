"""Serial one-item aerender invocations with attributable traces and wall timings."""
import hashlib
import json
import os
import subprocess
import time
import numpy as np
import tifffile


def render(state, data, app, preflight):
    results = []
    for project in data['projects']:
        for item in project['items']:
            preflight(state)
            prefix = item['outputPrefix']
            trace = state / (prefix + '.refusals.log')
            logpath = state / (prefix + '.aerender.log')
            env = dict(os.environ, OLM_REFUSAL_TRACE=str(trace))
            start = time.monotonic()
            with logpath.open('w') as log:
                proc = subprocess.run([str(app.parent / 'aerender'), '-project', project['path'],
                                       '-rqindex', str(item['queueIndex']), '-mfr', 'OFF'],
                                      env=env, stdout=log, stderr=subprocess.STDOUT)
            row = dict(item, returncode=proc.returncode, wall_seconds=time.monotonic()-start,
                       timing_scope='one frame plus aerender startup',
                       refusals=trace.read_text() if trace.exists() else '')
            paths = list(state.glob(prefix + '_*.tif'))
            row['output_count'] = len(paths)
            row['status'] = 'error'
            if proc.returncode == 0 and len(paths) == 1:
                rgba = tifffile.imread(paths[0])
                row.update(shape=list(rgba.shape), dtype=str(rgba.dtype),
                           output_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                           all_black=bool(np.all(rgba[:, :, :3] == 0)),
                           all_transparent=bool(np.all(rgba[:, :, 3] == 0)))
                row['status'] = 'black' if row['all_black'] or row['all_transparent'] else 'OK'
            results.append(row)
            (state / 'render-results.json').write_text(json.dumps(results, indent=2) + '\n')
