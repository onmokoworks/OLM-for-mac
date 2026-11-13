"""Read snapshot inventories; never opens the original project paths."""
import json
from pathlib import Path
from runtime import HOME, ORIGINALS, atomic_json, files, sha256, start_jvm


def inventory():
    start_jvm()
    from ghidra.base.project import GhidraProject
    from ghidra.util.task import TaskMonitor
    from java.lang import Object
    result = []
    known_hashes = {sha256(p) for p in ORIGINALS.glob('*.aex')}
    for path in json.loads((HOME/'snapshots/projects.json').read_text()):
        path = Path(path)
        if not path.resolve().is_relative_to((HOME/'snapshots').resolve()):
            raise ValueError('Only snapshots may be opened')
        project = GhidraProject.openProject(str(path.parent), path.stem, True)
        try:
            for df in files(project.getRootFolder()):
                if str(df.getContentType()) != 'Program':
                    continue
                if ('.aex' not in str(df.getName()).lower() and
                    str(df.getMetadata().get('Executable SHA256')) not in known_hashes):
                    continue
                consumer = Object()
                try:
                    p = df.getReadOnlyDomainObject(consumer, -1, TaskMonitor.DUMMY)
                except Exception as error:
                    row = dict(project=str(path), path=str(df.getPathname()), error=str(error))
                    result.append(row)
                    print(json.dumps(row), flush=True)
                    continue
                try:
                    row = dict(project=str(path), path=str(df.getPathname()),
                        name=str(p.getName()), sha256=str(p.getExecutableSHA256()),
                        language=str(p.getLanguageID()), compiler=str(p.getCompilerSpec().getCompilerSpecID()),
                        functions=int(p.getFunctionManager().getFunctionCount()),
                        user_symbols=sum(str(s.getSource())=='USER_DEFINED' for s in p.getSymbolTable().getAllSymbols(True)))
                    result.append(row)
                    print(json.dumps(row), flush=True)
                finally:
                    p.release(consumer)
        finally:
            project.close()
    atomic_json(HOME/'reports/source-inventory.json', result)


if __name__ == '__main__':
    inventory()
