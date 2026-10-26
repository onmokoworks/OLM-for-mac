#!/usr/bin/env python3
"""Compile the actual span helpers against adjacent and truly aliased worlds.

Scratch must be in orchestra/state. --revision permits a pre-fix measurement.
No AE SDK or copied oracle assets are needed for these admission-only probes.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def source(path, revision):
    if revision:
        return subprocess.check_output(['git', 'show', f'{revision}:{path}'], cwd=ROOT, text=True)
    return (ROOT / path).read_text()


def functions(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision')
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    if not scratch.is_relative_to(ROOT / 'orchestra/state'):
        parser.error('scratch must be under orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    results = {}
    for plugin, path, start, end in [
        ('olmcolorkey', 'mac/OLMColorKey/Render.inc', 'static bool CheckedPayloadBytes', 'template <typename PixelT>'),
        ('olmdirectionalblur', 'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp', 'static bool PayloadSpan', 'static bool PublicType3Layer16WorldsExact'),
        ('radialblur', 'mac/OLMRadialBlur/OLMRadialBlur.cpp', 'static bool RadialPayloadSpan', 'static bool RadialActiveRowBytes'),
    ]:
        body = functions(source(path, args.revision), start, end)
        new = 'size_t pixel_bytes' in body
        helper = 'RadialPayloadsDisjoint' if plugin == 'radialblur' else 'DisjointPayloads'
        call = helper + '(&a, &b' + (', pixel' if new else '') + ')'
        cpp = '''#include <cstddef>
#include <cstdint>
#include <limits>
#include <cstdio>
#include <vector>
struct PF_EffectWorld { void *data; int width, height, rowbytes; };
''' + body + '''
int main() {
    unsigned adjacent_refusals=0, missed_overlap=0, checks=0;
    for (int iteration=0; iteration<1000; ++iteration) {
        for (size_t pixel : {4u, 8u, 16u}) {
            for (int height : {1, 2, 7}) {
                const int width=2, stride=3*pixel+1;
                const size_t touched=(height-1)*stride+width*pixel;
                std::vector<unsigned char> arena(touched*2+64);
                PF_EffectWorld a{arena.data()+pixel,width,height,stride};
                PF_EffectWorld b{arena.data()+pixel+touched,width,height,stride};
                adjacent_refusals += !''' + call + ''';
                b.data=arena.data()+pixel+touched-1;
                missed_overlap += ''' + call + ''';
                ++checks;
            }
        }
    }
    std::printf("{\\"checks\\":%u,\\"adjacent_refusals\\":%u,\\"missed_overlap\\":%u}\\n",checks,adjacent_refusals,missed_overlap);
}
'''
        host, binary = scratch / (plugin + '.cpp'), scratch / plugin
        host.write_text(cpp)
        env = dict(os.environ, TMPDIR=str(scratch))
        subprocess.run(['clang++', '-std=c++17', '-O2', '-fsanitize=address,undefined', str(host), '-o', str(binary)], env=env, check=True)
        results[plugin] = json.loads(subprocess.check_output([binary], env=env, text=True))
    print(json.dumps(results, indent=2, sort_keys=True))
    return int(any(r['missed_overlap'] or (not args.revision and r['adjacent_refusals'])
                   for r in results.values()))


if __name__ == '__main__':
    raise SystemExit(main())
