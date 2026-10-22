#!/usr/bin/env python3
"""Run reproducible C11 admission experiments using scratch-only source copies.

Remaining arguments are forwarded to run.py. The oracle is never modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess

sys.dont_write_bytecode = True
from adapters.radialblur import public
import run

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', choices=('centers', 'centers-radius', 'finite', 'finite-zoom', 'negative-noise', 'negative-noise-integer'), required=True)
    parser.add_argument('--experiment-directory', type=Path, required=True)
    parser.add_argument('--revision', help='Read source at a revision without modifying the checkout')
    parser.add_argument('--snapshot-only', action='store_true')
    args, forwarded = parser.parse_known_args()
    out = args.experiment_directory.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C11-radial-smart-r2')
    out.mkdir(parents=True, exist_ok=True)
    source = (subprocess.check_output(['git','show',args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT).decode()
              if args.revision else public.SOURCE.read_text())
    if args.experiment.startswith('centers'):
        old = ('\t\tinfo.center_x >= 0.0 && info.center_x <= (PF_FpLong)input->width &&\n'
               '\t\tinfo.center_y >= 0.0 && info.center_y <= (PF_FpLong)input->height &&\n')
        new = ''
    elif args.experiment.startswith('negative-noise'):
        old = 'info.noise_offset < 0.0f ||'
        new = 'info.noise_offset < RadialNoiseOffsetRadians(std::numeric_limits<PF_Fixed>::min()) ||'
        core = (subprocess.check_output(['git','show',args.revision+':core/dblur_noise.h'],cwd=ROOT).decode()
                if args.revision else (ROOT/'core/dblur_noise.h').read_text())
        pos = core.index('inline bool generate_radial_noise_plane(')
        prefix, radial = core[:pos], core[pos:]
        marker = '        const int table_index = static_cast<int>(table_position);'
        assert radial.count(marker) == 1
        radial = radial.replace(marker, marker+'\n        if (table_index < 0 || table_index >= 100) return false;')
        header = out/'dblur_noise.h'
        header.write_text(prefix+radial)
        source = source.replace('#include "../../core/dblur_noise.h"', '#include "'+str(header)+'"')
        (out/'core-binding.json').write_text(json.dumps(dict(
            original_sha256=hashlib.sha256(core.encode()).hexdigest(),
            candidate_sha256=hashlib.sha256(header.read_bytes()).hexdigest()), indent=2)+'\n')
        if args.experiment == 'negative-noise-integer':
            marker = '\tsize_t rgba_words = 0;'
            assert source.count(marker) == 1
            source = source.replace(marker,
                '\tif constexpr (std::is_same<PixelT, PF_PixelFloat>::value) {\n'
                '\t\tif (info.noise_variation != 0.0 && info.noise_offset < 0.0f) return false;\n'
                '\t}\n'+marker)
    else:
        old = 'GenericRadialInputIsSDR<PF_PixelFloat>(input);'
        new = ('(info.blur_type == 1 ? GenericRadialInputIsFinite<PF_PixelFloat>(input) : '
               'GenericRadialInputIsSDR<PF_PixelFloat>(input));' if args.experiment == 'finite-zoom'
               else 'GenericRadialInputIsFinite<PF_PixelFloat>(input);')
    assert source.count(old) == 1, 'Experimental boundary changed'
    source=source.replace(old,new)
    if args.experiment == 'centers-radius':
        old='const A_long min_r = std::max<A_long>(0, (A_long)(std::sqrt(left * left + top * top) / ratio) - 2);'
        assert source.count(old)==1
        source=source.replace(old,old.replace('const A_long','A_long'))
        old='const A_long max_r = (A_long)std::sqrt(max_x * max_x + max_y * max_y) + 2;'
        assert source.count(old)==1
        source=source.replace(old,old.replace('const A_long','A_long')+'\n\tif (use_generic_baseline)\n\t\tZoomRadiusBoundsAEX(w, h, (float)cx, (float)cy, (float)ratio, &min_r, &max_r);')
    snapshot = out/'experiment.cpp'
    snapshot.write_text(source)
    snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
    if args.snapshot_only:
        print(snapshot)
        return 0
    public.SOURCE = snapshot
    sys.argv = [sys.argv[0], *forwarded]
    return run.main()


if __name__ == '__main__':
    raise SystemExit(main())
