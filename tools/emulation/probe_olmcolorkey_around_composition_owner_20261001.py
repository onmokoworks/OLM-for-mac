#!/usr/bin/env python3
"""Recover the legal Around/Manhattan/Blur4 owner and Thin composition.

Temporary source experiments precede production admission. All references use
the exported AEX owner and its actual parameter builder, without a record detour.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
import probe_olmcolorkey_thin_public_owner_20261001 as thin_owner

ROOT = thin_owner.ROOT
SOURCE = thin_owner.general.SOURCE
HARNESS = thin_owner.HARNESS.replace('if(argc!=8)', 'if(argc!=11)').replace(
    'info.edge_thin_amount=thin;', '''info.premultiplied=atoi(argv[9]);
 info.enable_replace=atoi(argv[10]);info.use_replace_color[0]=info.use_replace_color[1]=true;
 info.replace_colors[0]={1,224/255.f,32/255.f,96/255.f};
 info.replace_colors[1]={1,26/255.f,89/255.f,242/255.f};
 info.edge_blur_amount=atoi(argv[8]);
 info.edge_thin_amount=thin;''')


def candidate_source(original: str) -> str:
    replace_once = thin_owner.general.base.replace_once
    body = replace_once(original, 'static bool IsGenericEdgeCompositionTuple', '''static bool IsRecoveredAroundBlur(const OLMColorKeyInfo &info)
{
    return info.edge_blur_direction == 102 && info.edge_blur_distance_type == 2 &&
           info.edge_blur_amount == 4.0;
}

static bool IsGenericEdgeCompositionTuple''')
    start = body.index('\t(void)info;', body.index('static bool IsGenericEdgeCompositionTuple'))
    end = body.index('\n}', start)
    body = body[:start] + '''    return IsRecoveredAroundBlur(info) &&
           info.edge_thin_amount >= -100.0 && info.edge_thin_amount <= 100.0 &&
           info.edge_thin_distance_type >= 1 && info.edge_thin_distance_type <= 3;''' + body[end:]
    body = replace_once(body, 'if (!info.color_keep && info.edge_thin_amount != 0.0)',
                        'if (!info.color_keep && (info.edge_thin_amount != 0.0 || IsRecoveredAroundBlur(info)))')
    needle = 'if (info.color_keep && info.edge_thin_amount != 0.0)'
    if body.count(needle) != 2: raise RuntimeError('expected both matched-matte alpha gates')
    body = body.replace(needle, 'if (info.color_keep && (info.edge_thin_amount != 0.0 || IsRecoveredAroundBlur(info)))')
    body = replace_once(body,
        '(bounded_public_owner_lane || OLMCKPixelTraits<PixelT>::is_32bpc()) ? 1.0f : 255.0f;',
        '(IsRecoveredAroundBlur(info) || bounded_public_owner_lane || OLMCKPixelTraits<PixelT>::is_32bpc()) ? 1.0f : 255.0f;')
    body = replace_once(body,
        "\t\t\t\tif (bounded_public_owner_lane && edge_blur_direction == 1) {",
        r'''				if (IsRecoveredAroundBlur(info)) {
                    // FUN_180005550: FLOAT32 pi/2/amount, signed phase,
                    // sinf, add 1, multiply 0.5; native integer writer truncates.
                    if (native_dist == 0.0f) weight = 0.5f;
                    else if (native_dist >= (float)info.edge_blur_amount) weight = keep ? 1.0f : 0.0f;
                    else {
                        float phase = native_dist * (1.5707963705062866f / (float)info.edge_blur_amount);
                        if (!keep) phase = -phase;
                        float sine = std::sin(phase);
                        weight = (sine + 1.0f) * 0.5f;
                    }
                    if (!keep && weight != 0.0f) OLMCKPixelTraits<PixelT>::restore_alpha(*outP, *inP);
                    OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(*outP, weight);
                    continue;
                }
				if (bounded_public_owner_lane && edge_blur_direction == 1) {''')
    body = replace_once(body, "\tstd::vector<int> matched_index(pixel_count, -1);",
        "\tstd::vector<int> matched_index(pixel_count, -1);\n\tstd::vector<u_char> thin_expanded(pixel_count, 0);")
    body = replace_once(body,
        "\t\t\tmatched[i] = (matched[i] || dist[i] * distance_scale <= limit) ? 1 : 0;",
        "\t\t\tthin_expanded[i] = (!matched[i] && dist[i] * distance_scale <= limit) ? 1 : 0;\n"
        "\t\t\tmatched[i] = (matched[i] || thin_expanded[i]) ? 1 : 0;")
    body = replace_once(body, "(keep || !info.premultiplied)) {", "!thin_expanded[idx]) {")
    return body


def compile_public(directory: Path, body: str) -> Path:
    saved = thin_owner.HARNESS
    try:
        thin_owner.HARNESS = HARNESS
        return thin_owner.compile_public(directory, body)
    finally:
        thin_owner.HARNESS = saved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--production', action='store_true')
    parser.add_argument('--boundaries', action='store_true', help='Singleton/one-dimensional worlds and Thin +/-100')
    parser.add_argument('--quick', action='store_true', help='One mixed-alpha geometry, Replace/premultiplied off')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    original = SOURCE.read_text()
    body = original if args.production else candidate_source(original)
    sha = thin_owner.general.base.sha
    probe = thin_owner.general.base.retained.actual_probe
    rows = []
    fixtures = thin_owner.general.FIXTURES[1:2] if args.quick else thin_owner.general.FIXTURES
    if args.boundaries:
        fixtures = ({'id':'single_opaque','width':1,'height':1,'alpha':'opaque'},
                    {'id':'column_opaque','width':1,'height':7,'alpha':'opaque'},
                    {'id':'row_mixed_zero','width':9,'height':1,'alpha':'mixed'})
    amounts = (0,-100,-4,-1,1,4,100) if args.boundaries else (0,-4,-1,1,4)
    toggles = ((False, False),) if args.quick else ((False, False), (False, True), (True, False), (True, True))
    with tempfile.TemporaryDirectory(prefix='olmck_around_owner_') as raw:
        directory = Path(raw)
        exe = compile_public(directory/'mac', body)
        for fixture in fixtures:
            w, h = fixture['width'], fixture['height']
            source8, rb = thin_owner.general.fixture(fixture, 'PF8')
            image = Image.new('RGBA', (w, h))
            image.putdata([tuple(source8[y*rb+x*4+1:y*rb+x*4+4])+(source8[y*rb+x*4],)
                           for y in range(h) for x in range(w)])
            input_png = directory/'input.png'; image.save(input_png)
            for premultiplied, replace in toggles:
                for keep in (False, True):
                    for distance in (1, 2, 3):
                        for thin in amounts:
                            for depth, fmt in (('PF8','argb8'), ('PF16','argb16'), ('PF32','argb32f')):
                                params = [f'Color Keep={int(keep)}', f'Premultiplied Color={int(premultiplied)}',
                                    'Number of Colors=2', 'Use Color 1=1', 'Color 1=255,0,0,0',
                                    'Use Color 2=1', 'Color 2=255,0,255,0', f'Amount@14={thin}',
                                    f'Distance Type@15={distance}', 'Amount@18=4', 'Distance Type@19=2', 'Direction@20=2',
                                    f'Enable Replace={int(replace)}', 'Use Replace Color 1=1', 'Replace Color 1=255,224,32,96',
                                    'Use Replace Color 2=1', 'Replace Color 2=255,26,89,242']
                                actual = json.loads(subprocess.check_output([str(args.worker), 'render-png', str(probe.AEX),
                                    str(input_png), str(directory/'output.png'), '--pixel-format', fmt, *params], text=True))
                                if (actual['render_error'] or not actual['guards_intact'] or actual['unsupported_suite_calls'] or
                                    actual['dropped_unsupported_suite_calls'] or actual['setup']['global_setup_error'] or
                                    actual['setup']['params_setup_error']): raise RuntimeError('AEX exported owner failure')
                                values = {p['slot']:p.get('value') for p in actual['parameter_values']}
                                required = {1:int(keep),4:int(premultiplied),14:thin,15:distance,18:4,19:2,20:2,23:int(replace)}
                                if any(values[k] != v for k,v in required.items()): raise RuntimeError('parameter propagation drift')
                                source, _ = thin_owner.general.fixture(fixture, depth)
                                results = {}
                                for route, name in ((0,'classic'),(1,'smart')):
                                    output = subprocess.check_output([str(exe),str(w),str(h),depth[2:],str(thin),str(distance),
                                        str(int(keep)),str(route),'4',str(int(premultiplied)),str(int(replace))],input=source)
                                    if len(output) != actual['raw_pixel_bytes']: raise RuntimeError('output size drift')
                                    digest = sha(output)
                                    results[name] = {'exact':digest==actual['raw_pixel_sha256'],'sha256':digest}
                                rows.append({'fixture':fixture,'depth':depth,'keep':keep,'premultiplied':premultiplied,
                                    'replace':replace,'thin':thin,'type':distance,'blur':4,'input_sha256':sha(source),
                                    'input_png_sha256':actual['input_png_sha256'],'actual_sha256':actual['raw_pixel_sha256'],
                                    'parameter_values':actual['parameter_values'],'guards_intact':actual['guards_intact'],'results':results})
                    print(f"{fixture['id']} premultiplied={premultiplied} replace={replace} keep={keep}",flush=True)
    report = {'schema':'olmcolorkey.around-composition-owner/1','date':'2026-10-01','production':args.production,
        'case_count':len(rows),'source_sha256':sha(original.encode()),'candidate_source_sha256':sha(body.encode()),
        'probe_sha256':sha(Path(__file__).read_bytes()),'aex_sha256':sha(probe.AEX.read_bytes()),
        'worker_sha256':sha(args.worker.read_bytes()),'dependencies':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in
            (Path(thin_owner.__file__),Path(thin_owner.general.__file__),thin_owner.SDK_PROBE,SOURCE.with_suffix('.h'))},
        'summary':{route:sum(r['results'][route]['exact'] for r in rows) for route in ('classic','smart')},'cases':rows,
        'scope':'Around public2, Manhattan public2, Blur4; exported AEX Smart CPU owner and real SDK Mac Classic/Smart. Actual builder, full-resolution typed RGBA8 promotion. No native AE/installed claim.'}
    metadata = {k:v for k,v in report.items() if k != 'cases'}
    prefix = json.dumps(metadata,sort_keys=True,indent=2).rstrip()[:-1].rstrip()
    args.report.write_text(prefix+',\n  "cases": [\n'+',\n'.join(
        '    '+json.dumps(row,sort_keys=True,separators=(',',':')) for row in rows)+'\n  ]\n}\n')
    print(json.dumps(report['summary']))
    return 0

if __name__=='__main__': raise SystemExit(main())
