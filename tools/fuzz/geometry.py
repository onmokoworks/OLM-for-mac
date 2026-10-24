"""Versioned, opt-in geometry sampling; no host ABI or pixel resampling here.

Hosts must explicitly advertise this sampler before run.py executes its cases.
The request is in sampled coordinates. Output allocation must be negotiated by
that host, never inferred from this input rectangle.
"""
import copy
import random

VERSION = 'realistic-v1'


def sample(case, mode='default'):
    if mode == 'default':
        return case
    if mode not in ('realistic', VERSION):
        raise ValueError('unknown geometry sampler: '+mode)
    from core import case_seed
    if 'geometry_sampler' in case:
        raise ValueError('geometry already sampled')
    result = copy.deepcopy(case)
    rng = random.Random(case_seed(case['seed'], case['index']) ^ 0xF52B)
    ratios = rng.choice([((1,1),(1,1)), ((1,2),(1,2)), ((1,3),(1,3)),
                         ((1,4),(1,4)), ((1,8),(1,8)), ((1,2),(1,3))])
    full = list(case['geometry'])
    w,h = [(n*num+den-1)//den for n,(num,den) in zip(full,ratios)]
    pixel = case['depth']//8*4
    result.update(geometry_sampler=VERSION, full_geometry=full, geometry=[w,h],
                  downsample=[list(r) for r in ratios],
                  pixels=b''.join(case['pixels'][y*full[0]*pixel:(y*full[0]+w)*pixel] for y in range(h)))
    for p in result['parameters']:
        if p['kind'] == 'p':
            p['value'] = [round(v*num/den*65536)/65536 for v,(num,den) in zip(p['value'],ratios)]
    def rectangle():
        if rng.randrange(2):
            return [0,0,w,h]
        left,top = rng.randrange(w),rng.randrange(h)
        return [left,top,rng.randint(left+1,w),rng.randint(top+1,h)]
    result['extent_hint'] = rectangle()
    result['request_rect'] = rectangle()
    result['pixel_aspect'] = list(rng.choice([(1,1),(10,11),(4,3),(2,1)]))
    # The F52 oracle exposes a single padding option. Match both candidate rows.
    result['rowbytes_padding'] = rng.choice([0,1,3,7,16,32])
    result['input_padding'] = result['output_padding'] = result['rowbytes_padding']
    return result


def resize(case, old_geometry):
    """Keep cropped worlds consistent with full dimensions and sampled rects."""
    if 'geometry_sampler' not in case:
        return case
    if case['geometry_sampler'] != VERSION:
        raise ValueError('unknown geometry sampler version')
    case['full_geometry'] = [(n*den+num-1)//num for n,(num,den) in zip(case['geometry'],case['downsample'])]
    for key in ('extent_hint','request_rect'):
        l,t,r,b = case[key]
        w,h = case['geometry']; ow,oh = old_geometry
        left,top = min(w-1,l*w//ow),min(h-1,t*h//oh)
        case[key] = [left,top,max(left+1,min(w,(r*w+ow-1)//ow)),
                    max(top+1,min(h,(b*h+oh-1)//oh))]
    return case


def require_host(adapter, case):
    """Never silently measure geometry ignored by a legacy fake host."""
    version = case.get('geometry_sampler')
    if version and version not in getattr(adapter, 'geometry_samplers', ()):
        raise ValueError(f'{adapter.name}: host has not qualified {version} geometry')

    adapter.geometry_active=bool(version)
    if version and getattr(adapter,'geometry_routes',None):
        if not hasattr(adapter,'_default_geometry_routes'):adapter._default_geometry_routes=adapter.routes
        adapter.routes=adapter.geometry_routes
    elif not version and hasattr(adapter,'_default_geometry_routes'):
        adapter.routes=adapter._default_geometry_routes
