"""Serial one-item aerender invocations with attributable traces and wall timings."""
import hashlib
import json
import os
import subprocess
import time
import numpy as np
import tifffile


def render(state, data, app, preflight):
    from ae_dialog_watch.watcher import prepare_launch
    from ae_dialog_watch.prefs import scripting_prefs
    from run_ae_smoke import wait_unlocked, running
    results_path = state / 'render-results.json'
    results = json.loads(results_path.read_text()) if results_path.exists() else []
    if any(row['status'] == 'error' for row in results):
        raise RuntimeError('Prior render error requires investigation and a fresh run ID')
    completed = {row['outputPrefix'] for row in results}
    for project in data['projects']:
        for item in project['items']:
            if item['outputPrefix'] in completed:
                continue
            if (state / 'stop').exists():
                raise RuntimeError('Cooperative stop requested between frames')
            preflight(state)
            wait_unlocked(state)
            preflight(state)
            prefix = item['outputPrefix']
            extension = item.get('outputExtension', 'exr' if item['depth'] == 32 else 'tif')
            trace = state / (prefix + '.refusals.log')
            logpath = state / (prefix + '.aerender.log')
            env = dict(os.environ, OLM_REFUSAL_TRACE=str(trace))
            lifecycle = state / (prefix + '.lifecycle')
            prepare_launch(lifecycle / 'prevention')
            scripting_prefs(lifecycle / 'prefs')
            start = time.monotonic()
            try:
                with logpath.open('w') as log:
                    proc = subprocess.run([str(app.parent / 'aerender'), '-project', project['path'],
                                       '-rqindex', str(item['queueIndex']), '-mfr', 'OFF', '100',
                                       '-output', str(state / (prefix + '_[#####].' + extension))],
                                      env=env, stdout=log, stderr=subprocess.STDOUT)
                elapsed = time.monotonic() - start
            finally:
                scripting_prefs(lifecycle / 'prefs', restore=True)
            if running():
                raise RuntimeError('AE main executable remains after aerender; stop')
            row = dict(item, returncode=proc.returncode, wall_seconds=elapsed,
                       timing_scope='one frame plus aerender startup',
                       refusals=trace.read_text() if trace.exists() else '')
            paths = list(state.glob(prefix + '_*.' + extension))
            row['output_count'] = len(paths)
            row['status'] = 'error'
            if proc.returncode == 0 and len(paths) == 1:
                if extension == 'exr':
                    import OpenEXR
                    channels = OpenEXR.File(str(paths[0]), separate_channels=True).channels()
                    if any(channels[c].pixels.dtype != np.float32 for c in 'RGBA'):
                        raise ValueError('32 bpc output requires FLOAT EXR channels')
                    rgba = np.stack([channels[c].pixels for c in 'RGBA'], axis=-1)
                elif extension == 'png':
                    from PIL import Image
                    with Image.open(paths[0]) as image:
                        if image.mode != 'RGBA':
                            raise ValueError('RGBA PNG required')
                        rgba = np.array(image)
                else:
                    rgba = tifffile.imread(paths[0])
                row.update(shape=list(rgba.shape), dtype=str(rgba.dtype),
                           output_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                           all_black=bool(np.all(rgba[:, :, :3] == 0)),
                           all_transparent=bool(np.all(rgba[:, :, 3] == 0)))
                row['status'] = 'black' if row['all_black'] or row['all_transparent'] else 'OK'
            results = [r for r in results if r['outputPrefix'] != prefix]
            results.append(row)
            (state / 'render-results.json').write_text(json.dumps(results, indent=2) + '\n')
            if row['status'] == 'error':
                raise RuntimeError('Render failed; stop before next frame: ' + prefix)
