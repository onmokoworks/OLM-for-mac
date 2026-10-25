"""Summarize retained real-AE measurements, without launching AE or inferring passes."""
import argparse
import json
from pathlib import Path


def summarize(priority, depths):
    renders = json.loads((priority / 'render-results.json').read_text())
    comparisons = json.loads((priority / 'comparisons.json').read_text())
    if depths:
        renders += json.loads((depths / 'render-results.json').read_text())
        comparisons += json.loads((depths / 'comparisons.json').read_text())
    lookup = {r['outputPrefix']: r for r in comparisons}
    print('O=raw exact vs original AEX; F=raw exact vs same-bundle fallback; '
          'E=raw exact with unspecified reference; H=hidden-RGB I/O difference; U=uncalibrated/unresolved; '
          'P=rendered, comparison pending; —=not rendered. B suffix=black/transparent. '
          'Each cell lists counts across available sizes. No tolerance is used.\n')
    print('| Plugin | 8 Full/Half/Third/Quarter | 16 Full/Half/Third/Quarter | 32 Full/Half/Third/Quarter |')
    print('|---|---|---|---|')
    plugins = list(dict.fromkeys(r['plugin'] for r in renders if r['plugin'] != 'control'))
    for plugin in plugins:
        cells=[]
        for depth in (8,16,32):
            resolutions=[]
            for divisor in (1,2,3,4):
                counts={}
                for r in renders:
                    if (r['plugin'],r['depth'],r['divisor']) != (plugin,depth,divisor): continue
                    record=lookup.get(r['outputPrefix'],{})
                    c=record.get('comparison',{})
                    exact_code = ('O' if record.get('original',{}).get('status')=='ok' else
                                  'F' if record.get('bundle',{}).get('status')=='ok' else 'E')
                    code = ('error' if r['status']=='error' else exact_code if c.get('exact') is True
                            else 'H' if 'hidden RGB' in str(c.get('classification'))
                            else 'U' if c else 'P')
                    if r['status']=='black': code+='B'
                    counts[code]=counts.get(code,0)+1
                resolutions.append(','.join(str(n)+k for k,n in counts.items()) or '—')
            cells.append(' / '.join(resolutions))
        print('| '+plugin+' | '+' | '.join(cells)+' |')
    print('\nWall seconds per 8 bpc Full frame, including aerender startup; single observations.\n')
    print('| Plugin | 1080p | 4K |\n|---|---:|---:|')
    for plugin in plugins:
        values=[]
        for width in (1920,3840):
            rows=[r for r in renders if (r['plugin'],r['depth'],r['width'],r['divisor'])==(plugin,8,width,1)]
            values.append(f"{rows[0]['wall_seconds']:.3f}" if rows else '—')
        print('| '+plugin+' | '+' | '.join(values)+' |')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('priority',type=Path); p.add_argument('--depths',type=Path)
    a=p.parse_args(); summarize(a.priority,a.depths)
