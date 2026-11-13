"""Bounded round-two original oracle, including sparse/band-boundary witnesses.
Usage: python qualify.py OUT STAGED
Artifacts are retained for the director to compact; this script never deletes.
"""
from pathlib import Path
import json, sys
root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / 'rust/tools/oracle'))
import olm_oracle as o
out, staged = map(Path, sys.argv[1:3])
reference = Path(r'D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMToonDilate.aex')
generate, pixels = o.generate_cases, o.input_pixels
reports = []
for seed in [20261123, 20261124, 20261125]:
    targeted = seed == 20261125
    def plans(parameters, count, seed, sizes, downsample):
        cases = generate(parameters, count, seed, sizes, downsample)
        if targeted:
            for i, c in enumerate(cases):
                c['assignments'] = [{'slot': 1, 'value': [1, 2, 8, 100][i // 6]}]
                c['untouched_defaults'] = []
                c['input_seed'] = i
                c['pattern'] = ['no seeds', 'all seeds', 'one central seed', 'two competing seeds', 'band boundary seeds', 'sparse grid'][i % 6]
        return cases
    def image(w, h, seed):
        a = pixels(w, h, seed)
        if targeted:
            a[..., 3] = 128
            mode = seed % 6
            if mode == 1: a[..., 3] = 255
            elif mode == 2: a[h//2, w//2, 3] = 255
            elif mode == 3:
                a[h//2, max(0,w//2-1), 3] = 255
                a[h//2, min(w-1,w//2+1), 3] = 255
            elif mode == 4:
                for y in [127,128,134,135,255,256,269,270,399,400]:
                    if y<h: a[y, (y*31)%w, 3] = 255
            elif mode == 5: a[::97, ::31, 3] = 255
        return a
    o.generate_cases, o.input_pixels = plans, image
    dest = out / str(seed)
    code = o.main(['render', '--reference', str(reference), '--candidate', str(staged/'OLMToonDilate.aex'), '--out', str(dest), '--cases', '24' if targeted else '53', '--seed', str(seed), '--jobs', '2', '--routes', 'smart8,smart16,smart32', '--downsample', '1,1/2,1/4', '--sizes', '257x259,13x541,1x541' if targeted else '1x1,3x7,11x7,31x19,257x259', '--timeout', '120', '--resident'])
    reports.append({'seed':seed,'targeted':targeted,'exit':code,'summary':str(dest/'summary.json')})
    (out/'campaign.json').write_text(json.dumps(reports,indent=2))
    if code: raise SystemExit(code)
