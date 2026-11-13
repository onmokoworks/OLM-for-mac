"""Snapshot-only knowledge extraction and conservative, provenance-preserving transfer."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time

from matching import match_functions
from runtime import HOME, atomic_json, files, open_project, start_jvm

HUMAN = {'USER_DEFINED', 'IMPORTED'}


def fingerprint(program, fun):
    """Keep instruction bytes, mask referenced addresses, retain referenced literals.

    Inspired by triage/TriageExport.java; format is hub-v1, not triage-compatible.
    No shape-only or name-only matches are automatically applied.
    """
    instructions = list(program.getListing().getInstructions(fun.getBody(), True))
    indices = {str(i.getAddress()): n for n, i in enumerate(instructions)}
    raw, normalized = hashlib.sha256(), hashlib.sha256()
    for instruction in instructions:
        data = bytearray(instruction.getBytes())
        raw.update(len(data).to_bytes(2, 'little')+data)
        targets = []
        for op in range(instruction.getNumOperands()):
            refs = [r for r in instruction.getOperandReferences(op)
                    if not r.isStackReference() and not r.isRegisterReference()]
            if not refs:
                continue
            mask = instruction.getPrototype().getOperandValueMask(op)
            if mask is not None:
                for n, byte in enumerate(bytes(mask.getBytes())[:len(data)]):
                    data[n] &= ~byte & 255
            for ref in refs:
                addr = ref.getToAddress()
                if str(addr) in indices:
                    identity = 'local:'+str(indices[str(addr)])
                elif ref.getReferenceType().isCall():
                    f = program.getFunctionManager().getFunctionAt(addr)
                    identity = 'call:'+ (str(f.getName(True)) if f and f.isExternal() else 'internal')
                else:
                    # Keep referenced bytes rather than silently treating changed constants as equal.
                    try:
                        import jpype
                        buf = jpype.JArray(jpype.JByte)(32)
                        length = program.getMemory().getBytes(addr, buf)
                        identity = 'data:'+bytes(buf[:length]).hex()
                    except Exception:
                        identity = 'unreadable:'+str(addr)
                targets.append(f'{op}:{ref.getReferenceType()}:{identity}')
        for n in range(len(data)):
            for reloc in program.getRelocationTable().getRelocations(instruction.getAddress().add(n)):
                size = len(reloc.getBytes()) if reloc.getBytes() is not None else program.getDefaultPointerSize()
                for k in range(n, min(len(data), n+size)):
                    data[k] = 0
        normalized.update((str(instruction.getMnemonicString())+':'+data.hex()+':'+repr(targets)+'\n').encode())
    return dict(raw_hash=raw.hexdigest() if instructions else None,
                normalized_hash=normalized.hexdigest() if instructions else None, instructions=len(instructions))


def function_rows(program, fingerprints=False):
    result = []
    for f in program.getFunctionManager().getFunctions(True):
        row = dict(address=str(f.getEntryPoint()), rva=int(f.getEntryPoint().subtract(program.getImageBase())),
                   name=str(f.getName()), namespace=str(f.getParentNamespace().getName(True)),
                   source=str(f.getSymbol().getSource()), signature=str(f.getSignature()),
                   signature_source=str(f.getSignatureSource()),
                   comment=str(f.getComment() or ''), repeatable_comment=str(f.getRepeatableComment() or ''))
        if fingerprints:
            row.update(fingerprint(program, f))
        result.append(row)
    return result


def extract(program, output):
    from ghidra.program.model.data import FileDataTypeManager, DataTypeConflictHandler
    from java.io import File
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    listing = program.getListing()
    comments = []
    for kind in range(5):
        for address in listing.getCommentAddressIterator(kind, program.getMemory(), True):
            comments.append(dict(address=str(address), kind=kind, text=str(listing.getComment(kind, address))))
    symbols = [dict(address=str(s.getAddress()), name=str(s.getName()),
                    namespace=str(s.getParentNamespace().getName(True)), source=str(s.getSource()),
                    type=str(s.getSymbolType())) for s in program.getSymbolTable().getAllSymbols(True)
               if str(s.getSource()) in HUMAN and not s.isExternal()]
    bookmarks = [dict(address=str(b.getAddress()), type=str(b.getTypeString()),
                      category=str(b.getCategory()), comment=str(b.getComment()))
                 for b in program.getBookmarkManager().getBookmarksIterator()]
    types = [dict(path=str(dt.getPathName()), length=int(dt.getLength()), definition=str(dt))
             for dt in program.getDataTypeManager().getAllDataTypes()]
    archive_path = output/'types.gdt'
    if not archive_path.exists():
        archive = FileDataTypeManager.createFileArchive(File(str(archive_path)))
        tx = archive.startTransaction('Knowledge export')
        ok = False
        try:
            for dt in program.getDataTypeManager().getAllDataTypes():
                archive.resolve(dt, DataTypeConflictHandler.KEEP_HANDLER)
            ok = True
        finally:
            archive.endTransaction(tx, ok)
            if ok:
                archive.save()
            archive.close()
    data = dict(schema=1, program=str(program.getName()), sha256=str(program.getExecutableSHA256()),
                language=str(program.getLanguageID()), image_base=str(program.getImageBase()),
                functions=function_rows(program), symbols=symbols, comments=comments,
                bookmarks=bookmarks, types=types, types_archive=str(archive_path))
    atomic_json(output/'knowledge.json', data)
    return data


def transfer(source, target, provenance, output, exported=None):
    from ghidra.program.model.symbol import SourceType
    from ghidra.program.model.data import DataTypeConflictHandler
    from ghidra.app.cmd.function import ApplyFunctionSignatureCmd
    from ghidra.util.task import TaskMonitor
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    data = exported or extract(source, output/'source')
    if (str(source.getLanguageID()) != str(target.getLanguageID()) or
        str(source.getCompilerSpec().getCompilerSpecID()) != str(target.getCompilerSpec().getCompilerSpecID())):
        report = dict(source=provenance, target=str(target.getName()), skipped='different instruction language/compiler ABI',
                      source_language=str(source.getLanguageID()), counts={}, conflicts=[], matched=0)
        atomic_json(output/'match-report.json', report)
        return report
    identical = bool(source.getExecutableSHA256()) and str(source.getExecutableSHA256()) == str(target.getExecutableSHA256())
    print(f'Matching {source.getName()} -> {target.getName()} identical={identical}', flush=True)
    src_rows = data['functions'] if identical else function_rows(source, True)
    dst_rows = function_rows(target, not identical and bool(src_rows)) if src_rows else []
    matching = match_functions(src_rows, dst_rows, identical)
    if not identical and not matching['matches']:
        report = dict(source=provenance, target=str(target.getName()), skipped='no confident function matches',
                      counts={}, conflicts=[], matched=0, matching=matching)
        atomic_json(output/'match-report.json', report)
        return {k:v for k,v in report.items() if k != 'matching'}
    counts, conflicts = Counter(), []
    tfm, sfm = target.getFunctionManager(), source.getFunctionManager()
    af = target.getAddressFactory()
    def addr(text):
        return af.getAddress(text)
    def mapped(text):
        a = source.getAddressFactory().getAddress(text)
        if identical:
            return target.getImageBase().add(a.subtract(source.getImageBase()))
        f = sfm.getFunctionContaining(a)
        if f is None or str(f.getEntryPoint()) not in matching['matches']:
            return None
        match = matching['matches'][str(f.getEntryPoint())]
        # Raw-byte equality guarantees interior instruction layout. Normalized hash
        # equality is suitable for entry annotations only (data/code movement is possible).
        delta = a.subtract(f.getEntryPoint())
        if delta != 0 and match['method'] != 'raw_hash':
            return None
        return addr(match['target']).add(delta)
    def namespace(path):
        ns = target.getGlobalNamespace()
        for part in path.split('::'):
            if part in ('', 'Global'):
                continue
            found = target.getSymbolTable().getNamespace(part, ns)
            ns = found or target.getSymbolTable().createNameSpace(ns, part, SourceType.USER_DEFINED)
        return ns
    tx = target.startTransaction('Hub knowledge transfer')
    committed = False
    try:
        manager = target.getDataTypeManager()
        for dt in source.getDataTypeManager().getAllDataTypes():
            existing = manager.getDataType(dt.getPathName())
            if existing is not None and not existing.isEquivalent(dt):
                conflicts.append(dict(kind='type', path=str(dt.getPathName())))
            elif existing is None:
                manager.resolve(dt, DataTypeConflictHandler.KEEP_HANDLER)
                counts['types'] += 1
        for row in src_rows:
            match = matching['matches'].get(row['address'])
            if match is None:
                continue
            f = tfm.getFunctionAt(addr(match['target']))
            old = sfm.getFunctionAt(source.getAddressFactory().getAddress(row['address']))
            if row['source'] in HUMAN:
                if str(f.getSymbol().getSource()) in HUMAN and str(f.getName(True)) != str(old.getName(True)):
                    conflicts.append(dict(kind='name', address=str(f.getEntryPoint()), existing=str(f.getName(True)), incoming=str(old.getName(True))))
                elif str(f.getName(True)) != str(old.getName(True)):
                    f.setParentNamespace(namespace(row['namespace']))
                    f.setName(row['name'], SourceType.USER_DEFINED)
                    counts['names'] += 1
            if row['signature_source'] in HUMAN and str(f.getSignature()) != str(old.getSignature()):
                if str(f.getSignatureSource()) in HUMAN:
                    conflicts.append(dict(kind='signature', address=str(f.getEntryPoint())))
                else:
                    # Do not let a signature application rename an existing human symbol.
                    keep_name, keep_ns, keep_source = f.getName(), f.getParentNamespace(), f.getSymbol().getSource()
                    cmd = ApplyFunctionSignatureCmd(f.getEntryPoint(), old.getSignature(), SourceType.USER_DEFINED)
                    if not cmd.applyTo(target, TaskMonitor.DUMMY):
                        raise RuntimeError(str(cmd.getStatusMsg()))
                    f.setParentNamespace(keep_ns)
                    f.setName(keep_name, keep_source)
                    counts['signatures'] += 1
            for field, get, set_ in [('comment', f.getComment, f.setComment),
                                     ('repeatable_comment', f.getRepeatableComment, f.setRepeatableComment)]:
                text = row[field]
                current = str(get() or '')
                if text and text not in current:
                    set_((current+'\n' if current else '')+f'[Imported {provenance}]\n'+text)
                    counts['comments'] += 1
        for symbol in data['symbols']:
            if symbol['type'] != 'Label':
                continue
            a = mapped(symbol['address'])
            if a is None:
                counts['unmapped_symbols'] += 1
                continue
            existing = target.getSymbolTable().getPrimarySymbol(a)
            if existing and str(existing.getSource()) in HUMAN and str(existing.getName()) != symbol['name']:
                conflicts.append(dict(kind='label', address=str(a), incoming=symbol['name']))
            elif not existing or str(existing.getName()) != symbol['name']:
                target.getSymbolTable().createLabel(a, symbol['name'], namespace(symbol['namespace']), SourceType.USER_DEFINED)
                counts['names'] += 1
        for comment in data['comments']:
            a = mapped(comment['address'])
            if a is None:
                counts['unmapped_comments'] += 1
                continue
            current = str(target.getListing().getComment(comment['kind'], a) or '')
            if comment['text'] not in current:
                target.getListing().setComment(a, comment['kind'], (current+'\n' if current else '')+
                    f'[Imported {provenance}]\n'+comment['text'])
                counts['comments'] += 1
        for bookmark in data['bookmarks']:
            a = mapped(bookmark['address'])
            if a is None:
                counts['unmapped_bookmarks'] += 1
                continue
            bm = target.getBookmarkManager()
            old = bm.getBookmark(a, bookmark['type'], bookmark['category'])
            if old and str(old.getComment()) != bookmark['comment']:
                conflicts.append(dict(kind='bookmark', address=str(a)))
            elif old is None:
                bm.setBookmark(a, bookmark['type'], bookmark['category'], bookmark['comment'])
                counts['bookmarks'] += 1
        report = dict(source=provenance, source_sha256=str(source.getExecutableSHA256()),
                      target=str(target.getName()), target_sha256=str(target.getExecutableSHA256()),
                      counts=dict(counts), conflicts=conflicts, matched=len(matching['matches']),
                      matching=matching, timestamp=time.time())
        key = hashlib.sha256(provenance.encode()).hexdigest()
        target.getOptions('OLM Hub Provenance').setString(key, json.dumps(report))
        committed = True
    finally:
        target.endTransaction(tx, committed)
    atomic_json(output/'match-report.json', report)
    return {k: v for k, v in report.items() if k != 'matching'}


def import_notes(project, targets):
    """Attach address-grounded IR/validation excerpts, including their source path and line."""
    repo = Path(__file__).resolve().parents[3]
    reports = []
    aliases = {'DistanceGradation': 'OLMDistanceGradation', 'ColorKeep': 'ColorKeep'}
    for name, p in targets.items():
        marker = aliases.get(name, name)
        paths = sorted((repo/'notes').glob(f'IR_{marker}*.md'))
        # Rust validation files are included only when their text identifies this binary.
        paths += [path for path in (repo/'rust/plugins').glob('*/VALIDATION.md')
                  if name in path.read_text(encoding='utf-8')]
        count = 0
        tx = p.startTransaction('Source mapping comments')
        try:
            for path in paths:
                for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                    addresses = re.findall(r'(?:FUN_|0x)(18[0-9a-fA-F]{7})\b', line)
                    for address in set(addresses):
                        f = p.getFunctionManager().getFunctionAt(p.getAddressFactory().getAddress(address))
                        if f is None:
                            continue
                        text = f'[OLM Rust/C++ mapping: {path.relative_to(repo).as_posix()}:{number}]\n{line}'
                        previous = str(f.getComment() or '')
                        if text not in previous:
                            f.setComment(previous+('\n' if previous else '')+text)
                            count += 1
            p.endTransaction(tx, True)
        except BaseException:
            p.endTransaction(tx, False)
            raise
        project.save(p)
        reports.append(dict(program=name, mapping_comments=count))
    atomic_json(HOME/'reports/mapping-notes.json', reports)


def import_knowledge():
    start_jvm()
    from ghidra.base.project import GhidraProject
    from ghidra.util.task import TaskMonitor
    from java.lang import Object
    project = open_project()
    targets = {str(df.getName()): project.openProgram('/', str(df.getName()), False)
               for df in files(project.getRootFolder()) if str(df.getContentType()) == 'Program'}
    target_hashes = {str(p.getExecutableSHA256()): n for n, p in targets.items()}
    reports = []
    try:
        for snapshot_path in json.loads((HOME/'snapshots/projects.json').read_text()):
            path = Path(snapshot_path).resolve()
            if not path.is_relative_to((HOME/'snapshots').resolve()):
                raise ValueError('Source must be a snapshot')
            source_project = GhidraProject.openProject(str(path.parent), path.stem, True)
            try:
                for df in files(source_project.getRootFolder()):
                    if str(df.getContentType()) != 'Program':
                        continue
                    name = Path(str(df.getName())).stem.removesuffix('_pe64')
                    canonical = name.removeprefix('OLM') if name == 'OLMDistanceGradation' else name
                    # Cheap persisted metadata also catches renamed domain files.
                    metadata_hash = str(df.getMetadata().get('Executable SHA256'))
                    canonical = target_hashes.get(metadata_hash, canonical)
                    if canonical not in targets:
                        continue
                    consumer = Object()
                    source = None
                    provenance = str(path)+':'+str(df.getPathname())
                    export_dir = HOME/'knowledge'/hashlib.sha256(provenance.encode()).hexdigest()[:16]
                    try:
                        source = df.getReadOnlyDomainObject(consumer, -1, TaskMonitor.DUMMY)
                        exported = extract(source, export_dir)
                        # Hash takes priority over file-name selection.
                        matches = [(n,p) for n,p in targets.items()
                                   if str(p.getExecutableSHA256()) == str(source.getExecutableSHA256())]
                        if not matches:
                            matches = [(canonical, targets[canonical])]
                        for n, target in matches:
                            report = transfer(source, target, provenance, export_dir/n, exported)
                            project.save(target)
                            reports.append(report)
                            print(json.dumps(report), flush=True)
                    except Exception as error:
                        report = dict(source=provenance, target=canonical, error=str(error))
                        reports.append(report)
                        print(json.dumps(report), flush=True)
                    finally:
                        if source is not None:
                            source.release(consumer)
                        atomic_json(HOME/'reports/knowledge-import.json', reports)
            finally:
                source_project.close()
        import_notes(project, targets)
    finally:
        project.close()


if __name__ == '__main__':
    import_knowledge()
