"""Discard exact-case pixel artifacts after recording comparison hashes."""
from pathlib import Path

def install(oracle):
    original=oracle.write_json
    def write(path,value):
        original(path,value)
        path=Path(path)
        if path.name=='diff.json' and value.get('status')=='exact':
            purge(path.parent)
    oracle.write_json=write

def purge(directory):
    directory=Path(directory).resolve()
    for file in directory.rglob('*'):
        if file.is_file() and file.suffix in ('.png','.rgba16le','.rgba32f-le','.bin'):
            if not file.resolve().is_relative_to(directory): raise RuntimeError('artifact escaped case directory')
            file.unlink()
