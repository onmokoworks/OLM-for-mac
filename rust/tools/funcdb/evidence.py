"""Conservative source evidence mining. Address mentions alone are not mappings."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

ADDRESS = re.compile(r'(?i)(?:FUN_|0x)((?:18|14)[0-9a-f]{7})(?![0-9a-f])')
RVA = re.compile(r'(?i)\bRVA\s+(?:0x)?([0-9a-f]{3,8})(?![0-9a-f])')
RUST_FN = re.compile(r'(?m)^[ \t]*(?:pub(?:\([^\n)]*\))?\s+)?(?:unsafe\s+)?(?:extern\s+"[^"]+"\s+)?(?:const\s+)?fn\s+(\w+)')
CPP_FN = re.compile(r'(?m)^[ \t]*(?:(?:static|inline|constexpr|extern)\s+)*(?:[\w:<>,*&]+[ \t\n]+)+?([A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:const\s*)?\{')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mentions(text, base):
    return sorted({int(m[1], 16)-base for m in ADDRESS.finditer(text)} |
                  {int(m[1], 16) for m in RVA.finditer(text)})


def adjacent_comments(text, start):
    lines = text[:start].splitlines()
    result = []
    for line in reversed(lines[-20:]):
        if not line.strip() or line.lstrip().startswith(('//', '/*', '*', '*/')):
            result.append(line)
        else:
            break
    return '\n'.join(reversed(result))


def discover(root, programs, plugins):
    root = Path(root)
    active = {p['program']: p for p in programs}
    entries = {name: {int(f['rva'],16):f for f in p['functions']} for name,p in active.items()}
    sources, evidence, mappings = {}, [], []
    evidence_ids = {}
    source_hashes = {}
    associations = defaultdict(set)
    cpp_defs, rust_defs = defaultdict(list), defaultdict(list)
    skipped = []

    def add(path, line, kind):
        key = (path, line, kind)
        if key not in evidence_ids:
            if path not in source_hashes:
                source_hashes[path] = sha((root/path).read_bytes())
            evidence_ids[key] = len(evidence)
            evidence.append(dict(path=path, line=line, kind=kind, source_sha256=source_hashes[path]))
        return evidence_ids[key]

    aliases = {p: {re.sub('[^a-z0-9]', '', p.lower()), re.sub('[^a-z0-9]', '', crate)} for p,crate in plugins.items()}
    aliases['DistanceGradation'].add('olmdistancegradation')
    module_overrides = {}
    for crate in plugins.values():
        src = root/'rust/plugins'/crate/'src'
        for source in src.rglob('*.rs'):
            parent_module = source.relative_to(src).with_suffix('').as_posix().replace('/','::')
            for m in re.finditer(r'#\[path\s*=\s*"([^"]+)"\]\s*(?:pub\s+)?mod\s+(\w+)',source.read_text(encoding='utf-8')):
                module_overrides[(source.parent/m[1]).resolve()] = parent_module+'::'+m[2]
    def infer(path, context=''):
        value = re.sub('[^a-z0-9]', '', path.lower())
        matched = {p for p, names in aliases.items() if any(a in value for a in names)}
        # Smoother2 is not Smoother; avoid shared address-space cross-contamination.
        if 'OLMSmoother2' in matched:
            matched.discard('OLMSmoother')
        if 'dblur' in path.lower():
            matched.add('OLMDirectionalBlur')
        if 'RadialBlur' in context or 'radial_noise' in context:
            matched = {'OLMRadialBlur'}
        return matched & active.keys()

    paths = set(root.glob('notes/IR_*.md'))
    for directory in ('core', 'mac', 'tools/emulation', 'disasm', 'decomp'):
        base = root/directory
        if not base.exists():
            continue
        for path in base.rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.md','.cpp','.h','.inc','.c','.rs','.py','.json','.txt','.asm'}:
                if any(part in {'target','node_modules','.venv','__pycache__','fixtures'} for part in path.relative_to(base).parts):
                    continue
                paths.add(path)
    for crate in plugins.values():
        base = root/'rust/plugins'/crate
        paths.update((base/'src').rglob('*.rs'))
        paths.update(base.glob('VALIDATION.md'))
        paths.update((base/'tools').glob('translate.py'))
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        if path.stat().st_size > 4*1024*1024:
            skipped.append(relative)
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        sources[relative] = text
        scope = infer(relative)
        for line, value in enumerate(text.splitlines(), 1):
            if not ADDRESS.search(value) and not RVA.search(value):
                continue
            for p in infer(relative, value) or scope:
                for rva in mentions(value, int(active[p]['image_base'],16)):
                    if rva in entries[p]:
                        associations[p,rva].add(add(relative, line, 'address-mention'))
        if path.suffix == '.rs' and '/src/' in relative:
            for m in RUST_FN.finditer(text):
                line = text.count('\n',0,m.start())+1
                name = m[1]
                context = adjacent_comments(text,m.start())+'\n'+m.group()
                for p in scope:
                    module = relative.split('/src/')[1].removesuffix('.rs').replace('/','::')
                    module = module_overrides.get(path.resolve(),module)
                    if module == 'lib':
                        module = 'crate'
                    record = dict(crate=plugins[p],module=module,fn=name,path=relative,line=line)
                    rust_defs[p,name].append(record)
                    for rva in mentions(context, int(active[p]['image_base'],16)):
                        if rva in entries[p]:
                            mappings.append(dict(program=p,rva=format(rva,'x'),rust=record,cpp=[],
                                confidence='high',basis='explicit Rust function name or adjacent address comment',
                                evidence=[add(relative,line,'rust-definition')],verified_rust=False))
        if path.suffix in {'.cpp','.c','.h','.inc'}:
            for m in CPP_FN.finditer(text):
                if m[1] in {'if','for','while','switch','catch'}:
                    continue
                context = adjacent_comments(text,m.start())+'\n'+m[1]
                line = text.count('\n',0,m.start())+1
                # A comment saying a helper *calls* another function is not a
                # definition mapping. Accept only direct entry labels here.
                named = ADDRESS.search(m[1])
                direct = re.search(r'(?m)^\s*//\s*FUN_[0-9a-fA-F]+\s*[:\-\u2014]',context)
                literal = re.search(r'(?m)^\s*//\s*'+re.escape(m[1])+r'\s*[^\n]*literal (?:port|twin) of (FUN_[0-9a-fA-F]+)',context)
                if not direct and literal:
                    direct = literal
                if not named and not direct:
                    continue
                for p in infer(relative,context):
                    targets = mentions(m[1] if named else direct.group(),int(active[p]['image_base'],16))
                    for rva in targets:
                        if rva in entries[p]:
                            record = dict(fn=m[1],path=relative,line=line)
                            cpp_defs[p,rva].append((record,add(relative,line,'cpp-definition')))

    # Explicit reviewed chains supplement mechanically address-named translations.
    reviewed_path = Path(__file__).with_name('reviewed.json')
    reviewed = json.loads(reviewed_path.read_text()) if reviewed_path.exists() else []
    for row in reviewed:
        p, rva = row['program'], int(row['rva'],16)
        if p not in active:
            continue
        if rva not in entries[p]:
            raise ValueError(f'Reviewed mapping has no hub function: {p}:{rva:x}')
        refs = []
        for ref in row['sources']:
            path = ref['path']
            text = sources.get(path)
            if text is None:
                text = (root/path).read_text(encoding='utf-8')
                sources[path] = text
            matches = [i for i,line in enumerate(text.splitlines(),1) if ref['contains'] in line]
            if len(matches) != 1:
                raise ValueError(f'Reviewed evidence locator missing/ambiguous: {ref}')
            refs.append(add(path,matches[0],'reviewed-chain'))
        candidates = [r for r in rust_defs[p,row['rust']['fn']] if r['module']==row['rust']['module']]
        if len(candidates) != 1:
            raise ValueError('Reviewed Rust definition missing/ambiguous: '+str(row))
        rust = dict(candidates[0])
        if 'region' in row['rust']:
            rust['region'] = row['rust']['region']
        mappings.append(dict(program=p,rva=row['rva'],rust=rust,cpp=row.get('cpp',[]),
                             confidence=row['confidence'],basis=row['basis'],evidence=refs,verified_rust=False))

    # Generated v1 kernels preserve their C++ names. The generator itself binds
    # these source files to the Rust definitions; ordinary same-name guesses do not.
    for (p,rva), definitions in sorted(cpp_defs.items()):
        attached = [m for m in mappings if m['program']==p and int(m['rva'],16)==rva]
        for cpp, eid in definitions:
            for m in attached:
                if cpp not in m['cpp']:
                    m['cpp'].append(cpp)
                    m['evidence'].append(eid)
            if not attached:
                generated = [r for r in rust_defs[p,cpp['fn']] if
                             '@generated' in sources[r['path']][:500] and p=='OLMSmoother']
                for rust in generated:
                    mappings.append(dict(program=p,rva=format(rva,'x'),rust=rust,cpp=[cpp],confidence='high',
                        basis='C++ address comment + same-name mechanically generated Rust translation',
                        evidence=[eid,add(rust['path'],rust['line'],'rust-definition'),
                                  add('rust/plugins/olm-smoother/tools/translate.py',1,'translation-provenance')],
                        verified_rust=False))
                if not generated:
                    mappings.append(dict(program=p,rva=format(rva,'x'),rust=None,cpp=[cpp],confidence='high',
                        basis='explicit C++ function name or adjacent address comment; may identify a component rather than the entire original body',evidence=[eid],verified_rust=False))

    # Validation is plugin-corpus qualification, not independent function proof.
    # Bind to the report hash and state the scope instead of manufacturing per-fn tests.
    qualification = json.loads(Path(__file__).with_name('qualification.json').read_text())
    for m in mappings:
        m['original_sha256'] = active[m['program']]['sha256']
        m['evidence'] = sorted(set(m['evidence']) | associations[m['program'],int(m['rva'],16)])
        if m['rust'] and m['program'] in qualification:
            q = qualification[m['program']]
            path = f"rust/plugins/{plugins[m['program']]}/VALIDATION.md"
            if q['contains'] not in sources[path]:
                raise ValueError('Qualification evidence changed: '+path)
            line = next(i for i,s in enumerate(sources[path].splitlines(),1) if q['contains'] in s)
            eid = add(path,line,'plugin-validation')
            m['evidence'] = sorted(set(m['evidence']+[eid]))
            m['verified_rust'] = True
            m['verification_scope'] = 'Existing plugin-level corpus; not an independent proof for this function. '+q['scope']
    mappings.sort(key=lambda m:(m['program'],int(m['rva'],16),json.dumps(m['rust'],sort_keys=True)))
    for p in programs:
        for f in p['functions']:
            f['evidence'] = sorted(associations[p['program'],int(f['rva'],16)])
    return mappings, evidence, dict(scanned_files=len(sources), skipped_over_4MiB=skipped,
        absent_directories=[d for d in ('disasm','decomp') if not (root/d).exists()],
        scope='notes/IR_*.md; core/mac text sources; tools/emulation text/reports excluding fixtures; disasm/decomp if present; Rust plugin src/VALIDATION and translators. Address mentions do not establish equivalence.')
