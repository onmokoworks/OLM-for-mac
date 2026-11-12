"""Real JVM regression: seeded human knowledge, conflicts and different-hash carry-over."""
import json
from pathlib import Path
import tempfile

from runtime import HOME, ORIGINALS, atomic_json, import_program, open_project, start_jvm
from knowledge import transfer


def main():
    start_jvm()
    from ghidra.program.model.symbol import SourceType
    from ghidra.program.model.data import StructureDataType, IntegerDataType, CategoryPath
    from ghidra.program.model.listing import CodeUnit
    from ghidra.app.cmd.function import ApplyFunctionSignatureCmd
    from ghidra.app.util.parser import FunctionSignatureParser
    from ghidra.util.task import TaskMonitor
    import pefile
    with tempfile.TemporaryDirectory(prefix='knowledge-', dir=HOME) as temporary:
        folder = Path(temporary)
        source_file = ORIGINALS/'OLMBlur.aex'
        blob = bytearray(source_file.read_bytes())
        pe = pefile.PE(data=bytes(blob))
        patch_offset = pe.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum')
        pe.close()
        blob[patch_offset] ^= 1
        patched = folder/'patched.aex'
        patched.write_bytes(blob)
        project = open_project(folder)
        try:
            source = import_program(project, source_file, 'fixture-source')
            target = import_program(project, patched, 'fixture-target')
            candidates = [f for f in source.getFunctionManager().getFunctions(True)
                          if not f.isThunk() and f.getBody().getNumAddresses() > 100]
            fun = candidates[0]
            entry = fun.getEntryPoint()
            tx = source.startTransaction('Seed fixture knowledge')
            try:
                ns = source.getSymbolTable().createNameSpace(source.getGlobalNamespace(), 'Human', SourceType.USER_DEFINED)
                fun.setParentNamespace(ns)
                fun.setName('KnownKernel', SourceType.USER_DEFINED)
                struct = StructureDataType(CategoryPath('/OLMFixture'), 'KnownLayout', 0)
                struct.add(IntegerDataType.dataType, 'count', 'known field')
                source.getDataTypeManager().addDataType(struct, None)
                parser = FunctionSignatureParser(source.getDataTypeManager(), None)
                signature = parser.parse(fun.getSignature(), 'int KnownKernel(KnownLayout *state, int count)')
                cmd = ApplyFunctionSignatureCmd(entry, signature, SourceType.USER_DEFINED)
                assert cmd.applyTo(source, TaskMonitor.DUMMY), str(cmd.getStatusMsg())
                fun.setComment('Seeded human function comment')
                source.getListing().setComment(entry.add(3), CodeUnit.EOL_COMMENT, 'Seeded interior comment')
                source.getBookmarkManager().setBookmark(entry, 'Note', 'OLMFixture', 'Seeded bookmark')
                source.getSymbolTable().createLabel(entry.add(3), 'known_inner', ns, SourceType.USER_DEFINED)
                source.endTransaction(tx, True)
            except BaseException:
                source.endTransaction(tx, False)
                raise
            report = transfer(source, target, 'seeded-fixture', folder/'report')
            target_fun = target.getFunctionManager().getFunctionAt(entry)
            assert str(target_fun.getName()) == 'KnownKernel'
            assert str(target_fun.getParentNamespace().getName()) == 'Human'
            assert 'Seeded human' in str(target_fun.getComment())
            assert target.getDataTypeManager().getDataType('/OLMFixture/KnownLayout') is not None
            assert 'KnownLayout' in str(target_fun.getSignature())
            assert target.getBookmarkManager().getBookmark(entry, 'Note', 'OLMFixture') is not None
            assert 'Seeded interior' in str(target.getListing().getComment(CodeUnit.EOL_COMMENT, entry.add(3)))
            tx = target.startTransaction('Seed conflicting human name')
            target_fun.setName('KeepHumanName', SourceType.USER_DEFINED)
            target.endTransaction(tx, True)
            conflict = transfer(source, target, 'seeded-fixture-repeat', folder/'conflict')
            assert str(target_fun.getName()) == 'KeepHumanName'
            assert any(c['kind'] == 'name' for c in conflict['conflicts'])
            project.save(source)
            project.save(target)
            atomic_json(HOME/'reports/knowledge-fixture.json', dict(transfer=report, conflict=conflict,
                assertions='name, namespace, signature, structure, EOL/comment, bookmark, conflict all passed'))
            print(json.dumps(report), flush=True)
        finally:
            project.close()


if __name__ == '__main__':
    main()
