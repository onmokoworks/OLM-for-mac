"""Fuzz RadialBlur around fixture-style conditions (use_aex_* tuples) against the original AEX.

Usage: tools/emulation/.venv/bin/python3 tools/refactor/fixture_fuzz_radialblur.py <run.py arguments>.
Reference implementation for the F-series tickets; adapt SLOT and the regex per plugin."""
import re, sys, random, runpy, glob, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
import adapters.radialblur as rb
from core import case_seed

SLOT = dict(blur_type=1, outer_strength=4, outer_offset_mode=5, outer_offset=6, outer_edge_fade=7,
            inner_strength=10, inner_offset_mode=11, inner_offset=12, inner_edge_fade=13, repeat_border=15,
            ratio=17, angle_deg=18, quality=20, brightness_gain=21, size_variation=22, noise_variation=24,
            noise_type=25, seed=27, thickness=29)
src = ''.join(open(f).read() for f in sorted(glob.glob(str(ROOT/'mac/OLMRadialBlur/*.inc'))))
flags = []
for m in re.finditer(r'const bool (use_aex_\w+) =(.*?);\n', src, re.S):
    body = m.group(2)
    eq = collections.defaultdict(set)
    for f, v in re.findall(r'info\.(\w+) == (-?[0-9.]+)', body):
        if f in SLOT: eq[f].add(float(v))
    sizes = set(re.findall(r'\bw == (\d+) && h == (\d+)', body)) | set(re.findall(r'input->width == (\d+) && input->height == (\d+)', body))
    flags.append((m.group(1), dict(eq), sorted((int(a), int(b)) for a, b in sizes) or [(9, 7), (32, 18)]))
print(f'{len(flags)} fixture conditions parsed', file=sys.stderr)

base_generate = rb.Adapter.generate
def generate(self, seed, index):
    rng = random.Random(case_seed(seed, index) ^ 0x5eed)
    name, eq, sizes = rng.choice(flags)
    w, h = rng.choice(sizes)
    case = base_generate(self, seed, index)  # pixel/padding/depth sampling from the stock generator
    params = self.defaults(w, h)
    for f, values in eq.items():
        p = next(p for p in params if p['slot'] == SLOT[f]); v = rng.choice(sorted(values))
        p['value'] = int(v) if p['kind'] in ('i', 'u', 'b') else v
    centre = next(p for p in params if p['kind'] == 'p')
    centre['value'] = [w/2, h/2] if rng.random() < .5 else [float(w//2), float(h//2)]
    raw = bytearray(case['pixels'][:0])
    import struct
    for _ in range(w*h):  # mostly opaque sources, as the fixtures assume
        if case['depth'] == 32:
            raw += struct.pack('<4f', 1.0 if rng.random() < .8 else rng.random(), rng.random(), rng.random(), rng.random())
        else:
            top = 255 if case['depth'] == 8 else 32768
            vals = [top if rng.random() < .8 else rng.randint(0, top), *[rng.randint(0, top) for _ in range(3)]]
            raw += struct.pack('<4B' if case['depth'] == 8 else '<4H', *vals)
    case.update(geometry=[w, h], parameters=params, pixels=bytes(raw), profile='sdr')
    case['fixture'] = name
    return case
rb.Adapter.generate = generate
sys.argv = [str(ROOT/'tools/fuzz/run.py')] + sys.argv[1:]
runpy.run_path(str(ROOT/'tools/fuzz/run.py'), run_name='__main__')
