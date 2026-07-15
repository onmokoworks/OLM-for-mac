# OLMBlur case_0006 worker probe return 2026-07-15

## Verdict

`RETURN_OLMBLUR_CASE0006_WORKER_PROBE_20260715_0015.zip` is accepted as
same-run Windows AE export provenance, but not as an OLMBlur worker/internal
trace.

## Facts

- Return archive:
  `refs/windows_returns/20260715/20260715_145700__RETURN__OLMBLUR_CASE0006_WORKER_PROBE/RETURN_OLMBLUR_CASE0006_WORKER_PROBE_20260715_0015.zip`
- Return archive SHA-256:
  `9202f027852b46594bf9c4fe37375d1e1bae86e268437612bb589bc4834e1864`
- Windows AE reported:
  - `ae_version`: `25.2x131`
  - `project_bits_per_channel`: `16`
  - `project_working_space`: `None`
  - `project_linear_blending`: `false`
  - `status`: `ok`
- Rendered export:
  `export/case_0006.png`
- Export PNG SHA-256:
  `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`

The export PNG is byte-identical to both retained Windows references:

| Compared artifact | Result |
| --- | --- |
| `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `max=0`, byte-identical |
| `refs/win_references/olmblur_case0006_current_aex_export_20260709/OLMBlur/olmblur_case0006_current_aex_export_20260709__software_16bpc_current_aex_export__fr24__olmblur__case_0006.png` | `max=0`, byte-identical |

The latest retained Mac single-case output still differs from this Windows
export by one 8-bit PNG code at one pixel:

| Compared artifact | Result |
| --- | --- |
| `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `max=1`, `nz_px=1`; first differing pixel `(601,598)`, Windows `[18,18,18,255]`, Mac `[17,17,18,255]` |

## Worker probe classification

The return's `worker_process_monitor.log` did observe an
`aex_smart_worker.exe` process, but the command line contained
`RefractionDispersion.aex`, not `OLMBlur.aex`. Therefore this return does not
bind an OLMBlur smart-worker lane and must not be used as internal OLMBlur
worker proof.

Earlier feedback in the same exchange also showed that attaching CDB to AE2025
causes the render to fail even with no breakpoints. Further CDB-based OLMBlur
case_0006 retries are not useful unless the attach mechanism itself changes.

## Consequence

This return closes the repeated Windows export-provenance question for
`olmblur__case_0006`: the current Windows AE2025 direct UI export, the retained
2026-07-09 current-AEX export, and the canonical 2026-06-25 16bpc Software
reference are the same PNG bytes.

The remaining OLMBlur case_0006 issue is Mac-side or live-context/internal
ownership, not stale Windows reference provenance. Do not request another
plain Windows export for this case. If reopened, the next evidence must be a
different internal observation mechanism that can bind OLMBlur specifically
without CDB attach side effects.

## Verification command

```sh
python3 - <<'PY'
from pathlib import Path
from PIL import Image
import hashlib
import numpy as np

paths = [
    ('new', Path('/tmp/olmblur_worker_probe_20260715/export/case_0006.png')),
    ('canonical_20260625', Path('refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png')),
    ('current_20260709', Path('refs/win_references/olmblur_case0006_current_aex_export_20260709/OLMBlur/olmblur_case0006_current_aex_export_20260709__software_16bpc_current_aex_export__fr24__olmblur__case_0006.png')),
    ('mac_latest_single', Path('refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png')),
]

base = Image.open(paths[0][1])
for label, path in paths:
    data = path.read_bytes()
    print(label, hashlib.sha256(data).hexdigest(), Image.open(path).size, Image.open(path).mode)

for label, path in paths[1:]:
    image = Image.open(path)
    a = np.array(base)
    b = np.array(image)
    diff = np.abs(a.astype(np.int64) - b.astype(np.int64))
    nz = np.count_nonzero(np.any(diff != 0, axis=2))
    print(label, int(diff.max()), int(nz), float(diff.mean()))
PY
```
