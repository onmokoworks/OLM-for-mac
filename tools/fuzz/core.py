"""Plugin-independent raw differential runner and bounded greedy reduction."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import zlib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def case_seed(seed, index):
    return int.from_bytes(hashlib.sha256(f'{seed}:{index}'.encode()).digest()[:8], 'little')


def command(argv, *, data=None, timeout, deadline, env=None):
    """Kill the entire subprocess group at either deadline; never use shell=True."""
    remaining = min(timeout, deadline - time.monotonic())
    if remaining <= 0:
        return {'status': 'budget', 'reason': 'campaign deadline'}, b'', b''
    with subprocess.Popen(list(map(str, argv)), stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, start_new_session=True) as proc:
        try:
            out, err = proc.communicate(data, timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
            return {'status': 'budget', 'reason': 'wall timeout', 'limit_seconds': remaining}, out, err
    return {'status': 'ok' if proc.returncode == 0 else 'error',
            'returncode': proc.returncode}, out, err


def raw_diff(expected, actual, depth):
    unit = {8: 1, 16: 2, 32: 4}[depth]
    differences = [i for i in range(min(len(expected), len(actual))) if expected[i] != actual[i]]
    first = differences[0] if differences else min(len(expected), len(actual))
    word = first // unit
    return {'expected_bytes': len(expected), 'actual_bytes': len(actual),
            'different_bytes': len(differences) + abs(len(expected)-len(actual)),
            'different_words': sum(expected[i:i+unit] != actual[i:i+unit]
                                   for i in range(0, max(len(expected), len(actual)), unit)),
            'first_byte': first,
            'first_word': word,
            'expected_word_hex': expected[word*unit:(word+1)*unit].hex(),
            'actual_word_hex': actual[word*unit:(word+1)*unit].hex()}


def evaluate(adapter, case, directory, deadline, attribution=None):
    pairing = getattr(adapter, 'oracle_routes', {route: None for route in adapter.routes})
    references = {owner: adapter.oracle(case, directory, deadline, owner) if owner is not None
                  else adapter.oracle(case, directory, deadline) for owner in dict.fromkeys(pairing.values())}
    oracles = {}
    results = {}
    for route in adapter.routes:
        oracle, reference = references[pairing[route]]
        oracle = dict(oracle)
        if oracle['status'] == 'ok':
            oracle['raw_sha256'] = sha(reference)
        oracles[route] = oracle
        no_write = getattr(adapter, 'original_routes', {}).get(pairing[route]) == 'no-write'
        if no_write:
            oracle['semantics'] = 'no-write; AEX destination initially zero'
            if oracle['status'] == 'ok' and reference != bytes(len(case['pixels'])):
                oracle.update(status='harness_error', diagnostic='declared no-write AEX changed destination')
        outcome = adapter.candidate(case, directory, route, deadline)
        result, raw = outcome[0], outcome[1]
        if attribution is not None and len(outcome) > 2 and outcome[2]:
            attribution[route] = outcome[2]
        if result['status'] == 'ok':
            result['raw_sha256'] = sha(raw)
            if oracle['status'] == 'ok':
                if no_write:
                    # No numeric image exists for a no-write command. Check the
                    # Mac host's own initial bytes, never another route's image.
                    unchanged = raw == bytes([adapter.no_write_fill]) * len(case['pixels'])
                    result['status'] = 'no_write' if unchanged else 'no_write_violation'
                else:
                    result['status'] = 'exact' if reference == raw else 'mismatch'
                    if reference != raw:
                        result['diff'] = raw_diff(reference, raw, case['depth'])
            else:
                result['status'] = 'uncompared'
        results[route] = result
    stage = adapter.first_stage(case, directory, results, deadline) if any(
        r['status'] == 'mismatch' for r in results.values()) else None
    # Keep the historical primary reference for diagnostic consumers. It must
    # never be used for per-route comparisons; oracles is authoritative.
    primary = oracles[adapter.routes[-1]]
    route_metadata = {'oracles': oracles} if len(references) > 1 else {}
    return {**route_metadata, 'oracle': primary, 'routes': results, 'first_mismatching_stage': stage,
            'stage_observation': 'paired stages unavailable; final raw output only' if stage is None else 'paired stages'}


def mismatch_routes(result):
    return [route for route, value in result['routes'].items() if value['status'] in ('mismatch', 'no_write_violation')]


def crop(case, width, height):
    changed = copy.deepcopy(case)
    oldw, _ = case['geometry']
    pixel = case['depth']//8 * 4
    changed['pixels'] = b''.join(case['pixels'][y*oldw*pixel:(y*oldw+width)*pixel] for y in range(height))
    changed['geometry'] = [width, height]
    return changed


def apply_operation(adapter, case, op):
    changed = copy.deepcopy(case)
    if op['kind'] == 'crop':
        changed = crop(case, *op['geometry'])
        return adapter.resize(changed, case['geometry'])
    if op['kind'] == 'params':
        values = {int(k): v for k, v in op['values'].items()}
        for parameter in changed['parameters']:
            if parameter['slot'] in values:
                parameter['value'] = values[parameter['slot']]
    elif op['kind'] == 'pixels':
        if op['value'] == 'zero':
            changed['pixels'] = bytes(len(case['pixels']))
        elif op['value'] == 'constant':
            pixel = case['depth']//8 * 4
            changed['pixels'] = case['pixels'][:pixel] * (len(case['pixels'])//pixel)
        else:
            changed['pixels'] = adapter.simple_pixels(case)
    else:
        raise ValueError(op)
    return changed


def proposals(adapter, case):
    w, h = case['geometry']
    for geometry in dict.fromkeys([(1, 1), (max(1, w//2), max(1, h//2)),
                                    (1, h), (w, 1)]):
        if list(geometry) != case['geometry']:
            yield {'kind': 'crop', 'geometry': list(geometry)}
    defaults = {p['slot']: p['value'] for p in adapter.defaults(*case['geometry'])}
    changed = {p['slot']: defaults[p['slot']] for p in case['parameters'] if p['value'] != defaults[p['slot']]}
    if changed:
        yield {'kind': 'params', 'values': changed}
    for slot, value in changed.items():
        yield {'kind': 'params', 'values': {slot: value}}
    for mode in ('zero', 'constant', 'binary'):
        yield {'kind': 'pixels', 'value': mode}
    for parameter in case['parameters']:
        slot, value = parameter['slot'], parameter['value']
        if slot in changed and parameter['kind'] in ('i', 's', 'a'):
            midpoint = (value + defaults[slot])/2
            if parameter['kind'] == 'i':
                midpoint = int(midpoint)
            elif parameter['kind'] == 'a':
                midpoint = round(midpoint*65536)/65536
            if midpoint != value:
                yield {'kind': 'params', 'values': {slot: midpoint}}


def shrink(adapter, original, result, directory, deadline, max_attempts):
    """Only accept a reduction if all initially mismatching routes still mismatch."""
    target = set(mismatch_routes(result))
    case = original
    operations = []
    attempts = 0
    outcomes = {}
    # Bounded greedy passes; explicitly not a proof of global minimality.
    while attempts < max_attempts and time.monotonic() < deadline:
        improved = False
        for op in proposals(adapter, case):
            if attempts >= max_attempts or time.monotonic() >= deadline:
                break
            candidate = apply_operation(adapter, case, op)
            if candidate == case:
                continue
            attempts += 1
            observed = evaluate(adapter, candidate, directory, deadline)
            outcome = observed['oracle']['status'] + '/' + ','.join(
                observed['routes'][route]['status'] for route in adapter.routes)
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            if target.issubset(mismatch_routes(observed)):
                case, result = candidate, observed
                operations.append(op)
                improved = True
                break
        if not improved:
            break
    return case, result, {'attempts': attempts, 'accepted': operations,
                          'outcomes': outcomes, 'bounded': True, 'minimality_claimed': False}


def signature(adapter, case, result):
    defaults = {p['slot']: p['value'] for p in adapter.defaults(*case['geometry'])}
    slots = [p['slot'] for p in case['parameters'] if p['value'] != defaults[p['slot']]]
    return json.dumps([result['first_mismatching_stage'] or 'raw-output', slots, case['depth']], separators=(',', ':'))


def save_corpus(path, adapter, original, case, result, reduction, provenance):
    data = {'schema': 'olm-fuzz-case/1', 'plugin': adapter.name,
            'generator_version': adapter.generator_version,
            'seed': original['seed'], 'index': original['index'],
            'max_size': adapter.max_size,
            'operations': reduction['accepted'],
            'case': {k: v for k, v in case.items() if k != 'pixels'},
            'input_sha256': sha(case['pixels']), 'result': result,
            'reduction': reduction, 'provenance': provenance}
    compressed = zlib.compress(case['pixels'], 9)
    # Large unreduced random inputs stay procedural: seed + accepted operations.
    if len(compressed) <= 32768:
        data['pixels_zlib_base64'] = base64.b64encode(compressed).decode()
    path.write_text(json.dumps(data, sort_keys=True, indent=2)+'\n')
    return data


def load_corpus(path, adapter):
    data = json.loads(path.read_text())
    if data['plugin'] != adapter.name or data['generator_version'] != adapter.generator_version:
        raise ValueError('Corpus adapter/generator version does not match')
    if data['max_size'] != adapter.max_size:
        raise ValueError('Replay requires the corpus --max-size')
    if 'pixels_zlib_base64' in data:
        case = dict(data['case'], pixels=zlib.decompress(base64.b64decode(data['pixels_zlib_base64'])))
    else:
        case = adapter.generate(data['seed'], data['index'])
        for op in data['operations']:
            case = apply_operation(adapter, case, op)
    if sha(case['pixels']) != data['input_sha256']:
        raise ValueError('Corpus input hash mismatch')
    return case, data
