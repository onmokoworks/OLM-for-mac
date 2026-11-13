"""Multi-program API. All Program access goes through per-program read/write gates."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import threading
import time
import uuid

from decompiler_pool import DecompilerPool
from runtime import HOME, RWLock, atomic_json, files, import_program, open_project, start_jvm


class Hub:
    def __init__(self, workers=3):
        if not 1 <= workers <= 3:
            raise ValueError('workers must be 1..3')
        start_jvm()
        from ghidra.util.task import TaskMonitor
        self.monitor = TaskMonitor.DUMMY
        self.project = open_project()
        self.programs = {}
        self.locks = {}
        self.pools = {}
        self.catalog = threading.RLock()
        self.importer = threading.Lock()
        self.saver = threading.Lock()
        self.audit_lock = threading.Lock()
        self.workers = workers
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='decompile')
        for df in files(self.project.getRootFolder()):
            if str(df.getContentType()) == 'Program':
                program = self.project.openProgram(str(df.getParent().getPathname()), str(df.getName()), False)
                self._register(str(df.getName()), program)

    def _register(self, name, program):
        from ghidra.app.decompiler import DecompInterface, DecompileOptions
        def factory():
            dec = DecompInterface()
            options = DecompileOptions()
            options.grabFromProgram(program)
            dec.setOptions(options)
            if not dec.openProgram(program):
                dec.dispose()
                raise RuntimeError('Cannot open decompiler')
            return dec
        self.programs[name] = program
        self.locks[name] = RWLock()
        self.pools[name] = DecompilerPool(factory, size=self.workers)

    def selected(self, programs=None):
        with self.catalog:
            names = list(self.programs) if not programs else list(programs)
            for name in names:
                if name not in self.programs:
                    raise ValueError(f'Unknown program: {name}')
            return [(n, self.programs[n]) for n in names]

    def address(self, program, value):
        address = program.getAddressFactory().getAddress(str(value).removeprefix('0x'))
        if address is None:
            raise ValueError(f'Invalid address: {value}')
        return address

    def function(self, program, value):
        # Prefer explicit addresses, otherwise require one unambiguous name.
        if re.fullmatch(r'(?:0x)?[0-9a-fA-F]{6,}', value):
            fun = program.getFunctionManager().getFunctionAt(self.address(program, value))
            if fun is not None:
                return fun
        found = [f for f in program.getFunctionManager().getFunctions(True)
                 if str(f.getName()) == value or str(f.getName(True)) == value]
        if len(found) != 1:
            raise ValueError(f'Function not found or ambiguous: {value} ({len(found)} matches)')
        return found[0]

    @staticmethod
    def row(name, fun):
        return dict(program=name, address=str(fun.getEntryPoint()), name=str(fun.getName(True)),
                    signature=str(fun.getSignature()), size=int(fun.getBody().getNumAddresses()),
                    source=str(fun.getSymbol().getSource()), comment=str(fun.getComment() or ''))

    def programs_list(self):
        from ghidra.program.util import GhidraProgramUtilities
        result = []
        for name, p in self.selected():
            with self.locks[name].read():
                internal = sum(1 for _ in p.getFunctionManager().getFunctions(True))
                result.append(dict(name=name, sha256=str(p.getExecutableSHA256()),
                    functions=int(p.getFunctionManager().getFunctionCount()),
                    internal_functions=internal,
                    external_functions=int(p.getFunctionManager().getFunctionCount())-internal,
                    language=str(p.getLanguageID()), analyzed=bool(GhidraProgramUtilities.isAnalyzed(p))))
        return result

    def list_functions(self, programs=None, query='', offset=0, limit=100):
        if offset < 0 or not 1 <= limit <= 10000:
            raise ValueError('offset >= 0; limit 1..10000')
        rows, total = [], 0
        for name, p in self.selected(programs):
            with self.locks[name].read():
                for f in p.getFunctionManager().getFunctions(True):
                    if query.casefold() not in str(f.getName(True)).casefold():
                        continue
                    if offset <= total < offset + limit:
                        rows.append(self.row(name, f))
                    total += 1
        return dict(total=total, offset=offset, functions=rows)

    def _decompile(self, item, timeout):
        name = item['program']
        self.selected([name])
        with self.locks[name].read():
            p = self.programs[name]
            f = self.function(p, item['function'])
            with self.pools[name].acquire(timeout=timeout+30) as dec:
                result = dec.decompileFunction(f, timeout, self.monitor)
                row = self.row(name, f)
                row['completed'] = bool(result.decompileCompleted())
                row['error'] = str(result.getErrorMessage())
                row['c'] = str(result.getDecompiledFunction().getC()) if row['completed'] else None
                return row

    def decompile_batch(self, items, parallel=True, timeout=60):
        if not 1 <= timeout <= 300 or len(items) > 10000:
            raise ValueError('timeout 1..300 and at most 10000 items')
        started = time.perf_counter()
        def run(item):
            try:
                return self._decompile(item, timeout)
            except Exception as error:
                return dict(**item, completed=False, error=str(error), c=None)
        if parallel:
            results = list(self.executor.map(run, items))
        else:
            results = [run(item) for item in items]
        return dict(seconds=time.perf_counter()-started, results=results)

    def xrefs(self, program, address):
        self.selected([program])
        with self.locks[program].read():
            p = self.programs[program]
            addr = self.address(p, address)
            def rows(refs):
                return [dict(source=str(r.getFromAddress()), target=str(r.getToAddress()),
                             type=str(r.getReferenceType())) for r in refs]
            return dict(to=rows(p.getReferenceManager().getReferencesTo(addr)),
                        **{'from': rows(p.getReferenceManager().getReferencesFrom(addr))})

    def call_graph(self, program, functions=None, depth=1):
        if not 0 <= depth <= 8:
            raise ValueError('depth must be 0..8')
        self.selected([program])
        with self.locks[program].read():
            p = self.programs[program]
            frontier = ([self.function(p, f) for f in functions] if functions else
                        list(p.getFunctionManager().getFunctions(True)))
            nodes, edges = {}, set()
            for level in range(depth+1):
                next_frontier = []
                for f in frontier:
                    a = str(f.getEntryPoint())
                    if a in nodes:
                        continue
                    nodes[a] = self.row(program, f)
                    for callee in f.getCalledFunctions(self.monitor):
                        edges.add((a, str(callee.getEntryPoint())))
                        if level < depth:
                            next_frontier.append(callee)
                frontier = next_frontier
            return dict(nodes=list(nodes.values()), edges=sorted(edges), indirect_calls='not resolved exhaustively')

    def data_types(self, program, query='', offset=0, limit=100):
        from ghidra.program.model.data import Composite
        self.selected([program])
        if offset < 0 or not 1 <= limit <= 1000:
            raise ValueError('offset >= 0; limit 1..1000')
        with self.locks[program].read():
            result, total = [], 0
            for dt in self.programs[program].getDataTypeManager().getAllDataTypes():
                if query.casefold() not in str(dt.getPathName()).casefold():
                    continue
                if offset <= total < offset+limit:
                    row = dict(path=str(dt.getPathName()), length=int(dt.getLength()), definition=str(dt))
                    if isinstance(dt, Composite):
                        row['fields'] = [dict(name=str(c.getFieldName()), offset=int(c.getOffset()),
                            type=str(c.getDataType().getPathName()), comment=str(c.getComment() or ''))
                            for c in dt.getComponents()]
                    result.append(row)
                total += 1
            return dict(total=total, types=result)

    def _audit(self, event):
        with self.audit_lock:
            path = HOME/'logs/transactions.jsonl'
            with path.open('a', encoding='utf-8') as out:
                out.write(json.dumps(event, ensure_ascii=False)+'\n')

    def bulk_edit(self, rows, provenance='API client'):
        """Atomic per program, not across programs. Invalid rows roll back that program."""
        from ghidra.program.model.symbol import SourceType
        from ghidra.app.cmd.function import ApplyFunctionSignatureCmd
        from ghidra.app.util.parser import FunctionSignatureParser
        groups = defaultdict(list)
        for row in rows:
            if set(row)-{'program', 'function', 'name', 'signature', 'comment', 'expected_name'}:
                raise ValueError('Unknown edit field')
            groups[row['program']].append(row)
        self.selected(list(groups))
        result = []
        for name, edits in groups.items():
            with self.locks[name].write():
                p = self.programs[name]
                tx = p.startTransaction('Hub bulk edit')
                committed = False
                event = dict(id=uuid.uuid4().hex, time=time.time(), program=name,
                             provenance=provenance, rows=edits)
                try:
                    for edit in edits:
                        f = self.function(p, edit['function'])
                        if 'expected_name' in edit and str(f.getName()) != edit['expected_name']:
                            raise ValueError('Concurrent edit: expected_name differs')
                        if 'name' in edit:
                            if not edit['name'] or any(c.isspace() for c in edit['name']):
                                raise ValueError('Name must be nonempty without whitespace')
                            f.setName(edit['name'], SourceType.USER_DEFINED)
                        if 'signature' in edit:
                            parser = FunctionSignatureParser(p.getDataTypeManager(), None)
                            signature = parser.parse(f.getSignature(), edit['signature'])
                            cmd = ApplyFunctionSignatureCmd(f.getEntryPoint(), signature, SourceType.USER_DEFINED)
                            if not cmd.applyTo(p, self.monitor):
                                raise ValueError(str(cmd.getStatusMsg()))
                        if 'comment' in edit:
                            f.setComment(edit['comment'])
                    p.getOptions('OLM Hub Provenance').setString(event['id'], json.dumps(event))
                    committed = True
                finally:
                    p.endTransaction(tx, committed)
                    # Even rollback can invalidate a decompiler's internal symbol cache.
                    self.pools[name].invalidate_all()
                with self.saver:
                    self.project.save(p)
                self._audit(event)
                result.append(dict(program=name, edited=len(edits), transaction=event['id'], saved=True))
        return result

    def export_function(self, program, function):
        self.selected([program])
        # Use a single read gate for C, signature, disassembly and callees consistency.
        with self.locks[program].read():
            p = self.programs[program]
            f = self.function(p, function)
            with self.pools[program].acquire(timeout=90) as dec:
                result = dec.decompileFunction(f, 60, self.monitor)
                if not result.decompileCompleted():
                    raise RuntimeError(str(result.getErrorMessage()))
                metadata = self.row(program, f)
                metadata['callees'] = [self.row(program, c) for c in f.getCalledFunctions(self.monitor)]
                dest = HOME/'exports'/uuid.uuid4().hex
                dest.mkdir(parents=True)
                (dest/'function.c').write_text(str(result.getDecompiledFunction().getC()), encoding='utf-8')
                (dest/'disassembly.txt').write_text('\n'.join(
                    f'{i.getAddress()}  {i}' for i in p.getListing().getInstructions(f.getBody(), True)), encoding='utf-8')
                atomic_json(dest/'function.json', metadata)
                return dict(directory=str(dest), files=['function.c', 'disassembly.txt', 'function.json'])

    def add_version(self, aex, like):
        from knowledge import transfer
        from runtime import sha256
        self.selected([like])
        path = Path(aex).resolve()
        name = like.split('@')[0]+'@'+sha256(path)[:12]
        with self.importer:
            if name in self.programs:
                report_path = HOME/'reports'/name/'match-report.json'
                if not report_path.exists():
                    raise RuntimeError(f'{name} exists without a completed match report; inspect before reuse')
                return dict(program=name, reused=True, report_path=str(report_path))
            with self.saver:
                p = import_program(self.project, path, name)
            with self.locks[like].read():
                report = transfer(self.programs[like], p, f'add-version:{like}', HOME/'reports'/name)
            with self.saver:
                self.project.save(p)
            with self.catalog:
                self._register(name, p)
            return dict(program=name, report=report)

    def add_program(self, aex, name=None):
        path = Path(aex).resolve()
        name = name or path.stem
        if not re.fullmatch(r'[A-Za-z0-9_.@-]+', name):
            raise ValueError('Program name must use letters, numbers, _, ., @ or -')
        with self.importer:
            if name in self.programs:
                raise ValueError('Program exists; use add-version')
            with self.saver:
                p = import_program(self.project, path, name)
            with self.catalog:
                self._register(name, p)
        return {'program': name, 'analyzed': True}

    def reset_decompilers(self):
        """Cold-pool benchmark support; waits for active readers before disposal."""
        for name, _ in self.selected():
            with self.locks[name].write():
                pool = self.pools[name]
                pool.dispose()
                self.pools[name] = DecompilerPool(pool._factory, size=self.workers)
        return {'reset': True}

    def close(self):
        self.executor.shutdown(wait=True, cancel_futures=True)
        try:
            for name, program in self.selected():
                with self.locks[name].write():
                    self.pools[name].dispose()
                    self.project.save(program)
        finally:
            self.project.close()
