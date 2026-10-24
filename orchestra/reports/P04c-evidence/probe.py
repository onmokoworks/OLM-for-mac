"""P04c: distinguish cropped checkout from F52c's full sampled input ROI.

No worker/source modification. The intentionally short raw input tests whether
the existing session can express a 7x5 checkout of a 14x10 layer at 1:1.
These are host-boundary witnesses, not an accepted pixel-exact corpus.
"""
import copy
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from adapters.olmsmoother2 import Adapter
from adapters.public import messages
from core import sha
from run import main_checkout

scratch = ROOT / 'orchestra/state/P04c-smoother2-checkout-negotiation/probe'
scratch.mkdir(parents=True, exist_ok=True)
adapter = Adapter(SimpleNamespace(main=main_checkout(), worker=Path.home() /
    '.cache/olm-emu/worker-F52c-geom/aex-guest-worker', max_size=16, case_timeout=10))
adapter.env.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
case = adapter.generate(1, 0)
case.update(geometry=[14, 10], depth=8, parameters=adapter.defaults(14, 10),
    pixels=bytes([255, 32, 64, 128])*140, geometry_sampler='realistic-v1',
    full_geometry=[14, 10], downsample=[[1, 1], [1, 1]], rowbytes_padding=0,
    extent_hint=[0, 0, 14, 10], request_rect=[0, 0, 14, 10], pixel_aspect=[1, 1])
rows = []
for label, changes in [
    ('full-control', {}),
    ('cropped-checkout-unrepresentable', dict(geometry=[7, 5],
        pixels=bytes([255, 32, 64, 128])*35, extent_hint=[0, 0, 7, 5],
        request_rect=[0, 0, 7, 5])),
    ('full-input-cropped-extent-request', dict(extent_hint=[0, 0, 7, 5],
        request_rect=[0, 0, 7, 5])),
    ('half-downsample-control', dict(geometry=[7, 5],
        pixels=bytes([255, 32, 64, 128])*35, downsample=[[1, 2], [1, 2]],
        extent_hint=[0, 0, 7, 5], request_rect=[0, 0, 7, 5])),
]:
    current = copy.deepcopy(case)
    current.update(changes)
    observed = []
    def observe(out, err):
        observed.append(dict(messages=messages(out), stderr=err.decode(errors='replace')))
    adapter.session_observed = observe
    result, raw = adapter.oracle(current, scratch, time.monotonic()+20, 'smart')
    rows.append(dict(label=label, case={k:v for k,v in current.items() if k!='pixels'},
        input_bytes=len(current['pixels']), input_sha256=sha(current['pixels']),
        result=result, output_bytes=len(raw), output_sha256=sha(raw), observed=observed))
    print(label, result, len(raw), flush=True)
record = dict(label='P04c host-boundary witness set; not pixel acceptance',
    worker=str(adapter.worker), worker_sha256=sha(adapter.worker.read_bytes()),
    aex=str(adapter.aex), aex_sha256=sha(adapter.aex.read_bytes()), rows=rows)
(scratch/'results.json').write_text(json.dumps(record, indent=2)+'\n')
assert [r['result']['status'] for r in rows] == ['ok', 'reject', 'reject', 'ok']
assert [r['output_bytes'] for r in rows] == [560, 0, 0, 140]
assert '140 bytes, expected 560' in rows[1]['result']['diagnostic']
assert 'result=[0, 0, 7, 5] max=[0, 0, 14, 10] flags=0' in rows[2]['result']['diagnostic']
assert '0x180022410' in rows[2]['result']['diagnostic']
