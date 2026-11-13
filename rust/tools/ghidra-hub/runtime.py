"""Headless JVM/project primitives. Never opens a user project for update."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import threading
import time

HOME = Path('D:/olm-rs-ghidra')
GHIDRA = Path('C:/ghidra_12/ghidra_12.0.3_PUBLIC')
ORIGINALS = Path('D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex')


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, path)


def sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class RWLock:
    """Writer-preferring lock; readers can run concurrently, including decompilers."""
    def __init__(self):
        self.condition = threading.Condition()
        self.readers = self.waiting = 0
        self.writer = False

    @contextlib.contextmanager
    def read(self):
        with self.condition:
            self.condition.wait_for(lambda: not self.writer and not self.waiting)
            self.readers += 1
        try:
            yield
        finally:
            with self.condition:
                self.readers -= 1
                self.condition.notify_all()

    @contextlib.contextmanager
    def write(self):
        with self.condition:
            self.waiting += 1
            try:
                self.condition.wait_for(lambda: not self.writer and not self.readers)
                self.writer = True
            finally:
                self.waiting -= 1
        try:
            yield
        finally:
            with self.condition:
                self.writer = False
                self.condition.notify_all()


def start_jvm(home=HOME):
    import pyghidra
    if pyghidra.started():
        return
    os.environ['JAVA_HOME'] = os.environ.get('OLM_GHIDRA_JAVA_HOME', 'C:/Users/optim/jdks/temurin-21')
    from pyghidra.launcher import HeadlessPyGhidraLauncher
    class HubLauncher(HeadlessPyGhidraLauncher):
        def _launch(self):
            from ghidra.framework import Application, HeadlessGhidraApplicationConfiguration
            from java.io import File
            config = HeadlessGhidraApplicationConfiguration()
            (Path(home)/'logs').mkdir(parents=True, exist_ok=True)
            config.setApplicationLogFile(File(str(Path(home)/'logs'/f'ghidra-{os.getpid()}.log')))
            config.setScriptLogFile(File(str(Path(home)/'logs'/f'scripts-{os.getpid()}.log')))
            Application.initializeApplication(self._layout, config)
    launcher = HubLauncher(install_dir=GHIDRA)
    for directory in ['cache', 'settings', 'tmp']:
        (Path(home)/directory).mkdir(parents=True, exist_ok=True)
    launcher.add_vmargs('-Xmx12G', '-XX:ActiveProcessorCount=3',
                        '-Djava.awt.headless=true',
                        f'-Dapplication.cachedir={home}/cache',
                        f'-Dapplication.settingsdir={home}/settings',
                        f'-Dapplication.tempdir={home}/tmp')
    launcher.start()


class ProjectOwner:
    """Own raw Programs without GhidraProject's hidden, permanent batch transaction.

    GhidraProject.openProgram starts an outer transaction; nesting a rollback
    inside it does not restore reads until the outer transaction ends. The hub
    must own the actual transaction boundary, so use DomainFile directly.
    """
    def __init__(self, project):
        from java.lang import Object
        from ghidra.util.task import TaskMonitor
        self.base = project
        self.consumer = Object()
        self.monitor = TaskMonitor.DUMMY
        self.opened = set()

    def getRootFolder(self):
        return self.base.getRootFolder()

    def openProgram(self, folder_path, name, read_only=False):
        folder = self.getRootFolder()
        for part in folder_path.strip('/').split('/'):
            if part:
                folder = folder.getFolder(part)
        df = folder.getFile(name)
        for program in self.opened:
            if program.getDomainFile() == df:
                return program
        if read_only:
            p = df.getReadOnlyDomainObject(self.consumer, -1, self.monitor)
        else:
            p = df.getDomainObject(self.consumer, True, False, self.monitor)
        self.opened.add(p)
        return p

    def importProgram(self, path):
        return self.base.importProgram(path)

    def saveAs(self, p, folder, name, overwrite):
        self.base.saveAs(p, folder, name, overwrite)
        p.addConsumer(self.consumer)
        self.base.close(p)  # Ends GhidraProject's outer transaction and releases its consumer.
        self.opened.add(p)
        if p.getCurrentTransactionInfo() is not None:
            raise RuntimeError('Unexpected inherited transaction')

    def save(self, p):
        if p.getCurrentTransactionInfo() is not None:
            raise RuntimeError('Refusing to save an open transaction')
        p.getDomainFile().save(self.monitor)

    def close(self, p=None):
        if p is not None:
            if p in self.opened:
                p.release(self.consumer)
                self.opened.remove(p)
            return
        try:
            for program in list(self.opened):
                self.close(program)
        finally:
            self.base.close()


def open_project(home=HOME):
    from ghidra.base.project import GhidraProject
    home = Path(home).resolve()
    # All writable projects are restricted to the explicitly owned data directory.
    if not home.is_relative_to(HOME.resolve()):
        raise ValueError('Writable project must be inside D:/olm-rs-ghidra')
    home.mkdir(parents=True, exist_ok=True)
    if (home / 'OLM-rs.gpr').exists():
        return ProjectOwner(GhidraProject.openProject(str(home), 'OLM-rs', True))
    if (home/'OLM-rs.rep').exists():
        raise ValueError('Refusing to replace a project repository with a missing .gpr')
    return ProjectOwner(GhidraProject.createProject(str(home), 'OLM-rs', False))


def files(folder):
    yield from folder.getFiles()
    for child in folder.getFolders():
        yield from files(child)


def analyze(project, program):
    from ghidra.program.util import GhidraProgramUtilities
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.app.script import GhidraScriptUtil
    if GhidraProgramUtilities.isAnalyzed(program):
        return False
    tx = program.startTransaction('Hub full auto-analysis')
    ok = False
    GhidraScriptUtil.acquireBundleHostReference()
    try:
        program.getOptions('Analyzers').setBoolean('PDB Universal', False)
        FlatProgramAPI(program).analyzeAll(program)
        GhidraProgramUtilities.markProgramAnalyzed(program)
        ok = True
    finally:
        GhidraScriptUtil.releaseBundleHostReference()
        program.endTransaction(tx, ok)
    project.save(program)
    return True


def import_program(project, path, name=None):
    from java.io import File
    path = Path(path).resolve()
    name = name or path.stem
    existing = project.getRootFolder().getFile(name)
    if existing:
        program = project.openProgram('/', name, False)
        if str(program.getExecutableSHA256()).lower() != sha256(path):
            raise ValueError(f'{name} exists with different hash; use add-version')
    else:
        program = project.importProgram(File(str(path)))
        if program is None:
            raise ValueError(f'Import failed: {path}')
        project.saveAs(program, '/', name, True)
    analyze(project, program)
    return program


def bootstrap():
    start_jvm()
    project = open_project()
    results = []
    try:
        # Small programs first so interrupted initial imports are useful/restartable.
        for path in sorted(ORIGINALS.glob('*.aex'), key=lambda p: p.stat().st_size):
            begun = time.perf_counter()
            print(f'Import/analyze {path.name}', flush=True)
            program = import_program(project, path)
            results.append(dict(program=path.stem, sha256=sha256(path),
                                functions=program.getFunctionManager().getFunctionCount(),
                                seconds=time.perf_counter()-begun, analyzed=True))
            atomic_json(HOME/'reports/bootstrap.json', results)
            print(json.dumps(results[-1]), flush=True)
            project.close(program)
    finally:
        project.close()


if __name__ == '__main__':
    bootstrap()
