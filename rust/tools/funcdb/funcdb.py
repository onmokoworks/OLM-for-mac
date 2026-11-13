"""Evidence-backed original AEX -> Rust function library, using the persistent hub."""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
_client_spec = importlib.util.spec_from_file_location('olm_ghidra_client',HERE.parent/'ghidra-hub/client.py')
_client_module = importlib.util.module_from_spec(_client_spec)
_client_spec.loader.exec_module(_client_module)
Client = _client_module.Client
from binary import Image, NORMALIZER, digest, similarity

PLUGINS = dict(ColorKeep='color-keep', DistanceGradation='olm-distance-gradation',
               OLMBlur='olm-blur', OLMColorKey='olm-color-key',
               OLMDirectionalBlur='olm-directional-blur', OLMKiraKira='olm-kirakira',
               OLMRadialBlur='olm-radial-blur', OLMSmoother='olm-smoother',
               OLMSmoother2='olm-smoother2', OLMToonDilate='olm-toon-dilate')
DEFAULT_DB = HERE/'catalog.json.gz'
DEFAULT_ORIGINALS = ROOT.parent/'ghidra_windows_aex'


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = encoded(value)+b'\n'
    if path.suffix == '.gz':
        data = gzip.compress(data, mtime=0)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_bytes(data)
    temp.replace(path)


def read(path):
    path = Path(path)
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def log(message):
    print(message, file=sys.stderr, flush=True)


def collect(client, aex, cache, program=None):
    image = Image(aex)
    catalog = client.programs_list()
    equal = [p for p in catalog if p['sha256'].lower() == image.sha256]
    if program:
        equal = [p for p in equal if p['name'] == program]
    if not equal:
        if program:
            raise ValueError(f'Original {program} absent or hash differs from hub')
        name = 'funcdb-'+image.path.stem+'@'+image.sha256[:12]
        log(f'Importing {name} into shared hub (one analysis)')
        client.add_program(aex=str(image.path.resolve()), name=name)
        equal = [p for p in client.programs_list() if p['name'] == name]
    info = sorted(equal, key=lambda p: p['name'])[0]
    if not info['analyzed'] or info['language'] != 'x86:LE:64:default':
        raise ValueError('Hub program must have completed AMD64 analysis')
    program = info['name']
    rows = list(client.all_functions(programs=[program]))
    # Inventory remains live even on cache hits: names/comments may change.
    inventory_hash = digest(encoded([(r['address'], r['size']) for r in rows]))
    cachefile = Path(cache)/(image.sha256+'-'+NORMALIZER+'.json.gz')
    cached = read(cachefile) if cachefile.exists() else None
    if cached and cached.get('inventory_hash') == inventory_hash:
        for f, row in zip(cached['functions'], rows):
            f['name'] = row['name']
        cached['program'] = program
        return cached, rows
    graph = client.call_graph(program=program, depth=1)
    nodes = {n['address']: n for n in graph['nodes']}
    entries = {int(r['address'], 16) for r in rows}
    entry_strings = {r['address'] for r in rows}
    callees, callers = defaultdict(set), defaultdict(set)
    for source, target in graph['edges']:
        callees[source].add(target)
        callers[target].add(source)
    checkpoint = cachefile.with_name(cachefile.name+'.partial.json.gz')
    prior = read(checkpoint) if checkpoint.exists() else {}
    functions = prior.get('functions', []) if prior.get('inventory_hash') == inventory_hash else []
    fallback = 0
    for n, row in enumerate(rows):
        if n < len(functions):
            continue
        address = int(row['address'], 16)
        instructions = image.recover(address, row['size'], entries)
        method = 'cfg-size-checked'
        if instructions is None:
            fallback += 1
            method = 'hub-listing'
            try:
                exported = client.export_function(program=program, function=row['address'])
                instructions = image.exported(exported['directory'], row['size'])
            except Exception:
                save(checkpoint, dict(inventory_hash=inventory_hash, functions=functions))
                raise
        if not instructions:
            raise ValueError(f'No decoded body: {program}:{row["address"]}')
        fp = image.fingerprint(instructions)
        direct_imports = {nodes[a]['name'] for a in callees[row['address']]
                          if a in nodes and a not in entry_strings}
        def rva(a):
            return format(int(a, 16)-image.base, 'x')
        functions.append(dict(rva=rva(row['address']), name=row['name'], size=row['size'],
                              decoded_bytes=sum(i.size for i in instructions),
                              listing_only_instructions=sum(hasattr(i,'text') for i in instructions),
                              decoder_overlap=any(a.address+a.size>b.address for a,b in zip(instructions,instructions[1:])),
                              fingerprint=fp, body_source=method,
                              callees=sorted(rva(a) for a in callees[row['address']] if a in entry_strings),
                              callers=sorted(rva(a) for a in callers[row['address']] if a in entry_strings),
                              external_callees=sorted(direct_imports)))
        if n % 1000 == 0:
            save(checkpoint, dict(inventory_hash=inventory_hash, functions=functions))
            log(f'{program}: {n+1}/{len(rows)} functions; hub listing fallbacks={fallback}')
    result = dict(program=program, sha256=image.sha256, image_base=hex(image.base),
                  inventory_hash=inventory_hash, external_functions=info['external_functions'],
                  imports=sorted(set(image.imports.values())), functions=functions)
    save(cachefile, result)
    log(f'{program}: complete {len(rows)}; hub listing fallbacks={fallback}')
    return result, rows


def build(client, originals, cache, exclude=()):
    from evidence import discover
    db = dict(schema=1, normalizer=NORMALIZER, programs=[], mappings=[], evidence=[])
    inventories = {}
    for program in sorted(PLUGINS):
        if program in exclude:
            continue
        record, rows = collect(client, Path(originals)/(program+'.aex'), cache, program)
        db['programs'].append(record)
        inventories[program] = rows
    mappings, evidence, audit = discover(ROOT, db['programs'], PLUGINS)
    db['mappings'], db['evidence'], db['evidence_scan'] = mappings, evidence, audit
    # Deduplicate bulky fuzzy signatures shared by statically linked libraries.
    fingerprints = {}
    for p in db['programs']:
        for f in p['functions']:
            fp = f.pop('fingerprint')
            key = digest(encoded(fp))
            fingerprints[key] = fp
            f['fingerprint_id'] = key
    db['fingerprints'] = fingerprints
    return db


def iter_functions(db):
    for p in db['programs']:
        for f in p['functions']:
            yield p, f, db['fingerprints'][f['fingerprint_id']]


def exact_key(fp):
    return fp['exact'], fp['literals'], tuple(fp['imports'])


def analysis_warnings(f):
    result=[]
    if f.get('decoder_overlap'):
        result.append('Ghidra/Capstone instruction boundaries overlap')
    if f.get('listing_only_instructions'):
        result.append('Some instructions use the Ghidra-text fallback')
    if f.get('decoded_bytes',f['size']) != f['size']:
        result.append('Decoded instruction bytes differ from Ghidra body size')
    return result


class Matcher:
    def __init__(self, db, exclude=()):
        self.exact, self.inverted = defaultdict(list), defaultdict(set)
        self.fingerprints, self.members = {}, defaultdict(list)
        self.mapping = defaultdict(list)
        for m in db['mappings']:
            if m['program'] not in exclude:
                self.mapping[m['program'], m['rva']].append(m)
        for p, f, fp in iter_functions(db):
            if p['program'] in exclude:
                continue
            member = (p['program'], f)
            self.exact[exact_key(fp)].append(member)
            fid = f['fingerprint_id']
            self.members[fid].append(member)
            if fid not in self.fingerprints:
                self.fingerprints[fid] = fp
                for token in fp['fuzzy']:
                    self.inverted[token].add(fid)

    def candidate(self, program, function, score):
        mappings = self.mapping[program, function['rva']]
        return dict(program=program, rva=function['rva'], name=function['name'], similarity=score,
                    mappings=mappings, verified_rust=any(m.get('verified_rust') for m in mappings),
                    analysis_warnings=analysis_warnings(function))

    def match(self, f, fp, threshold=.65, limit=5):
        matches = self.exact.get(exact_key(fp), [])
        if matches:
            candidates = [self.candidate(p, other, 1.0) for p, other in matches]
            # Retain all duplicate identities: truncation could hide conflicting mappings.
            return dict(kind='exact', candidates=candidates, ambiguous=len(candidates)>1,
                        tiny=fp['instructions']<5)
        votes = Counter(fid for token in fp['fuzzy'] for fid in self.inverted.get(token, ()))
        ranked = []
        for fid, count in votes.items():
            other = self.fingerprints[fid]
            ratio = min(fp['instructions'], other['instructions'])/max(fp['instructions'], other['instructions'], 1)
            if round(ratio,6) < threshold:
                continue
            # Intersection in the union sample cannot exceed shared sketch
            # tokens; its denominator is at least the larger sketch size.
            if round(count/max(len(fp['fuzzy']),len(other['fuzzy']),1)*ratio,6) < threshold:
                continue
            score = similarity(fp, other)
            if score >= threshold:
                for p, member in self.members[fid]:
                    ranked.append(self.candidate(p, member, score))
        ranked.sort(key=lambda r: (-r['similarity'], r['program'], int(r['rva'], 16)))
        return dict(kind='fuzzy' if ranked else 'unknown', candidates=ranked[:limit],
                    candidate_count=len(ranked), ambiguous=len(ranked)>1, tiny=fp['instructions']<5)


def lookup(db, record, exclude=(), threshold=.65):
    matcher = Matcher(db, exclude)
    result = []
    original = next((p for p in db['programs'] if p['sha256'] == record['sha256']
                     and p['program'] not in exclude), None)
    for f in record['functions']:
        match = matcher.match(f, f['fingerprint'], threshold)
        # Only the identical binary + RVA establishes an already verified mapping.
        own = matcher.mapping.get((original['program'], f['rva']), []) if original else []
        covered = any(m.get('verified_rust') for m in own)
        potential = any(c['verified_rust'] for c in match['candidates'])
        status = 'already-covered' if covered else ('review-rust-reuse' if potential else 'port-or-classify')
        result.append(dict(rva=f['rva'], name=f['name'], size=f['size'], **match,
                           port_status=status, verified_rust=covered, own_mappings=own,
                           callers=f.get('callers',[]),callees=f.get('callees',[]),
                           imports_used=f['fingerprint']['imports'],external_callees=f.get('external_callees',[]),
                           analysis_warnings=analysis_warnings(f)))
    result.sort(key=lambda f: ({'unknown': 0, 'fuzzy': 1, 'exact': 2}[f['kind']], -f['size'], int(f['rva'], 16)))
    return dict(schema=1, aex_sha256=record['sha256'], program=record['program'],
                normalizer=db['normalizer'],evidence=db['evidence'],
                database_programs=[dict(program=p['program'],sha256=p['sha256']) for p in db['programs']],
                excluded=sorted(exclude), counts=dict(Counter(f['kind'] for f in result)),
                port_work=result, limitation='Fingerprint equality is not semantic or behavioral proof; indirect calls may be missing.')


def stats(db):
    mappings = defaultdict(list)
    for m in db['mappings']:
        mappings[m['program'], m['rva']].append(m)
    result = []
    for p in db['programs']:
        fs = p['functions']
        mapped = [f for f in fs if mappings[p['program'], f['rva']]]
        verified = [f for f in fs if any(m.get('verified_rust') for m in mappings[p['program'], f['rva']])]
        size = sum(f['size'] for f in fs)
        result.append(dict(program=p['program'], functions=len(fs), bytes=size,
                           functions_with_analysis_warnings=sum(bool(analysis_warnings(f)) for f in fs),
                           external_functions=p['external_functions'], mapped_functions=len(mapped),
                           mapped_bytes=sum(f['size'] for f in mapped),
                           mapped_functions_percent=round(100*len(mapped)/len(fs), 3),
                           mapped_bytes_percent=round(100*sum(f['size'] for f in mapped)/size, 3),
                           verified_rust_functions=len(verified),
                           verified_rust_functions_percent=round(100*len(verified)/len(fs), 3),
                           verified_rust_bytes_percent=round(100*sum(f['size'] for f in verified)/size, 3)))
    return result


def annotate(client, db):
    groups = defaultdict(list)
    for m in db['mappings']:
        groups[m['program'], m['rva']].append(m)
    rows = []
    for p in db['programs']:
        current = {r['address']: r for r in client.all_functions(programs=[p['program']])}
        live = next(x for x in client.programs_list() if x['name'] == p['program'])
        if live['sha256'].lower() != p['sha256']:
            raise ValueError('Annotation target hash mismatch')
        for f in p['functions']:
            mappings = groups.get((p['program'], f['rva']))
            if not mappings:
                continue
            address = format(int(p['image_base'], 16)+int(f['rva'], 16), 'x')
            previous = current[address]['comment']
            payload = dict(mappings=mappings,evidence=[db['evidence'][i] for i in sorted({e for m in mappings for e in m['evidence']})])
            block = '[funcdb evidence '+digest(encoded(payload))[:16]+']\n'+encoded(payload).decode()
            if block not in previous:
                rows.append(dict(program=p['program'], function=address,
                                 comment=(previous+'\n'+block).strip()))
    # Public API has no namespace/comment compare-and-swap: merge immediately
    # before writing, preserve names/signatures, and document concurrent-writer limit.
    return client.bulk_edit(rows=rows, provenance='Job L-funcdb: source-linked mappings; names preserved') if rows else []


def sqlite_export(path, db):
    path = Path(path)
    if path.exists():
        raise ValueError('SQLite destination must be new')
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as con, con:
        con.executescript('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);'
                          'CREATE TABLE programs(name TEXT PRIMARY KEY,sha256 TEXT,metadata TEXT);'
                          'CREATE TABLE fingerprints(id TEXT PRIMARY KEY,json TEXT);'
                          'CREATE TABLE functions(program TEXT,rva TEXT,size INTEGER,name TEXT,fingerprint TEXT,json TEXT,PRIMARY KEY(program,rva));'
                          'CREATE TABLE mappings(program TEXT,rva TEXT,json TEXT);'
                          'CREATE TABLE evidence(id INTEGER PRIMARY KEY,json TEXT);')
        for k in ('schema', 'normalizer', 'evidence_scan'):
            con.execute('INSERT INTO metadata VALUES (?,?)', (k, encoded(db[k]).decode()))
        for p in db['programs']:
            con.execute('INSERT INTO programs VALUES (?,?,?)', (p['program'], p['sha256'], encoded({k:v for k,v in p.items() if k!='functions'}).decode()))
            con.executemany('INSERT INTO functions VALUES (?,?,?,?,?,?)', [(p['program'], f['rva'], f['size'], f['name'], f['fingerprint_id'], encoded(f).decode()) for f in p['functions']])
        con.executemany('INSERT INTO fingerprints VALUES (?,?)', [(k, encoded(v).decode()) for k,v in sorted(db['fingerprints'].items())])
        con.executemany('INSERT INTO mappings VALUES (?,?,?)', [(m['program'], m['rva'], encoded(m).decode()) for m in db['mappings']])
        con.executemany('INSERT INTO evidence VALUES (?,?)', [(i, encoded(e).decode()) for i,e in enumerate(db['evidence'])])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8766')
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--cache', type=Path, default=HERE/'local/cache')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('build')
    p.add_argument('--originals', type=Path, default=DEFAULT_ORIGINALS)
    p.add_argument('--exclude', action='append', choices=sorted(PLUGINS), default=[])
    p.add_argument('--sqlite', type=Path)
    p.add_argument('--annotate', action='store_true')
    p = sub.add_parser('lookup')
    p.add_argument('--aex', type=Path, required=True)
    p.add_argument('--exclude', action='append', default=[])
    p.add_argument('--threshold', type=float, default=.65)
    p.add_argument('--out', type=Path, help='Default: runs/<binary-sha256>/lookup.json.gz')
    sub.add_parser('stats')
    sub.add_parser('annotate')
    args = parser.parse_args()
    if args.command == 'build':
        db = build(Client(args.url), args.originals, args.cache, args.exclude)
        save(args.db, db)
        if args.sqlite:
            sqlite_export(args.sqlite, db)
        if args.annotate:
            log(json.dumps(annotate(Client(args.url), db)))
        print(json.dumps(stats(db), indent=2))
    elif args.command == 'stats':
        print(json.dumps(stats(read(args.db)), indent=2))
    elif args.command == 'annotate':
        print(json.dumps(annotate(Client(args.url), read(args.db)), indent=2))
    else:
        if not 0 < args.threshold <= 1:
            parser.error('threshold must be in (0,1]')
        record, _ = collect(Client(args.url), args.aex, args.cache)
        result = lookup(read(args.db), record, args.exclude, args.threshold)
        if args.out is None:
            args.out = HERE/'runs'/record['sha256']/'lookup.json.gz'
        save(args.out, result)
        print(json.dumps(dict(output=str(args.out), counts=result['counts'])))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        log(str(error))
        sys.exit(2)
